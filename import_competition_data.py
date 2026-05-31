# -*- coding: utf-8 -*-
"""
竞赛数据导入脚本
从Excel表格数据导入竞赛信息、学生-竞赛关联到竞赛管理系统
"""
import requests
import json
import sys

API_BASE = "http://localhost:5000/api"

competitions_data = [
    {
        "name": "中国研究生创芯大赛（华为杯）",
        "official_url": "https://cpipc.acge.org.cn/",
        "category": "集成电路设计",
        "status": "active",
        "end_date": "2026-08-15",
        "description": "中国研究生创芯大赛是面向全国研究生的集成电路设计创新赛事"
    }
]

student_projects = [
    {"name": "陈凯鸿", "grade": "研二", "phone": "13859261531", "project": "高分辨率CMOS图像的异构算法设计"},
    {"name": "刘庆锟", "grade": "研二", "phone": "18607280672", "project": "高精度AWG或DGT的THD校准算法设计"},
    {"name": "刘灿银", "grade": "研二", "phone": "18263869419", "project": "应用于CMOS图像传感器PD sensitivity补偿的插值采样点选取方法优化"},
    {"name": "史明上", "grade": "研二", "phone": "17851258170", "project": "基于大模型推理的 FlashAttention高性能硬件加速器IP设计"},
    {"name": "张曾龙", "grade": "研一", "phone": "15591808928", "project": "基于dinov3语义分割和SLAM全景扫描的脑机接口芯片智能切割系统"},
    {"name": "张宇杰", "grade": "研一", "phone": "13063555536", "project": "基于LCOS-SLM空间光调制器与DDPM扩散模型的光学图像生成系统"},
    {"name": "姚一鸣", "grade": "研一", "phone": "18731136108", "project": "高动态范围、小像素尺寸的图像传感器像素性能优化"},
    {"name": "孔德鹏", "grade": "研一", "phone": "13859261531", "project": "一种稀疏矩阵运算的芯片系统的设计与实现"},
    {"name": "李东旭", "grade": "研二", "phone": "18155463852", "project": "车载毫米波雷达在多径情况下的参数估计问题"},
    {"name": "李天宇", "grade": "研二", "phone": "13230123814", "project": "基于UWB雷达的非接触式生命体征监测"},
    {"name": "杜嘉", "grade": "研二", "phone": "18903489868", "project": "AI超分辨率模型高效硬件加速器设计与实现"},
    {"name": "石佳祥", "grade": "研二", "phone": "13056986175", "project": "智绘毫米波\u2014AI辅助20GHz~40GHz超宽带LNA设计"},
    {"name": "秦博", "grade": "研一", "phone": "13158781223", "project": "半导体激光器应力仿真、表征技术及抗应力激光器设计"},
    {"name": "罗旭东", "grade": "研一", "phone": "15592043362", "project": "金刚石n型掺杂的理论研究"},
]


def import_data():
    print("=" * 70)
    print("竞赛数据导入脚本")
    print("=" * 70)

    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if not response.json().get('success'):
            print("错误: 系统未就绪")
            return False
        print("系统连接成功！\n")
    except Exception as e:
        print(f"错误: 无法连接到系统 - {e}")
        return False

    # Step 1: 创建竞赛
    print("=" * 50)
    print("[步骤1] 导入竞赛信息")
    print("=" * 50)

    competition_id = None
    for comp in competitions_data:
        print(f"\n正在创建竞赛: {comp['name']}")
        response = requests.post(
            f"{API_BASE}/competitions",
            json=comp,
            timeout=10
        )
        result = response.json()
        if result.get('success'):
            competition_id = result.get('id')
            print(f"  ✓ 竞赛创建成功 - ID: {competition_id}")
        else:
            print(f"  ✗ 失败: {result.get('message')}")

    if not competition_id:
        print("\n竞赛创建失败，跳过后续步骤")
        return False

    # Step 2: 导入学生信息
    print("\n" + "=" * 50)
    print("[步骤2] 导入学生信息")
    print("=" * 50)

    # 先获取已有学生列表，避免重复导入
    existing_students = {}
    try:
        response = requests.get(f"{API_BASE}/students", timeout=5)
        if response.json().get('success'):
            for s in response.json().get('data', []):
                existing_students[s['name']] = s
    except:
        pass

    # 创建每个学生
    for student in student_projects:
        if student['name'] in existing_students:
            print(f"  ○ {student['name']} 已存在，跳过")
            continue

        data = {
            'name': student['name'],
            'grade': student['grade'],
            'major': '集成电路工程',
            'phone': student['phone'],
            'email': '',
            'remarks': ''
        }
        response = requests.post(
            f"{API_BASE}/students",
            json=data,
            timeout=10
        )
        result = response.json()
        if result.get('success'):
            existing_students[student['name']] = {'id': result.get('id'), 'name': student['name']}
            print(f"  ✓ {student['name']} 导入成功")
        else:
            print(f"  ✗ {student['name']} 导入失败: {result.get('message')}")

    # Step 3: 创建学生-竞赛关联
    print("\n" + "=" * 50)
    print("[步骤3] 创建学生-竞赛关联")
    print("=" * 50)

    for student in student_projects:
        student_info = existing_students.get(student['name'])
        if not student_info:
            print(f"  ✗ {student['name']} 未找到，跳过关联")
            continue

        data = {
            'student_id': student_info['id'],
            'competition_id': competition_id,
            'project_name': student['project'],
            'role': '队长',
            'registration_status': 'registered',
            'remarks': ''
        }

        response = requests.post(
            f"{API_BASE}/student-competitions",
            json=data,
            timeout=10
        )
        result = response.json()
        if result.get('success'):
            print(f"  ✓ {student['name']} -> 创芯大赛 ({student['project']})")
        else:
            print(f"  ✗ {student['name']} 关联失败: {result.get('message')}")

    print("\n" + "=" * 70)
    print("导入完成!")
    print("=" * 70)
    print(f"竞赛: 创芯大赛 (ID: {competition_id})")
    print(f"参赛学生: {len(student_projects)}人")
    print(f"官网: https://cpipc.acge.org.cn/")
    print("=" * 70)

    return True


if __name__ == '__main__':
    success = import_data()
    sys.exit(0 if success else 1)