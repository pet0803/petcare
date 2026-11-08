"""
阶段 3 验证脚本：RAG 检索测试（不依赖大模型）。

用法（在 backend/ 目录下，后端需已启动）：
    python scripts/test_retrieval.py

预期：
- 相关问题（幼猫喝牛奶 / 狗狗疫苗）返回多条 score 较高的片段
- 无关问题（股票）返回空数组或低分片段
"""
import sys
from pathlib import Path

# 允许从任意目录运行：把 backend/ 加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

BASE = "http://127.0.0.1:8000"


def ask(label: str, query: str, top_k: int = 4) -> None:
    print(f"===== {label}：{query} =====")
    resp = requests.post(
        f"{BASE}/api/search",
        json={"query": query, "top_k": top_k},
        timeout=120,
    )
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print(resp.text)
        return
    results = resp.json().get("results", [])
    if not results:
        print("结果: （空）")
        return
    for r in results:
        page = f"第{r['page']}页" if r.get("page") else "无页码"
        print(f"- score={r['score']:.3f} | {r['filename']} {page}")
        snippet = r["snippet"]
        print(f"  片段: {snippet[:80]}{'...' if len(snippet) > 80 else ''}")
    print()


def main() -> None:
    # 1. 先看文档列表，确认库里有数据
    resp = requests.get(f"{BASE}/api/documents", timeout=10)
    docs = resp.json().get("documents", [])
    print(f"===== 当前知识库共 {len(docs)} 个文档 =====")
    for doc in docs:
        print(f"- {doc['filename']} ({doc['chunk_count']} 个切片)")
    print()

    # 2. 相关问题
    ask("[A]", "幼猫可以喝牛奶吗？")
    ask("[B]", "狗狗的疫苗什么时候打？")

    # 3. 无关问题
    ask("[C]", "股票怎么买？")


if __name__ == "__main__":
    main()
