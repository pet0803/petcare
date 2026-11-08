"""
检索服务：问题向量化 → Chroma Top-K 相似度检索 → 阈值过滤。

RAG 流程的"召回"环节：
    query 文本 → Embedding API 向量化 → Chroma 余弦相似度检索 Top-K
    → score = 1 - 余弦距离（collection 建在 cosine 空间上）
    → 低于 settings.retrieval_threshold 的结果被丢弃

检索无结果返回空列表（不是错误）——阶段 4 的问答会按提示词回答
"抱歉，当前知识库中没有找到相关的内容"。
"""
from typing import Any

from langchain_core.documents import Document

from app.core.config import settings
from app.services.document_service import (
    EmbeddingError,
    MissingApiKeyError,
    _get_vector_store,
)

SNIPPET_MAX_LEN = 200  # 引用来源展示的片段截断长度


class RetrievalService:
    """向量检索的统一入口（阶段 4 的问答服务将复用它）。"""

    def search_with_docs(
        self, query: str, top_k: int | None = None
    ) -> list[tuple[Document, float]]:
        """检索并返回通过阈值过滤的 (Document, 相似度) 列表。

        Document 保留完整片段内容与 metadata（doc_id/filename/page），
        问答服务需要原始内容构建 RAG Prompt，因此单独提供此方法。
        """
        if not settings.siliconflow_api_key:
            raise MissingApiKeyError(
                "未配置 SILICONFLOW_API_KEY，请在 backend/.env 中填写"
            )
        k = min(top_k or settings.top_k, settings.max_top_k)
        try:
            # similarity_search_with_score 返回 (Document, distance) 列表；
            # cosine 空间下 distance = 1 - 余弦相似度，越小越相关
            hits = _get_vector_store().similarity_search_with_score(query, k=k)
        except Exception as e:
            raise EmbeddingError(f"检索失败：{e}") from e

        filtered: list[tuple[Document, float]] = []
        for doc, distance in hits:
            score = 1.0 - distance
            if score < settings.retrieval_threshold:
                continue
            filtered.append((doc, score))
        return filtered

    def search(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """检索并返回 API 友好的结果字典列表。"""
        return [
            self._to_dict(doc, score)
            for doc, score in self.search_with_docs(query, top_k)
        ]

    @staticmethod
    def _to_dict(doc: Document, score: float) -> dict[str, Any]:
        meta = doc.metadata
        content = doc.page_content.strip()
        return {
            "doc_id": meta.get("doc_id", ""),
            "filename": meta.get("filename", ""),
            "page": meta.get("page"),
            "score": round(score, 4),
            "snippet": (
                content
                if len(content) <= SNIPPET_MAX_LEN
                else content[:SNIPPET_MAX_LEN] + "…"
            ),
        }


# 模块级单例：路由直接使用
retrieval_service = RetrievalService()
