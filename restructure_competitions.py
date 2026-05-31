import os
import shutil
import json
import re

BASE_DIR = r"f:\0_MyNote\0_硕士\4、竞赛\0_2026竞赛辅导【14人】"
DRY_RUN = False
LOG_FILE = os.path.join(BASE_DIR, "目录重构日志.txt")

operations = []

def log(op_type, src, dst):
    msg = f"[{'DRY-RUN' if DRY_RUN else 'EXEC'}] {op_type}  {src}  ->  {dst}"
    operations.append(msg)
    print(f"  {op_type}: {os.path.basename(src)} -> {dst}")

def ensure_dir(path):
    if not DRY_RUN:
        os.makedirs(path, exist_ok=True)

def safe_move(src, dst):
    if not os.path.exists(src):
        print(f"    [跳过] 源不存在: {src}")
        return False
    log("MOVE", src, dst)
    if not DRY_RUN:
        ensure_dir(os.path.dirname(dst))
        if os.path.exists(dst):
            print(f"    ⚠ 目标已存在，覆盖: {dst}")
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        shutil.move(src, dst)
    return True

SKIP_PATTERNS = [
    r'^\.git$', r'^\.vscode$', r'^__pycache__$', r'^\.mypy_cache$',
    r'^\.pytest_cache$', r'^\.ruff_cache$', r'^\.venv$', r'^\.env$',
    r'^\.uploads$', r'^logs$', r'^\.cache$', r'^\.idea$',
    r'^node_modules$', r'^dist$', r'^build$', r'^\.egg-info$',
    r'^\.benchmark', r'\.pyc$', r'\.lnk$', r'^package-lock\.json$',
    r'^账号密码\.txt$', r'^account', r'^\.gitignore$',
    r'^\.DS_Store$', r'^Thumbs\.db$', r'^\.pytest_cache',
]

def should_skip(name):
    for pat in SKIP_PATTERNS:
        if re.search(pat, name, re.IGNORECASE):
            return True
    return False

def list_dir(path):
    if not os.path.exists(path):
        return []
    return [f for f in os.listdir(path) if not should_skip(f)]

def classify_file(filename):
    """根据文件名和扩展名分类到目标子目录"""
    name_lower = filename.lower()
    ext = os.path.splitext(filename)[1].lower()

    # 报名材料: 图片、申请表
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']:
        return "报名材料"
    if ext in ['.docx', '.doc'] and any(kw in filename for kw in ['申请', '附件', '合照', '报名']):
        return "报名材料"
    if ext == '.pdf':
        # PDF 可能是文档也可能是官方材料，默认归文档
        return "项目文档"

    # 项目文档: markdown、文档类
    if ext in ['.md']:
        return "项目文档"
    if ext in ['.docx', '.doc', '.ppt', '.pptx', '.xls', '.xlsx', '.pdf']:
        return "项目文档"
    if ext in ['.txt'] and any(kw in name_lower for kw in ['报告', 'report', 'readme']):
        return "项目文档"

    # 源代码: .py, .js, .ts, .cpp, .c, .h, .sv, .v, .sh, .yml, .yaml, .toml, .json, .xml
    if ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.cpp', '.c', '.h', '.hpp',
               '.sv', '.v', '.vhd', '.vhdl', '.sh', '.ps1', '.bat',
               '.yml', '.yaml', '.toml', '.cfg', '.ini', '.json',
               '.css', '.scss', '.less', '.html', '.xml',
               '.sql', '.rs', '.go', '.java', '.rb', '.php',
               '.ipynb', '.r', '.m', '.jl']:
        return "源代码"

    # 默认归项目文档
    return "项目文档"

def classify_dir(dirname, dirname_lower):
    """根据目录名分类到目标子目录"""
    # 源代码类目录
    if any(kw in dirname_lower for kw in ['delivery_app', 'src', 'sr_platform', 'sr',
                                           'scripts', 'script', 'tests', 'test',
                                           'app', 'api', 'web', 'db', 'core',
                                           'hw', 'rtl', 'sim', 'vivado',
                                           'accel', 'compile', 'compiler', 'golden',
                                           'model', 'quant', 'utils']):
        return "源代码"

    # 文档类目录
    if any(kw in dirname_lower for kw in ['doc', 'docs', 'document', 'documentation',
                                           'report', 'reports', '检测', '报告', '分析']):
        return "项目文档"

    # 提交材料类
    if any(kw in dirname_lower for kw in ['artifact', 'artifacts', 'output', 'build',
                                           'dist', 'release', '提交', 'submit']):
        return "提交材料"

    # 报名材料类
    if any(kw in dirname for kw in ['华为杯', '创芯', '合照', '报名', '申请', '电子设计', '研电赛']):
        return "报名材料"

    # 代码相关默认
    if any(kw in dirname_lower for kw in ['code', 'source', 'src', 'lib', 'module', 'package']):
        return "源代码"

    # 其余归文档
    return "项目文档"

def organize_student_folder(old_student_path, new_student_path):
    """将一个学生的旧目录结构重组为标准化结构"""
    ensure_dir(os.path.join(new_student_path, "报名材料"))
    ensure_dir(os.path.join(new_student_path, "项目文档"))
    ensure_dir(os.path.join(new_student_path, "源代码"))
    ensure_dir(os.path.join(new_student_path, "提交材料"))

    if not os.path.exists(old_student_path):
        print(f"    [跳过] 学生目录不存在: {old_student_path}")
        return

    for item in list_dir(old_student_path):
        item_path = os.path.join(old_student_path, item)

        if os.path.isfile(item_path):
            target_sub = classify_file(item)
            safe_move(item_path, os.path.join(new_student_path, target_sub, item))

        elif os.path.isdir(item_path):
            target_sub = classify_dir(item, item.lower())

            # 特殊处理: 如果是报名材料目录，将其内容展开移入
            if target_sub == "报名材料":
                for inner in list_dir(item_path):
                    inner_path = os.path.join(item_path, inner)
                    if os.path.isfile(inner_path):
                        safe_move(inner_path, os.path.join(new_student_path, "报名材料", inner))
                    elif os.path.isdir(inner_path) and not should_skip(inner):
                        safe_move(inner_path, os.path.join(new_student_path, "报名材料", inner))

            elif target_sub == "源代码":
                safe_move(item_path, os.path.join(new_student_path, "源代码", item))

            elif target_sub == "提交材料":
                safe_move(item_path, os.path.join(new_student_path, "提交材料", item))

            else:
                safe_move(item_path, os.path.join(new_student_path, "项目文档", item))


def restructure_chuangxin():
    comp_dir = os.path.join(BASE_DIR, "1_创芯大赛")
    print("\n" + "=" * 60)
    print("📁 重构: 1_创芯大赛")
    print("=" * 60)

    ensure_dir(os.path.join(comp_dir, "00_官方材料"))
    ensure_dir(os.path.join(comp_dir, "00_赛题"))
    ensure_dir(os.path.join(comp_dir, "00_参赛学生"))

    # 顶层 .md 文件 -> 赛题
    for f in list_dir(comp_dir):
        fp = os.path.join(comp_dir, f)
        if os.path.isfile(fp) and f.endswith('.md'):
            safe_move(fp, os.path.join(comp_dir, "00_赛题", f))

    # ToThem -> 赛题目录
    tothem = os.path.join(comp_dir, "ToThem")
    if os.path.exists(tothem):
        safe_move(tothem, os.path.join(comp_dir, "00_赛题", "参赛申请表_汇总"))

    # delivery_template
    dt = os.path.join(comp_dir, "0_竞赛报名表+合照", "delivery_template")
    if os.path.exists(dt):
        safe_move(dt, os.path.join(comp_dir, "00_赛题", "delivery_template"))

    # 学生项目重组
    old_student_dir = os.path.join(comp_dir, "0_竞赛报名表+合照")
    if os.path.exists(old_student_dir):
        for item in list_dir(old_student_dir):
            item_path = os.path.join(old_student_dir, item)
            if os.path.isdir(item_path):
                new_student_dir = os.path.join(comp_dir, "00_参赛学生", item)
                organize_student_folder(item_path, new_student_dir)
                print(f"    ✅ {item}")

        # 如果旧目录只剩缓存/空目录，重命名为备份
        if not DRY_RUN and os.path.exists(old_student_dir):
            remaining = [f for f in os.listdir(old_student_dir) if not should_skip(f)]
            if not remaining:
                bak = old_student_dir + "_原始备份"
                try:
                    os.rename(old_student_dir, bak)
                    print(f"  旧目录已备份: {bak}")
                except Exception as e:
                    print(f"  备份失败: {e}")
            else:
                print(f"  残留 {len(remaining)} 项，保留旧目录")
                for r in remaining[:10]:
                    print(f"    - {r}")


def restructure_yandiansai():
    comp_dir = os.path.join(BASE_DIR, "2_研电赛")
    print("\n" + "=" * 60)
    print("📁 重构: 2_研电赛")
    print("=" * 60)

    ensure_dir(os.path.join(comp_dir, "00_官方材料"))
    ensure_dir(os.path.join(comp_dir, "00_赛题"))
    ensure_dir(os.path.join(comp_dir, "00_参赛学生"))

    for item in list_dir(comp_dir):
        item_path = os.path.join(comp_dir, item)
        if any(s in item for s in ['00_']):
            continue

        if os.path.isfile(item_path):
            ext = os.path.splitext(item)[1].lower()
            if ext in ['.pdf', '.docx', '.doc']:
                safe_move(item_path, os.path.join(comp_dir, "00_官方材料", item))
            elif ext in ['.md']:
                safe_move(item_path, os.path.join(comp_dir, "00_赛题", item))

        elif os.path.isdir(item_path):
            new_student_dir = os.path.join(comp_dir, "00_参赛学生", item)
            organize_student_folder(item_path, new_student_dir)
            print(f"    ✅ {item}")


def restructure_zhinengjianzao():
    comp_dir = os.path.join(BASE_DIR, "3_智能创建大赛")
    print("\n" + "=" * 60)
    print("📁 重构: 3_智能创建大赛")
    print("=" * 60)

    ensure_dir(os.path.join(comp_dir, "00_官方材料"))
    ensure_dir(os.path.join(comp_dir, "00_赛题"))
    ensure_dir(os.path.join(comp_dir, "00_参赛学生"))

    for item in list_dir(comp_dir):
        item_path = os.path.join(comp_dir, item)
        if any(s in item for s in ['00_']):
            continue

        if os.path.isfile(item_path):
            ext = os.path.splitext(item)[1].lower()
            if ext == '.pdf':
                safe_move(item_path, os.path.join(comp_dir, "00_官方材料", item))
            elif ext == '.md':
                safe_move(item_path, os.path.join(comp_dir, "00_赛题", item))
            else:
                safe_move(item_path, os.path.join(comp_dir, "00_官方材料", item))

        elif os.path.isdir(item_path):
            new_student_dir = os.path.join(comp_dir, "00_参赛学生", item)
            organize_student_folder(item_path, new_student_dir)
            print(f"    ✅ {item}")


def generate_structure_doc(comp_dir, comp_name):
    """生成目录结构说明"""
    students = []
    student_dir = os.path.join(comp_dir, "00_参赛学生")
    if not DRY_RUN and os.path.exists(student_dir):
        for item in sorted(list_dir(student_dir)):
            sp = os.path.join(student_dir, item)
            if os.path.isdir(sp):
                sub_info = []
                for sub in ['报名材料', '项目文档', '源代码', '提交材料']:
                    sub_path = os.path.join(sp, sub)
                    if os.path.exists(sub_path):
                        count = len(list_dir(sub_path))
                        if count > 0:
                            sub_info.append(f"{sub}({count})")
                students.append(f"- `{item}`: {', '.join(sub_info) if sub_info else '（空）'}")

    official = []
    off_dir = os.path.join(comp_dir, "00_官方材料")
    if not DRY_RUN and os.path.exists(off_dir):
        official = [f for f in list_dir(off_dir) if os.path.isfile(os.path.join(off_dir, f))]

    topics = []
    topic_dir = os.path.join(comp_dir, "00_赛题")
    if not DRY_RUN and os.path.exists(topic_dir):
        topics = [f for f in list_dir(topic_dir) if os.path.isfile(os.path.join(topic_dir, f))]

    name_clean = comp_name.replace("_", "")
    readme = f"""# {name_clean}

> 标准化竞赛管理目录 — 系统可自动扫描读取

## 📁 目录结构

```
{comp_name}/
├── 00_官方材料/        ← 参赛指南、邀请函等官方PDF/DOCX
├── 00_赛题/             ← 赛题说明、参赛申请表汇总
├── 00_参赛学生/         ← 按学生+项目组织的全部材料
│   └── {{项目}}_{{姓名}}_{{年级}}/
│       ├── 报名材料/   ← 参赛申请表、团队合照
│       ├── 项目文档/   ← 需求说明、设计文档、检测报告
│       ├── 源代码/     ← delivery_app, RTL, scripts 等
│       └── 提交材料/   ← artifacts, 最终提交包
└── 00_目录说明.md      ← 本文件
```

## 📋 官方材料
{chr(10).join(f"- {f}" for f in official) if official else "（暂无）"}

## 📝 赛题
{chr(10).join(f"- {f}" for f in topics) if topics else "（暂无）"}

## 👥 参赛学生 ({len(students)}人)
{chr(10).join(students) if students else "（暂无）"}

---
*本文件由目录规范化脚本自动生成*
"""
    path = os.path.join(comp_dir, "00_目录说明.md")
    if not DRY_RUN:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(readme)
        print(f"  📄 已生成: {path}")
    else:
        log("CREATE", "-", path)


def main():
    global DRY_RUN
    print("=" * 60)
    print("竞赛目录标准化重构")
    print(f"基础目录: {BASE_DIR}")
    print(f"模式: {'🔍 DRY-RUN（预览）' if DRY_RUN else '⚡ 执行模式'}")
    print("=" * 60)

    if DRY_RUN:
        print("\n⚠ 预览模式：仅显示将要执行的操作，不会实际移动文件")
        print("  确认无误后，将脚本开头 DRY_RUN = False 再运行\n")

    restructure_chuangxin()
    restructure_yandiansai()
    restructure_zhinengjianzao()

    # 生成目录说明
    if not DRY_RUN:
        generate_structure_doc(os.path.join(BASE_DIR, "1_创芯大赛"), "1_创芯大赛")
        generate_structure_doc(os.path.join(BASE_DIR, "2_研电赛"), "2_研电赛")
        generate_structure_doc(os.path.join(BASE_DIR, "3_智能创建大赛"), "3_智能创建大赛")

    print("\n" + "=" * 60)
    print(f"操作汇总: {len(operations)} 项")
    print("=" * 60)

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"操作总数: {len(operations)}\n\n")
        f.write("\n".join(operations))

    print(f"📄 日志: {LOG_FILE}")

    move_count = sum(1 for op in operations if 'MOVE' in op)
    create_count = sum(1 for op in operations if 'CREATE' in op)
    print(f"  MOVE: {move_count} | CREATE: {create_count}")

    if DRY_RUN:
        print("\n✅ 预览完成！确认后设置 DRY_RUN = False 并重新运行以执行。")
    else:
        print("\n✅ 重构完成！")


if __name__ == "__main__":
    main()