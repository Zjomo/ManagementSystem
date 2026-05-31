import requests
import json

API = "http://localhost:5000/api"

yandiansai_students = [
    {"name": "孔德鹏", "project": "基于YOLOv8目标检测和RTSP流媒体架构的多场景智能预警系统"},
    {"name": "张曾龙", "project": "基于dinov3语义分割和SLAM全景扫描的脑机接口芯片智能切割系统"},
    {"name": "姚一鸣", "project": "基于语义分割和四轴电机的主动激光束稳定系统"},
    {"name": "李东旭", "project": ""},
    {"name": "杜嘉", "project": ""},
    {"name": "秦博", "project": ""},
    {"name": "罗旭东", "project": ""},
]

zhinengjianzao_students = [
    {"name": "姚一鸣", "project": "融合LLM与知识图谱的施工现场安全风险隐患智能研判方法（赛题4）"},
]

zhinengjianzao_materials = json.dumps([
    {"name": "第二届智能建造大赛参赛指南", "url": "materials/第二届中国研究生智能建造创新大赛参赛指南.pdf"},
    {"name": "第二届智能建造大赛邀请函", "url": "materials/第二届中国研究生智能建造创新大赛邀请函.pdf"},
], ensure_ascii=False)

print("=" * 60)
print("导入研电赛 + 智能建造大赛")
print("=" * 60)

r = requests.get(f"{API}/health")
print(f"API状态: {r.json().get('status', 'unknown')}")

print("\n[1/4] 创建 研电赛...")
resp = requests.post(f"{API}/competitions", json={
    "name": "第二十一届中国研究生电子设计竞赛（研电赛）",
    "official_url": "https://cpipc.acge.org.cn/",
    "category": "电子设计",
    "status": "active",
    "end_date": "2026-07-15",
    "description": "中国研究生电子设计竞赛是面向全国研究生的电子设计创新赛事",
}).json()
print(f"  -> {resp}")
yandiansai_id = resp.get("id")

print("\n[2/4] 创建 智能建造大赛...")
resp = requests.post(f"{API}/competitions", json={
    "name": "第二届中国研究生智能建造创新大赛",
    "official_url": "https://cpipc.acge.org.cn/",
    "category": "智能建造",
    "status": "active",
    "end_date": "2026-07-31",
    "description": "中国研究生智能建造创新大赛旨在推动智能建造领域的技术创新与应用",
    "official_materials": zhinengjianzao_materials,
}).json()
print(f"  -> {resp}")
zhinengjianzao_id = resp.get("id")

print("\n[3/4] 创建 研电赛 学生关联...")
for s in yandiansai_students:
    r = requests.get(f"{API}/students", params={"search": s["name"]})
    students = r.json().get("data", [])
    if students:
        sid = students[0]["id"]
        resp = requests.post(f"{API}/student-competitions", json={
            "student_id": sid,
            "competition_id": yandiansai_id,
            "project_name": s["project"] or "",
            "registration_status": "registered",
        }).json()
        status = "OK" if resp.get("success") else "FAIL"
        print(f"  {status}: {s['name']} -> 研电赛 ({s['project'] or '待定'})")
    else:
        print(f"  NOTFOUND: {s['name']}")

print("\n[4/4] 创建 智能建造大赛 学生关联...")
for s in zhinengjianzao_students:
    r = requests.get(f"{API}/students", params={"search": s["name"]})
    students = r.json().get("data", [])
    if students:
        sid = students[0]["id"]
        resp = requests.post(f"{API}/student-competitions", json={
            "student_id": sid,
            "competition_id": zhinengjianzao_id,
            "project_name": s["project"],
            "registration_status": "registered",
        }).json()
        status = "OK" if resp.get("success") else "FAIL"
        print(f"  {status}: {s['name']} -> 智能建造大赛 ({s['project']})")
    else:
        print(f"  NOTFOUND: {s['name']}")

print("\n" + "=" * 60)
print("导入完成!")
print(f"研电赛 ID: {yandiansai_id}, 学生: {len(yandiansai_students)}人")
print(f"智能建造大赛 ID: {zhinengjianzao_id}, 学生: {len(zhinengjianzao_students)}人")
print("=" * 60)