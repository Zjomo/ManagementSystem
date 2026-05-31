import urllib.request
import urllib.parse
import json


def api(path, params=None):
    url = f"http://localhost:5000{path}"
    if params:
        qs = urllib.parse.urlencode(params)
        url = f"{url}?{qs}"
    try:
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


# 1. 查看所有竞赛
print("=== 所有竞赛 ===")
result = api("/api/competitions")
for c in result["data"]:
    fp = c.get('folder_path') or '(None)'
    print(f"  ID={c['id']} name={c['name']} folder_path={fp[:80]}")

# 2. 测试浏览根目录 (创芯大赛 ID=10)
print("\n=== 测试文件浏览 (ID=10, 根目录) ===")
result = api("/api/files/browse", {"competition_id": 10})
if result["success"]:
    print(f"  current_path: {result['data']['current_path']}")
    for item in result["data"]["items"]:
        print(f"  {item['type']:6s} {item['name']}")
else:
    print(f"  FAILED: {result['message']}")

# 3. 测试浏览子目录
print("\n=== 测试子目录浏览 (00_参赛学生) ===")
result2 = api("/api/files/browse", {"competition_id": 10, "subdir": "00_参赛学生"})
if result2["success"]:
    for item in result2["data"]["items"]:
        print(f"  {item['type']:6s} {item['name']}")
else:
    print(f"  FAILED: {result2['message']}")

# 4. 测试浏览官方材料
print("\n=== 测试官方材料 (ID=12) ===")
result3 = api("/api/files/browse", {"competition_id": 12, "subdir": "00_官方材料"})
if result3["success"]:
    for item in result3["data"]["items"]:
        kb = (item.get('size') or 0) / 1024
        print(f"  {item['type']:6s} {item['name']:40s} {kb:.0f}KB")
else:
    print(f"  FAILED: {result3['message']}")

# 5. 测试深层嵌套: 某个学生的项目目录
print("\n=== 测试嵌套 (创芯大赛/杜嘉) ===")
result4 = api("/api/files/browse", {
    "competition_id": 10,
    "subdir": "00_参赛学生/AI超分辨率模型高效硬件加速器设计与实现-杜嘉-研二"
})
if result4["success"]:
    for item in result4["data"]["items"]:
        print(f"  {item['type']:6s} {item['name']}")
else:
    print(f"  FAILED: {result4['message']}")