"""
文档管理路由：上传 / 列表 / 删除。

业务异常 → HTTP 状态码映射：
    UnsupportedFileTypeError -> 400
    FileTooLargeError         -> 413
    DocumentParseError        -> 422
    MissingApiKeyError        -> 503
    EmbeddingError            -> 502
"""
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import (
    DeleteResponse,
    DocumentInfo,
    DocumentListResponse,
    UploadResponse,
)
from app.services.document_service import (
    DocumentParseError,
    EmbeddingError,
    FileTooLargeError,
    MissingApiKeyError,
    UnsupportedFileTypeError,
    document_service,
)

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """上传并入库：解析 → 切片 → 向量化 → 写索引。

    同步函数（def 而非 async def）：FastAPI 会自动放入线程池执行，
    避免 pypdf 解析和 embedding 调用阻塞事件循环。
    """
    try:
        entry = document_service.upload_and_index(file)
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    except DocumentParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except MissingApiKeyError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except EmbeddingError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return UploadResponse(**entry)


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    """文档列表（数据来源：documents.json 索引）。"""
    return DocumentListResponse(
        documents=[DocumentInfo(**e) for e in document_service.list_documents()]
    )


@router.delete("/{doc_id}", response_model=DeleteResponse)
def delete_document(doc_id: str) -> DeleteResponse:
    """删除文档及其全部向量（文档不存在时返回 404）。"""
    if not document_service.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="文档不存在")
    return DeleteResponse(doc_id=doc_id, message="删除成功")
