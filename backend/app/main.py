"""
FastAPI 应用入口。

职责：
- 创建应用实例、配置 CORS
- 注册各功能路由（文档管理 / 检索 / 会话 / 问答，后续阶段逐步加入）
- 提供健康检查接口

启动方式（在 backend/ 目录下）：
    python -m uvicorn app.main:app --reload --port 8000
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("petcare")

app = FastAPI(
    title="PetCare AI",
    description="基于 RAG 的宠物智能知识库问答系统",
    version="0.1.0",
)

# CORS：前端开发服务器（Vite :5173）直连后端时兜底。
# 正常开发走 Vite 代理（同源），不依赖 CORS。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 全局异常处理 =====
# 未捕获异常统一返回中文 JSON detail，前端据此展示错误提示。

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """请求参数校验失败：422 + 首个字段错误信息。"""
    first = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(x) for x in first.get("loc", []))
    return JSONResponse(
        status_code=422,
        content={"detail": f"请求参数不合法：{loc} {first.get('msg', '')}"},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """HTTP 异常：仅把"路由不存在"的默认 404 中文化；
    业务抛出的 404（如"会话不存在"）等 detail 原样透传。"""
    if exc.status_code == 404 and exc.detail == "Not Found":
        return JSONResponse(status_code=404, content={"detail": "接口不存在"})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """兜底：未捕获异常记录日志并返回 500。
    SSE 流建立后发生的异常不经过这里，由 chat_service 自行发 error 事件。"""
    logger.exception("未处理异常: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500, content={"detail": f"服务器内部错误：{exc}"}
    )


@app.get("/api/health")
def health() -> dict:
    """健康检查：返回服务状态与 API Key 配置情况。

    Key 未配置时不报错，只返回 configured=false，
    方便阶段 1 快速验证链路是否打通。
    """
    return {
        "status": "ok",
        "llm_configured": bool(settings.deepseek_api_key),
        "embedding_configured": bool(settings.siliconflow_api_key),
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
    }


# ===== 路由注册 =====
# 阶段 2：文档上传 / 列表 / 删除
# 阶段 3：Top-K 相似度检索
# 阶段 4：SSE 流式问答 / 会话管理
from app.routers import chat, documents, search, sessions

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])

logger.info(
    "PetCare AI 启动配置摘要 | LLM: %s | Embedding: %s | TopK: %d | 阈值: %.2f",
    settings.llm_model,
    settings.embedding_model,
    settings.top_k,
    settings.retrieval_threshold,
)
