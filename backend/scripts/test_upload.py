"""
阶段 2 验证脚本：上传样例 TXT → 文档列表 → 非法类型校验。

用法（在 backend/ 目录下，后端需已启动）：
    python scripts/test_upload.py
"""
import os
import sys
import tempfile
from pathlib import Path

# 允许从任意目录运行：把 backend/ 加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

BASE = "http://127.0.0.1:8000"


def main() -> None:
    # 1. 健康检查（确认服务在运行、Key 已配置）
    health = requests.get(f"{BASE}/api/health", timeout=10).json()
    print("[1] 健康检查:", health)
    if not health.get("embedding_configured"):
        print("[!] 警告：SILICONFLOW_API_KEY 未配置，上传会返回 503")
        return

    # 2. 上传样例 TXT（覆盖"幼猫不能喝牛奶/疫苗时间/狗吃巧克力中毒"等知识点）
    sample = Path(__file__).resolve().parent.parent / "data" / "sample" / "宠物喂养知识.txt"
    if not sample.exists():
        print("[!] 样例文件不存在:", sample)
        return
    with sample.open("rb") as f:
        resp = requests.post(
            f"{BASE}/api/documents/upload",
            files={"file": ("宠物喂养知识.txt", f, "text/plain")},
            timeout=180,  # 首次上传包含向量化，可能较慢
        )
    print("[2] 上传响应:", resp.status_code, resp.json())
    if resp.status_code != 200:
        print("[!] 上传失败，终止验证")
        return

    # 3. 文档列表（应包含刚上传的记录）
    resp = requests.get(f"{BASE}/api/documents", timeout=10)
    print("[3] 文档列表:", resp.status_code)
    for doc in resp.json()["documents"]:
        print("    -", doc)

    # 4. 非法类型校验（.md 应返回 400）
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        tmp.write(b"# test file")
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            resp = requests.post(
                f"{BASE}/api/documents/upload",
                files={"file": ("test.md", f, "text/markdown")},
                timeout=30,
            )
        print("[4] 非法类型响应:", resp.status_code, resp.json())
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
