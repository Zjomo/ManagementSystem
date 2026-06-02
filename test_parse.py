import sys
sys.path.insert(0, 'backend')
from app import parse_student_folder_name, scan_student_folders, get_db_connection, resolve_competition_folder

# 测试解析函数
test_cases = [
    '金刚石n型掺杂的理论研究-罗旭东-研一',
    '罗旭东-研一',
    '一种稀疏矩阵运算的芯片系统的设计与实现-孔德鹏-研一-陈凯鸿-研二',
    '基于YOLOv8目标检测和RTSP流媒体架构的多场景智能预警系统-孔德鹏-研一',
    '李东旭-研二',
]
print('=== 解析测试 ===')
for tc in test_cases:
    name, grade, project = parse_student_folder_name(tc)
    if project:
        print(f'{tc} -> 学生:{name}, 年级:{grade}, 项目:{project[:20]}...')
    else:
        print(f'{tc} -> 学生:{name}, 年级:{grade}, 项目:无')

# 测试扫描函数 - 查找华为杯竞赛ID
print('\n=== 华为杯扫描结果 ===')
conn = get_db_connection()
comps = conn.execute("SELECT id, name FROM competitions WHERE name LIKE '%华为杯%'").fetchall()
print('Found competitions:', [dict(c) for c in comps])
if comps:
    comp_id = comps[0]['id']
    students = conn.execute('''
        SELECT sc.id as relation_id, sc.project_name, sc.role, sc.registration_status,
               sc.progress, sc.project_url, sc.material_files, sc.remarks, sc.created_at,
               s.id as student_id, s.name as student_name, s.grade, s.major, s.phone, s.email
        FROM student_competitions sc
        LEFT JOIN students s ON sc.student_id = s.id
        WHERE sc.competition_id = ?
        ORDER BY sc.created_at DESC
    ''', (comp_id,)).fetchall()
    students_list = [dict(row) for row in students]
    comp_dict = dict(comps[0])
    base_path = resolve_competition_folder(comp_dict)
    print('Base path:', base_path)
    result = scan_student_folders(base_path, students_list)
    for name, folders in result.items():
        print(f'{name}:')
        for f in folders:
            pname = f['project_name'][:30] if f['project_name'] else '无'
            print(f'  - {f["name"]} (解析: {f["parsed_name"]}, {f["parsed_grade"]}, 项目: {pname}...)')
conn.close()
