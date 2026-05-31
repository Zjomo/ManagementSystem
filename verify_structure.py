import os
base = r"f:\0_MyNote\0_硕士\4、竞赛\0_2026竞赛辅导【14人】"
for d in sorted(os.listdir(base)):
    dp = os.path.join(base, d)
    if os.path.isdir(dp) and d[0].isdigit():
        items = [x for x in os.listdir(dp) if not x.startswith('.')]
        print(f"\n{d}: {len(items)} top-level items")
        for item in sorted(items):
            ip = os.path.join(dp, item)
            if os.path.isdir(ip):
                sub_count = len(os.listdir(ip))
                print(f"  {item}/ ({sub_count} children)")
                if '学生' in item:
                    for s in sorted(os.listdir(ip))[:5]:
                        print(f"    - {s}")
                    if len(os.listdir(ip)) > 5:
                        print(f"    ... and {len(os.listdir(ip))-5} more")
            else:
                print(f"  {item}")