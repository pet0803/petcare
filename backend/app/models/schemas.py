"""
Pydantic 请求 / 响应模型。

字段与前端 TS 类型（frontend/src/types.ts）一一对应，保持命名一致。
"""
from pydantic import BaseModel


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
