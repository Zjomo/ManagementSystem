# -*- coding: utf-8 -*-
"""
竞赛信息管理系统 - 配置文件
"""
import os

# 项目根目录（自动定位）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================
# 竞赛材料源路径
# ============================================
# 所有竞赛的材料文件在此目录下按"竞赛名称"子目录存放。
# 当某个竞赛在数据库中没有单独设置 folder_path 时，
# 系统会自动使用此路径 + 竞赛名称 来寻找材料。
#
# 你可以修改为任意绝对路径或相对路径（相对于项目根目录）。
# 例如:
#   MATERIALS_BASE_DIR = r"D:\我的竞赛文件"
#   MATERIALS_BASE_DIR = r"E:\Backup\CompetitionMaterials"
# ============================================
MATERIALS_BASE_DIR = os.path.join(BASE_DIR, 'competition_materials')

# 确保目录存在
os.makedirs(MATERIALS_BASE_DIR, exist_ok=True)