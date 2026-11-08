"""
Pydantic 请求 / 响应模型。

字段与前端 TS 类型（frontend/src/types.ts）一一对应，保持命名一致。
"""
from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    """文档索引条目。"""

    doc_id: str
    filename: str          # 原始文件名（中文原样保存）
    file_type: str         # "pdf" | "txt"
    size_bytes: int
    chunk_count: int
    uploaded_at: str       # "YYYY-MM-DD HH:MM:SS"


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]


class UploadResponse(DocumentInfo):
    message: str = "上传成功"


class DeleteResponse(BaseModel):
    doc_id: str
    message: str


class SearchRequest(BaseModel):
    """检索请求。"""

    query: str = Field(min_length=1, max_length=500)
    top_k: int | None = Field(default=None, ge=1, le=8)  # 上限与 settings.max_top_k 一致


class SearchResult(BaseModel):
    """检索结果条目。"""

    doc_id: str
    filename: str
    page: int | None = None    # TXT 无页码为 null
    score: float               # 相似度 = 1 - 余弦距离，越高越相关
    snippet: str               # 片段文本（最多 200 字）


class SearchResponse(BaseModel):
    results: list[SearchResult]


class ChatRequest(BaseModel):
    """流式问答请求。session_id 可选：不传或传未知 id 都会自动创建/重建会话。"""

    session_id: str | None = None
    question: str = Field(min_length=1, max_length=2000)


class ChatMessage(BaseModel):
    """会话中的一条消息。"""

    role: str                # "user" | "assistant"
    content: str
    created_at: str | None = None


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    messages: list[ChatMessage]


class SessionCreateResponse(BaseModel):
    session_id: str
    created_at: str


class SessionDeleteResponse(BaseModel):
    session_id: str
    message: str
