"""
检索路由：独立的检索测试端点（不依赖大模型）。

用途：阶段 3 单独验证"问题 → 相关片段"的召回质量；
阶段 4 的问答接口内部走的是同一套检索逻辑。
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import SearchRequest, SearchResponse, SearchResult
from app.services.document_service import EmbeddingError, MissingApiKeyError
from app.services.retrieval_service import retrieval_service

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    """Top-K 相似度检索。无结果返回空数组（不是错误）。"""
    try:
        results = retrieval_service.search(req.query, req.top_k)
    except MissingApiKeyError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except EmbeddingError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return SearchResponse(results=[SearchResult(**r) for r in results])
