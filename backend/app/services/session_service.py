"""
会话管理：内存存储（无数据库）。

设计取舍：
- 演示项目足够用，后端重启后会话清空（面试时可主动说明，
  生产环境可替换为 Redis / 数据库，接口不变）
- get_or_create 语义：前端传入未知 session_id（如后端重启后
  浏览器 localStorage 里的旧 id）时自动按该 id 重建，前端无感知
- 历史裁剪保留最近 8 条（约 4 轮对话），控制 token 消耗
"""
import threading
import uuid
from datetime import datetime
from typing import Any

HISTORY_LIMIT = 8  # 送入 LLM 的最大历史消息条数


class Session:
    """一个会话：id + 消息列表。"""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages: list[dict[str, Any]] = []

    def append(
        self, role: str, content: str, sources: list[dict[str, Any]] | None = None
    ) -> None:
        msg = {
            "role": role,  # "user" | "assistant"
            "content": content,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if sources is not None:  # 仅 assistant 消息携带引用来源
            msg["sources"] = sources
        self.messages.append(msg)

    def history(self) -> list[dict[str, str]]:
        """返回裁剪后的历史（最近 HISTORY_LIMIT 条），供模型使用。"""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self.messages[-HISTORY_LIMIT:]
        ]


class SessionManager:
    """会话注册表（线程安全）。"""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def get_or_create(self, session_id: str | None) -> Session:
        """取会话；不存在则创建（session_id 为 None 时生成新 id）。"""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        sid = session_id or uuid.uuid4().hex
        with self._lock:
            if sid not in self._sessions:
                self._sessions[sid] = Session(sid)
        return self._sessions[sid]

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None


# 模块级单例：路由与问答服务共享
session_manager = SessionManager()
