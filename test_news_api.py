import urllib.request
import json

r = urllib.request.urlopen('http://localhost:5000/api/collected-data')
d = json.loads(r.read())
print('Groups:', len(d['data']))
for g in d['data']:
    print(f"  [{g['competition_name']}] {len(g['news'])} items")
if d['data']:
    first_title = d['data'][0]['news'][0]['title'] if d['data'][0]['news'] else 'no news'
    print('First title:', first_title[:80])