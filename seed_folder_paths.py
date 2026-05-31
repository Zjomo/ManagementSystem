import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from database import get_db_connection, migrate_db

BASE_DIR = r"f:\0_MyNote\0_硕士\4、竞赛\0_2026竞赛辅导【14人】"

# 赛事 → 文件夹映射
COMP_FOLDER_MAP = {
    "中国研究生创芯大赛（华为杯）": os.path.join(BASE_DIR, "1_创芯大赛"),
    "第二十一届中国研究生电子设计竞赛（研电赛）": os.path.join(BASE_DIR, "2_研电赛"),
    "第二届中国研究生智能建造创新大赛": os.path.join(BASE_DIR, "3_智能创建大赛"),
}

print("运行数据库迁移...")
migrate_db()

conn = get_db_connection()
cursor = conn.cursor()

for comp_name, folder_path in COMP_FOLDER_MAP.items():
    if os.path.exists(folder_path):
        official_materials_dir = os.path.join(folder_path, "00_官方材料")
        official_materials_path = official_materials_dir if os.path.exists(official_materials_dir) else ""
        
        cursor.execute(
            "UPDATE competitions SET folder_path = ?, official_materials_path = ? WHERE name = ?",
            (folder_path, official_materials_path, comp_name)
        )
        print(f"  {comp_name}: {folder_path}")
        print(f"    官方材料: {official_materials_path}")
    else:
        print(f"  {comp_name}: 目录不存在 - {folder_path}")

# 填充学生项目文件夹路径
cursor.execute("""
    SELECT sc.id, sc.student_id, sc.competition_id, sc.project_name,
           s.name as student_name, c.name as competition_name, c.folder_path
    FROM student_competitions sc
    LEFT JOIN students s ON sc.student_id = s.id
    LEFT JOIN competitions c ON sc.competition_id = c.id
    WHERE project_name IS NOT NULL AND c.folder_path IS NOT NULL
""")

for row in cursor.fetchall():
    folder = row['folder_path'] or ''
    if not folder:
        continue
    student_dir = os.path.join(folder, "00_参赛学生")
    if not os.path.exists(student_dir):
        continue
    
    for d in os.listdir(student_dir):
        d_path = os.path.join(student_dir, d)
        if os.path.isdir(d_path) and row['student_name'] and row['student_name'] in d:
            cursor.execute(
                "UPDATE student_competitions SET project_folder = ? WHERE id = ?",
                (d_path, row['id'])
            )
            print(f"  {row['competition_name']}/{row['student_name']}: {d_path}")
            break

conn.commit()
conn.close()
print("\n数据库路径填充完成!")