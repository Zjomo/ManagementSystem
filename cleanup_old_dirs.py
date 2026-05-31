import os
import shutil
import stat

BASE_DIR = r"f:\0_MyNote\0_硕士\4、竞赛\0_2026竞赛辅导【14人】"

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_rmtree(path):
    if os.path.exists(path):
        shutil.rmtree(path, onerror=remove_readonly)
        print(f"  ✅ 已删除: {path}")

# 1. 删除 创芯大赛 的旧0_竞赛报名表+合照目录（已全部迁移到00_参赛学生）
old = os.path.join(BASE_DIR, "1_创芯大赛", "0_竞赛报名表+合照")
if os.path.exists(old):
    size = sum(os.path.getsize(os.path.join(dirpath, f)) 
               for dirpath, _, filenames in os.walk(old) for f in filenames)
    print(f"删除创芯大赛旧目录: {old} ({size/1024/1024:.1f}MB)")
    safe_rmtree(old)

# 2. 删除 智能创建大赛 旧目录（含.git残留）
old2 = os.path.join(BASE_DIR, "3_智能创建大赛", "赛题4：融合LLM与知识图谱的施工现场安全风险隐患智能研判方法-姚一鸣-研一")
if os.path.exists(old2):
    safe_rmtree(old2)

print("\n✅ 清理完成！")