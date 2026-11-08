"""
阶段 6 冒烟测试：一键端到端回归（无第三方测试框架）。

用法（在 backend/ 目录下，后端需已启动）：
    python scripts/smoke_test.py

覆盖链路：
    health → 上传样例 → 检索断言 → 建会话 → SSE 流式问答（含引用来源）
    → 会话历史（含引用持久化）→ 清理（删除测试文档 / 会话，不留痕迹）
全部通过打印 PASS 且退出码 0；任何一项失败打印 FAIL 且退出码 1。
"""
import json
import sys
from pathlib import Path

# 允许从任意目录运行：把 backend/ 加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

BASE = "http://127.0.0.1:8000"
SAMPLE = (
    Path(__file__).resolve().parent.parent / "data" / "sample" / "宠物喂养知识.txt"
)

passed: list[str] = []
failed: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    """记录一项检查结果并即时打印。"""
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" —— {detail}" if detail else ""))
    (passed if ok else failed).append(name)


def main() -> None:
    print("=" * 64)
    print("PetCare AI 冒烟测试（后端需已启动）")
    print("=" * 64)

    # 0. 前置检查：后端连通 + API Key 配置（不满足则无法继续，直接退出）
    try:
        resp = requests.get(f"{BASE}/api/health", timeout=10)
    except requests.ConnectionError:
        print("[FAIL] 无法连接 http://127.0.0.1:8000，请先启动后端")
        sys.exit(1)
    health = resp.json()
    if not (health.get("llm_configured") and health.get("embedding_configured")):
        print("[FAIL] API Key 未配置完整，请检查 backend/.env")
        sys.exit(1)
    check(
        "健康检查",
        resp.status_code == 200 and health.get("status") == "ok",
        f"LLM={health['llm_model']} Embedding={health['embedding_model']}",
    )

    doc_id: str | None = None
    session_id: str | None = None
    try:
        # 1. 上传样例文档（解析 + 切片 + 向量化全链路）
        with SAMPLE.open("rb") as f:
            resp = requests.post(
                f"{BASE}/api/documents/upload",
                files={"file": (SAMPLE.name, f, "text/plain")},
                timeout=180,  # 首次向量化可能较慢
            )
        if resp.status_code == 200:
            body = resp.json()
            doc_id = body.get("doc_id")
            check(
                "上传文档",
                bool(doc_id) and body.get("chunk_count", 0) > 0,
                f"chunk_count={body.get('chunk_count')}",
            )
        else:
            check("上传文档", False, f"{resp.status_code} {resp.text[:120]}")

        # 2. 检索断言：相关问题应召回高相似度片段
        resp = requests.post(
            f"{BASE}/api/search", json={"query": "幼猫可以喝牛奶吗"}, timeout=60
        )
        results = resp.json().get("results", []) if resp.status_code == 200 else []
        if results:
            check(
                "检索相关问题",
                results[0]["score"] > 0.5,
                f"top1 score={results[0]['score']:.3f}，片段：{results[0]['snippet'][:40]}…",
            )
        else:
            check("检索相关问题", False, "未召回任何结果")

        # 3. 建会话 + SSE 流式问答（token → sources → done 事件顺序）
        resp = requests.post(f"{BASE}/api/sessions", timeout=10)
        check("创建会话", resp.status_code == 200)
        session_id = resp.json().get("session_id")

        tokens: list[str] = []
        sources: list[dict] = []
        got_done = False
        stream_error: str | None = None
        resp = requests.post(
            f"{BASE}/api/chat",
            json={"session_id": session_id, "question": "幼猫可以喝牛奶吗？"},
            stream=True,
            timeout=180,
        )
        event = None
        for line in resp.iter_lines(decode_unicode=True):
            if line is None or line == "":
                event = None  # SSE 帧分隔
                continue
            if line.startswith("event: "):
                event = line[7:].strip()
            elif line.startswith("data: ") and event:
                data = json.loads(line[6:])
                if event == "token":
                    tokens.append(data.get("content", ""))
                elif event == "sources":
                    sources = data.get("sources", [])
                elif event == "done":
                    got_done = True
                elif event == "error":
                    stream_error = data.get("message")
        answer = "".join(tokens)
        check(
            "SSE 流式问答",
            bool(tokens) and got_done and not stream_error,
            f"回答：{answer[:40]}…" + (f"（错误：{stream_error}）" if stream_error else ""),
        )
        check(
            "引用来源事件",
            len(sources) > 0,
            f"{len(sources)} 条，第一条：{sources[0]['filename']} score={sources[0]['score']}"
            if sources
            else "sources 为空",
        )

        # 4. 会话历史：引用来源应随消息持久化（历史会话恢复依赖此数据）
        resp = requests.get(f"{BASE}/api/sessions/{session_id}", timeout=10)
        messages = resp.json().get("messages", []) if resp.status_code == 200 else []
        assistant = [m for m in messages if m.get("role") == "assistant"]
        ok = len(messages) == 2 and bool(assistant) and bool(assistant[0].get("sources"))
        check(
            "会话历史与引用持久化",
            ok,
            f"{len(messages)} 条消息，assistant 引用 {len(assistant[0].get('sources', [])) if assistant else 0} 条",
        )
    finally:
        # 5. 清理：删除测试上传的文档与会话，不留测试痕迹
        if doc_id:
            resp = requests.delete(f"{BASE}/api/documents/{doc_id}", timeout=30)
            check("清理文档", resp.status_code == 200)
        if session_id:
            requests.delete(f"{BASE}/api/sessions/{session_id}", timeout=10)

    print("=" * 64)
    print(f"结果：{len(passed)} 通过，{len(failed)} 失败")
    if failed:
        print("FAIL —— 失败项：", ", ".join(failed))
        sys.exit(1)
    print("PASS —— 全链路验证通过 ✅")


if __name__ == "__main__":
    main()
