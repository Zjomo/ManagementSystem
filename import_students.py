# -*- coding: utf-8 -*-
"""
学生信息导入脚本
从Excel文件读取学生信息并导入到竞赛管理系统
"""
import requests
import json
import sys
import os

# 竞赛管理系统API地址
API_BASE = "http://localhost:5000/api"

# 学生信息列表（从Excel提取）
students = [
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
    {"name": "石佳祥", "grade": "研二", "phone": "13056986175", "project": "智绘毫米波—AI辅助20GHz~40GHz超宽带LNA设计"},
    {"name": "秦博", "grade": "研一", "phone": "13158781223", "project": "半导体激光器应力仿真、表征技术及抗应力激光器设计"},
    {"name": "罗旭东", "grade": "研一", "phone": "15592043362", "project": "金刚石n型掺杂的理论研究"},
]

def import_students():
    """导入学生信息到竞赛管理系统"""
    print("=" * 60)
    print("学生信息导入脚本")
    print("=" * 60)
    
    # 检查系统是否运行
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if not response.json().get('success'):
            print("错误: 系统未就绪，请先启动竞赛管理系统")
            return False
        print("系统连接成功！")
    except Exception as e:
        print(f"错误: 无法连接到系统 - {e}")
        print("请先启动竞赛管理系统: python backend\\app.py")
        return False
    
    # 导入学生信息
    success_count = 0
    fail_count = 0
    
    for i, student in enumerate(students, 1):
        print(f"\n[{i}/{len(students)}] 正在导入: {student['name']} ({student['grade']})")
        
        try:
            # 准备学生数据
            data = {
                'name': student['name'],
                'grade': student['grade'],
                'major': '集成电路工程',  # 默认专业
                'phone': student['phone'],
                'email': '',
                'remarks': f'竞赛项目: {student["project"]}'
            }
            
            # 调用API创建学生
            response = requests.post(
                f"{API_BASE}/students",
                json=data,
                timeout=10
            )
            
            result = response.json()
            
            if result.get('success'):
                print(f"  ✓ 导入成功 - ID: {result.get('id')}")
                success_count += 1
            else:
                print(f"  ✗ 导入失败: {result.get('message')}")
                fail_count += 1
                
        except Exception as e:
            print(f"  ✗ 导入异常: {e}")
            fail_count += 1
    
    # 打印导入总结
    print("\n" + "=" * 60)
    print("导入完成!")
    print("=" * 60)
    print(f"总数: {len(students)}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print("=" * 60)
    
    return fail_count == 0

if __name__ == '__main__':
    success = import_students()
    sys.exit(0 if success else 1)
