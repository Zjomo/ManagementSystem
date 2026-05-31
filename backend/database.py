# -*- coding: utf-8 -*-
"""
数据库模块 - 管理SQLite数据库连接和操作
"""
import sqlite3
import os
from datetime import datetime

# 数据库文件路径（放在data目录下）
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'competition.db')

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def migrate_db():
    """数据库迁移 - 添加新字段"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE student_competitions ADD COLUMN project_name TEXT")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE student_competitions ADD COLUMN registration_status TEXT DEFAULT 'pending'")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE student_competitions ADD COLUMN material_files TEXT")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE competitions ADD COLUMN official_materials TEXT")
    except:
        pass
    
    # 新增: 文件夹路径映射（支持结构化读取）
    try:
        cursor.execute("ALTER TABLE competitions ADD COLUMN folder_path TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE competitions ADD COLUMN official_materials_path TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE student_competitions ADD COLUMN project_folder TEXT")
    except:
        pass
    
    # 新增: collected_data 表关联 competition_id
    try:
        cursor.execute("ALTER TABLE collected_data ADD COLUMN competition_id INTEGER")
    except:
        pass
    
    # 新增: time_plan remarks字段
    try:
        cursor.execute("ALTER TABLE time_plan ADD COLUMN remarks TEXT DEFAULT '{}'")
    except:
        pass
    
    conn.commit()
    conn.close()
    print("数据库迁移完成")

def init_db():
    """初始化数据库，创建所有必要的表"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建竞赛信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            official_url TEXT,
            description TEXT,
            category TEXT,
            official_materials TEXT,
            official_materials_path TEXT,
            folder_path TEXT,
            status TEXT DEFAULT 'active',
            start_date TEXT,
            end_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建学生信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade TEXT,
            major TEXT,
            phone TEXT,
            email TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建学生竞赛关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            competition_id INTEGER NOT NULL,
            project_name TEXT,
            project_folder TEXT,
            role TEXT,
            registration_status TEXT DEFAULT 'pending',
            progress TEXT DEFAULT 'not_started',
            project_url TEXT,
            material_files TEXT,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (competition_id) REFERENCES competitions(id)
        )
    ''')
    
    # 创建采集数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collected_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            summary TEXT,
            source_url TEXT,
            publish_date TEXT,
            collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            category TEXT,
            tags TEXT
        )
    ''')
    
    # 创建系统日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            module TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建赛程规划表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_data TEXT NOT NULL,
            source_url TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            remarks TEXT DEFAULT '{}'
        )
    ''')
    
    conn.commit()
    conn.close()
    print("数据库初始化成功")

def log_message(level, message, module=None):
    """记录系统日志到数据库"""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO system_logs (level, message, module) VALUES (?, ?, ?)",
        (level, message, module)
    )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
