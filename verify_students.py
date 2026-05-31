import requests
r = requests.get('http://localhost:5000/api/students')
data = r.json()
print(f'学生总数: {len(data["data"])}')
for s in data['data']:
    print(f'  - {s["name"]} ({s["grade"]}) - {s["phone"]}')
