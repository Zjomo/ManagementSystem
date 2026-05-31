# -*- coding: utf-8 -*-
"""
数据采集模块 - 按赛事官网分别采集最新资讯信息
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import os
import re
import json
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from database import get_db_connection, log_message

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

NEWS_KEYWORDS = ['通知', '公告', '新闻', '动态', '信息', '发布', '报名', '大赛', '竞赛',
                 '日程', '安排', '结果', '公示', '获奖', '通知公告', '赛事动态',
                 'notice', 'news', 'announcement']

def fetch_page(url, timeout=15):
    """获取网页内容"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.text
        else:
            log_message("警告", f"访问 {url} 返回状态码 {response.status_code}", "数据采集")
            return None
    except requests.exceptions.Timeout:
        log_message("警告", f"访问 {url} 超时", "数据采集")
        return None
    except requests.exceptions.RequestException as e:
        log_message("警告", f"访问 {url} 失败: {str(e)}", "数据采集")
        return None

def try_subpages(base_url):
    """尝试常见子页面路径"""
    subpages = ['', '/news', '/notice', '/announcement', '/index/news', '/资讯中心']
    results = []
    seen_urls = set()

    for sub in subpages:
        url = base_url.rstrip('/') + sub
        if url in seen_urls:
            continue
        seen_urls.add(url)
        html = fetch_page(url)
        if html:
            items = parse_news_items(html, url)
            if items:
                results.extend(items)

    return results

def parse_news_items(html, source_url):
    """从 HTML 中解析新闻资讯条目"""
    if not html:
        return []

    soup = BeautifulSoup(html, 'lxml')
    items = []
    seen_titles = set()

    candidates = soup.find_all(['a', 'li', 'div', 'tr'], class_=re.compile(
        r'news|list|item|title|notice|article|post|entry', re.I
    ))

    if not candidates:
        candidates = soup.find_all(['a', 'li', 'div'])

    for elem in candidates:
        title = elem.get_text(strip=True)
        if not title or len(title) < 6:
            continue

        link = elem
        if elem.name == 'a':
            link = elem
        else:
            a_tag = elem.find('a')
            if a_tag:
                link = a_tag

        href = link.get('href', '') if hasattr(link, 'get') else ''
        title_text = link.get_text(strip=True) if hasattr(link, 'get_text') else title

        if not title_text or len(title_text) < 6 or title_text in seen_titles:
            continue

        is_newsworthy = any(kw in title_text for kw in NEWS_KEYWORDS)
        if not is_newsworthy:
            continue

        seen_titles.add(title_text)

        full_url = href
        if href and not href.startswith('http'):
            if href.startswith('/'):
                parsed = urllib.parse.urlparse(source_url)
                full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
            else:
                full_url = source_url.rstrip('/') + '/' + href.lstrip('/')

        items.append({
            'title': title_text[:300],
            'url': full_url,
            'publish_date': datetime.now().strftime('%Y-%m-%d'),
            'content': title_text[:1000]
        })

        if len(items) >= 15:
            break

    return items

def parse_detail_content(html):
    """尝试获取详情页的正文内容"""
    if not html:
        return ''
    soup = BeautifulSoup(html, 'lxml')
    for tag in ['article', 'main', '.content', '.article', '.detail', '.text']:
        if tag.startswith('.'):
            el = soup.select_one(tag)
        else:
            el = soup.find(tag)
        if el:
            return el.get_text(strip=True)[:2000]
    return ''

def match_competition(title, comp_name):
    """判断标题是否与赛事相关"""
    keywords = comp_name.replace('（', ' ').replace('）', ' ').replace('(', ' ').replace(')', ' ')
    keywords = re.sub(r'第[一二三四五六七八九十\d]+届', '', keywords).strip()
    parts = [p.strip() for p in keywords.split() if len(p.strip()) > 1]
    return any(p in title for p in parts) if parts else True

def collect_for_competition(comp):
    """为单个赛事采集资讯"""
    comp_id = comp['id']
    comp_name = comp['name']
    official_url = comp.get('official_url', '')

    if not official_url:
        log_message("信息", f"赛事 [{comp_name}] 未配置官网链接，跳过", "数据采集")
        return []

    log_message("信息", f"开始为 [{comp_name}] 采集资讯: {official_url}", "数据采集")

    all_items = try_subpages(official_url)

    filtered = [item for item in all_items if match_competition(item['title'], comp_name)]
    if not filtered and all_items:
        filtered = all_items[:5]

    for item in filtered:
        item['competition_id'] = comp_id
        item['competition_name'] = comp_name

        detail_html = fetch_page(item['url'], timeout=8)
        if detail_html:
            detail = parse_detail_content(detail_html)
            if detail:
                item['content'] = detail

    log_message("信息", f"[{comp_name}] 采集到 {len(filtered)} 条相关资讯", "数据采集")
    return filtered

def save_news_batch(news_list):
    """批量保存资讯到数据库"""
    if not news_list:
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()
    saved = 0

    for news in news_list:
        try:
            cursor.execute(
                "SELECT id FROM collected_data WHERE title = ? AND competition_id = ?",
                (news['title'], news.get('competition_id'))
            )
            if cursor.fetchone():
                continue

            summary = news.get('content', news['title'])[:150]
            if len(summary) > 147:
                summary += '...'

            cursor.execute(
                """INSERT INTO collected_data
                   (title, content, summary, source_url, publish_date, category, competition_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    news['title'],
                    news.get('content', ''),
                    summary,
                    news.get('url', ''),
                    news.get('publish_date', datetime.now().strftime('%Y-%m-%d')),
                    '竞赛资讯',
                    news.get('competition_id')
                )
            )
            saved += 1
        except Exception as e:
            log_message("错误", f"保存资讯失败: {str(e)}", "数据采集")
            continue

    conn.commit()
    conn.close()
    return saved

def collect_daily_data():
    """执行数据采集 - 遍历所有赛事"""
    log_message("信息", "开始执行资讯采集任务", "数据采集")

    conn = get_db_connection()
    competitions = conn.execute(
        "SELECT id, name, official_url FROM competitions WHERE official_url IS NOT NULL AND official_url != ''"
    ).fetchall()
    conn.close()

    if not competitions:
        log_message("警告", "数据库中没有配置官网链接的赛事", "数据采集")
        return {'success': False, 'message': '没有可采集的赛事（请先配置赛事官网链接）'}

    all_news = []
    total_competitions = len(competitions)

    for i, comp in enumerate(competitions):
        log_message("信息", f"[{i+1}/{total_competitions}] 采集: {comp['name']}", "数据采集")
        try:
            news = collect_for_competition({'id': comp['id'], 'name': comp['name'], 'official_url': comp['official_url']})
            all_news.extend(news)
        except Exception as e:
            log_message("错误", f"[{comp['name']}] 采集异常: {str(e)}", "数据采集")

    saved = save_news_batch(all_news)

    result = {
        'success': True,
        'message': f'采集完成: 共扫描 {total_competitions} 个赛事，获取 {len(all_news)} 条资讯，新增 {saved} 条',
        'total_competitions': total_competitions,
        'total_news': len(all_news),
        'saved': saved
    }

    log_message("信息", result['message'], "数据采集")
    return result

if __name__ == '__main__':
    result = collect_daily_data()
    print(f"\n采集结果: {json.dumps(result, ensure_ascii=False, indent=2)}")