"""
阶段 4 验证脚本：SSE 流式问答 + 多轮会话 + 未知会话自动重建。

用法（在 backend/ 目录下，后端需已启动）：
    python scripts/test_chat.py

验证点：
1. token 逐字打印 → 证明是真实流式输出（非一次性返回）
2. 结尾 sources 带文件名 / 片段 / 分数 → 引用来源链路
3. 追问"那疫苗呢"能接上上文 → 多轮对话
4. 未知 session_id 自动重建 → 内存会话的容错设计
"""
import json
import sys
from pathlib import Path

# 允许从任意目录运行：把 backend/ 加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

BASE = "http://127.0.0.1:8000"


def ask(session_id: str | None, question: str) -> None:
    print(f"\n===== 提问：{question} =====")
    resp = requests.post(
        f"{BASE}/api/chat",
        json={"session_id": session_id, "question": question},
        stream=True,
        timeout=180,
    )
    if resp.status_code != 200:
        print(f"错误: {resp.status_code} {resp.text}")
        return

    event = None
    sources = []
    for line in resp.iter_lines(decode_unicode=True):
        if line is None or line == "":
            event = None  # SSE 帧分隔
            continue
        if line.startswith("event: "):
            event = line[7:].strip()
        elif line.startswith("data: ") and event:
            data = json.loads(line[6:])
            if event == "token":
                print(data.get("content", ""), end="", flush=True)  # 逐字打印
            elif event == "sources":
                sources = data.get("sources", [])
            elif event == "error":
                print(f"\n[流内错误] {data.get('message')}")

    print()  # 换行
    if sources:
        print("引用来源:")
        for s in sources:
            page = f"第{s['page']}页" if s.get("page") else "无页码"
            snippet = s["snippet"]
            print(f"  [{s['index']}] {s['filename']} {page} score={s['score']}")
            print(f"      片段: {snippet[:60]}{'...' if len(snippet) > 60 else ''}")
    else:
        print("（无引用来源）")


def main() -> None:
    # 1. 新建会话
    resp = requests.post(f"{BASE}/api/sessions", timeout=10)
    print("新建会话:", resp.json())
    sid = resp.json()["session_id"]

    # 2. 第一问 + 追问（验证多轮：追问省略了主语，依赖上一轮上下文）
    ask(sid, "幼猫可以喝牛奶吗？")
    ask(sid, "那猫咪的疫苗呢？")

    # 3. 未知 session_id 自动重建（模拟后端重启后前端拿旧 id 提问）
    ask("unknown-session-id-123", "狗能吃巧克力吗？")

    # 4. 查看会话历史（确认问答已写入会话）
    resp = requests.get(f"{BASE}/api/sessions/{sid}", timeout=10)
    print(f"\n===== 会话历史（{len(resp.json()['messages'])} 条消息）=====")
    for m in resp.json()["messages"]:
        print(f"  {m['role']}: {m['content'][:60]}...")


if __name__ == "__main__":
    main()
