"""
会话路由：创建 / 查询 / 删除。

会话存储在内存中（SessionManager），后端重启后清空；
前端把 session_id 存 localStorage，重启后请求未知 id 会自动重建，前端无感知。
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    SessionCreateResponse,
    SessionDeleteResponse,
    SessionInfo,
)
from app.services.session_service import session_manager

router = APIRouter()


@router.post("", response_model=SessionCreateResponse)
def create_session() -> SessionCreateResponse:
    """新建会话，返回 session_id（前端保存到 localStorage）。"""
    session = session_manager.get_or_create(None)
    return SessionCreateResponse(
        session_id=session.session_id, created_at=session.created_at
    )


@router.get("/{session_id}", response_model=SessionInfo)
def get_session(session_id: str) -> SessionInfo:
    """查询会话历史（前端刷新页面后恢复对话）。"""
    session = session_manager.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return SessionInfo(
        session_id=session.session_id,
        created_at=session.created_at,
        messages=session.messages,
    )


@router.delete("/{session_id}", response_model=SessionDeleteResponse)
def delete_session(session_id: str) -> SessionDeleteResponse:
    """删除会话。"""
    if not session_manager.delete(session_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    return SessionDeleteResponse(session_id=session_id, message="删除成功")
