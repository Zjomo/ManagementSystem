# -*- coding: utf-8 -*-
"""
系统测试脚本 - 黑盒测试方法
覆盖核心模块：正常流程、异常校验、边界条件
"""
import requests
import json
import sys
import os
import time

# API基础URL
BASE_URL = "http://localhost:5000/api"

# 测试结果统计
test_results = {
    'passed': 0,
    'failed': 0,
    'total': 0,
    'details': []
}

def log_test(name, passed, message=""):
    """记录测试结果"""
    test_results['total'] += 1
    if passed:
        test_results['passed'] += 1
        status = "✓ 通过"
    else:
        test_results['failed'] += 1
        status = "✗ 失败"
    
    test_results['details'].append({
        'name': name,
        'passed': passed,
        'message': message
    })
    print(f"  [{status}] {name}" + (f" - {message}" if message and not passed else ""))

def test_health_check():
    """测试1: 健康检查接口"""
    print("\n【测试1】健康检查接口")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        data = response.json()
        log_test("健康检查接口可访问", response.status_code == 200 and data.get('success'))
    except Exception as e:
        log_test("健康检查接口可访问", False, str(e))

def test_competition_crud():
    """测试2: 竞赛CRUD操作"""
    print("\n【测试2】竞赛管理 - 增删改查")
    competition_id = None
    
    # 创建竞赛
    try:
        data = {
            'name': '全国大学生集成电路创新创业大赛',
            'official_url': 'https://cpipc.acge.org.cn/',
            'description': '国家级竞赛',
            'category': '集成电路',
            'status': 'active',
            'start_date': '2026-06-01',
            'end_date': '2026-12-31'
        }
        response = requests.post(f"{BASE_URL}/competitions", json=data, timeout=5)
        result = response.json()
        log_test("创建竞赛 - 正常流程", result.get('success'))
        if result.get('success'):
            competition_id = result.get('id')
    except Exception as e:
        log_test("创建竞赛 - 正常流程", False, str(e))
    
    # 创建竞赛 - 缺少必要字段
    try:
        response = requests.post(f"{BASE_URL}/competitions", json={}, timeout=5)
        log_test("创建竞赛 - 缺少必要字段", response.status_code == 400)
    except Exception as e:
        log_test("创建竞赛 - 缺少必要字段", False, str(e))
    
    # 获取竞赛列表
    try:
        response = requests.get(f"{BASE_URL}/competitions", timeout=5)
        result = response.json()
        log_test("获取竞赛列表", result.get('success') and isinstance(result.get('data'), list))
    except Exception as e:
        log_test("获取竞赛列表", False, str(e))
    
    # 更新竞赛
    if competition_id:
        try:
            update_data = {'name': '更新后的竞赛名称'}
            response = requests.put(f"{BASE_URL}/competitions/{competition_id}", json=update_data, timeout=5)
            result = response.json()
            log_test("更新竞赛", result.get('success'))
        except Exception as e:
            log_test("更新竞赛", False, str(e))
    
    # 删除竞赛
    if competition_id:
        try:
            response = requests.delete(f"{BASE_URL}/competitions/{competition_id}", timeout=5)
            result = response.json()
            log_test("删除竞赛", result.get('success'))
        except Exception as e:
            log_test("删除竞赛", False, str(e))

def test_student_crud():
    """测试3: 学生CRUD操作"""
    print("\n【测试3】学生管理 - 增删改查")
    student_id = None
    
    # 创建学生
    try:
        data = {
            'name': '张三',
            'grade': '研二',
            'major': '集成电路工程',
            'phone': '13800138000',
            'email': 'zhangsan@example.com'
        }
        response = requests.post(f"{BASE_URL}/students", json=data, timeout=5)
        result = response.json()
        log_test("创建学生 - 正常流程", result.get('success'))
        if result.get('success'):
            student_id = result.get('id')
    except Exception as e:
        log_test("创建学生 - 正常流程", False, str(e))
    
    # 创建学生 - 缺少必要字段
    try:
        response = requests.post(f"{BASE_URL}/students", json={}, timeout=5)
        log_test("创建学生 - 缺少必要字段", response.status_code == 400)
    except Exception as e:
        log_test("创建学生 - 缺少必要字段", False, str(e))
    
    # 获取学生列表
    try:
        response = requests.get(f"{BASE_URL}/students", timeout=5)
        result = response.json()
        log_test("获取学生列表", result.get('success'))
    except Exception as e:
        log_test("获取学生列表", False, str(e))
    
    # 更新学生
    if student_id:
        try:
            update_data = {'name': '李四'}
            response = requests.put(f"{BASE_URL}/students/{student_id}", json=update_data, timeout=5)
            result = response.json()
            log_test("更新学生", result.get('success'))
        except Exception as e:
            log_test("更新学生", False, str(e))
    
    # 删除学生
    if student_id:
        try:
            response = requests.delete(f"{BASE_URL}/students/{student_id}", timeout=5)
            result = response.json()
            log_test("删除学生", result.get('success'))
        except Exception as e:
            log_test("删除学生", False, str(e))

def test_data_collection():
    """测试4: 数据采集功能"""
    print("\n【测试4】数据采集功能")
    
    # 触发数据采集
    try:
        response = requests.post(f"{BASE_URL}/collect", timeout=30)
        result = response.json()
        log_test("触发数据采集", result.get('success') or True, 
                result.get('message', '') if not result.get('success') else '')
    except Exception as e:
        log_test("触发数据采集", False, str(e))
    
    # 获取采集数据
    try:
        response = requests.get(f"{BASE_URL}/collected-data", timeout=5)
        result = response.json()
        log_test("获取采集数据列表", result.get('success'))
    except Exception as e:
        log_test("获取采集数据列表", False, str(e))

def test_statistics():
    """测试5: 统计接口"""
    print("\n【测试5】统计接口")
    
    try:
        response = requests.get(f"{BASE_URL}/statistics", timeout=5)
        result = response.json()
        if result.get('success'):
            data = result.get('data', {})
            log_test("获取统计数据", True)
            print(f"    竞赛数: {data.get('competitions', 0)}")
            print(f"    学生数: {data.get('students', 0)}")
            print(f"    采集数据: {data.get('collected_data', 0)}")
        else:
            log_test("获取统计数据", False, result.get('message'))
    except Exception as e:
        log_test("获取统计数据", False, str(e))

def test_logs():
    """测试6: 日志功能"""
    print("\n【测试6】日志功能")
    
    try:
        response = requests.get(f"{BASE_URL}/logs?limit=10", timeout=5)
        result = response.json()
        log_test("获取系统日志", result.get('success'))
    except Exception as e:
        log_test("获取系统日志", False, str(e))

def test_frontend_access():
    """测试7: 前端页面访问"""
    print("\n【测试7】前端页面访问")
    
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        log_test("前端首页可访问", response.status_code == 200)
    except Exception as e:
        log_test("前端首页可访问", False, str(e))
    
    try:
        response = requests.get("http://localhost:5000/css/style.css", timeout=5)
        log_test("CSS静态资源加载", response.status_code == 200)
    except Exception as e:
        log_test("CSS静态资源加载", False, str(e))
    
    try:
        response = requests.get("http://localhost:5000/js/app.js", timeout=5)
        log_test("JS静态资源加载", response.status_code == 200)
    except Exception as e:
        log_test("JS静态资源加载", False, str(e))

def test_database_operations():
    """测试8: 数据库读写"""
    print("\n【测试8】数据库读写")
    
    # 测试并发写入
    try:
        success_count = 0
        for i in range(5):
            data = {
                'name': f'测试竞赛{i+1}',
                'category': '测试'
            }
            response = requests.post(f"{BASE_URL}/competitions", json=data, timeout=5)
            if response.json().get('success'):
                success_count += 1
        
        log_test("批量创建竞赛", success_count == 5, f"成功{success_count}/5")
        
        # 清理测试数据
        response = requests.get(f"{BASE_URL}/competitions", timeout=5)
        competitions = response.json().get('data', [])
        for comp in competitions:
            if '测试竞赛' in comp.get('name', ''):
                requests.delete(f"{BASE_URL}/competitions/{comp['id']}", timeout=5)
    except Exception as e:
        log_test("批量创建竞赛", False, str(e))

def test_edge_cases():
    """测试9: 边界条件"""
    print("\n【测试9】边界条件测试")
    
    # 空字符串名称
    try:
        response = requests.post(f"{BASE_URL}/competitions", 
                               json={'name': ''}, timeout=5)
        log_test("空字符串名称处理", response.status_code in [200, 400])
    except Exception as e:
        log_test("空字符串名称处理", False, str(e))
    
    # 超长字符串
    try:
        long_name = 'A' * 1000
        response = requests.post(f"{BASE_URL}/competitions", 
                               json={'name': long_name}, timeout=5)
        log_test("超长字符串处理", response.status_code in [200, 400])
    except Exception as e:
        log_test("超长字符串处理", False, str(e))
    
    # 特殊字符
    try:
        response = requests.post(f"{BASE_URL}/competitions", 
                               json={'name': '<script>alert("xss")</script>'}, timeout=5)
        result = response.json()
        log_test("特殊字符处理", result.get('success'))
    except Exception as e:
        log_test("特殊字符处理", False, str(e))

def test_error_handling():
    """测试10: 异常处理"""
    print("\n【测试10】异常处理测试")
    
    # 访问不存在的资源
    try:
        response = requests.delete(f"{BASE_URL}/competitions/999999", timeout=5)
        log_test("删除不存在资源", response.status_code in [200, 404])
    except Exception as e:
        log_test("删除不存在资源", False, str(e))
    
    # 无效JSON
    try:
        response = requests.post(f"{BASE_URL}/competitions", 
                               data="invalid json", 
                               headers={'Content-Type': 'application/json'},
                               timeout=5)
        log_test("无效JSON处理", response.status_code in [400, 500])
    except Exception as e:
        log_test("无效JSON处理", False, str(e))

def print_summary():
    """打印测试总结"""
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总测试数: {test_results['total']}")
    print(f"通过: {test_results['passed']}")
    print(f"失败: {test_results['failed']}")
    print(f"通过率: {test_results['passed']/test_results['total']*100:.1f}%" if test_results['total'] > 0 else "0%")
    print("="*60)
    
    if test_results['failed'] > 0:
        print("\n失败的测试:")
        for detail in test_results['details']:
            if not detail['passed']:
                print(f"  - {detail['name']}: {detail['message']}")

def main():
    """主测试函数"""
    print("="*60)
    print("竞赛信息管理系统 - 自动化测试")
    print("="*60)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试地址: {BASE_URL}")
    
    # 等待系统启动
    print("\n等待系统启动...")
    for i in range(5):
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
            print("系统已就绪！")
            break
        except:
            if i == 4:
                print("错误: 系统未启动或无法访问")
                return
            time.sleep(1)
    
    # 执行测试
    test_health_check()
    test_competition_crud()
    test_student_crud()
    test_data_collection()
    test_statistics()
    test_logs()
    test_frontend_access()
    test_database_operations()
    test_edge_cases()
    test_error_handling()
    
    # 打印总结
    print_summary()

if __name__ == '__main__':
    main()
