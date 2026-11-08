"""
问答路由：SSE 流式问答（系统核心端点）。

POST /api/chat
    body: {"session_id": "可选", "question": "..."}
    response: text/event-stream
        事件顺序：token（多个）→ sources → done；流内出错发 error

错误策略：
    - 检索失败 / 未配置 Key：流建立前抛 HTTPException（普通 JSON 错误，前端易处理）
    - 生成过程中出错：error 事件 + 关闭流
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.models.schemas import ChatRequest
from app.services.chat_service import chat_service
from app.services.document_service import EmbeddingError, MissingApiKeyError
from app.services.retrieval_service import retrieval_service
from app.services.session_service import session_manager

router = APIRouter()


@router.post("/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    """RAG 流式问答（SSE）。session_id 未知时自动重建会话。"""
    if not settings.deepseek_api_key:
        raise HTTPException(
            status_code=503,
            detail="未配置 DEEPSEEK_API_KEY，请在 backend/.env 中填写",
        )

    # 会话：不传 / 传入未知 id（如后端重启后）都自动创建
    session = session_manager.get_or_create(req.session_id)

    # 检索在流建立前完成：失败以普通 JSON 返回，避免流中途断裂
    try:
        hits = retrieval_service.search_with_docs(req.question, settings.top_k)
    except MissingApiKeyError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except EmbeddingError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    # 调用即返回异步生成器对象，事件在响应过程中逐帧产出
    return StreamingResponse(
        chat_service.stream_answer(session, req.question, hits),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
