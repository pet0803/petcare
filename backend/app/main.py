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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from app.routers import documents, search

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(search.router, prefix="/api", tags=["search"])

# 阶段 4：from app.routers import chat, sessions
#         app.include_router(chat.router, prefix="/api", tags=["chat"])
#         app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])

logger.info(
    "PetCare AI 启动配置摘要 | LLM: %s | Embedding: %s | TopK: %d | 阈值: %.2f",
    settings.llm_model,
    settings.embedding_model,
    settings.top_k,
    settings.retrieval_threshold,
)
