"""
文档服务：上传、解析、切片、向量化与索引管理。

RAG 流程的"入库"环节，数据流：
    上传文件 → 校验类型/大小 → 落盘（uuid 文件名，规避中文文件名问题）
    → 解析文本（pypdf 逐页 / TXT 编码兜底）→ 递归字符切片（中文标点感知）
    → Embedding API 向量化（SiliconFlow bge-m3，1024 维）→ Chroma 持久化存储
    → 更新 documents.json 索引（文档列表接口的数据来源）

设计要点：
- 原子性：解析或向量化任一环节失败，不写索引、清理已写入的部分向量
- 中文文件名：磁盘文件统一用 uuid 命名，原始文件名只保存在索引 JSON 中
- 并发安全：documents.json 读写用线程锁保护
"""
import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.core.config import settings
from app.utils.text_utils import decode_text_bytes

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


# ===== 业务异常：路由层据此映射为对应的 HTTP 状态码 =====
class DocumentServiceError(Exception):
    """文档服务异常基类。"""


class UnsupportedFileTypeError(DocumentServiceError):
    """文件类型不在白名单。"""


class FileTooLargeError(DocumentServiceError):
    """文件超过大小上限。"""


class DocumentParseError(DocumentServiceError):
    """文本提取失败（扫描版/加密 PDF、空文件等）。"""


class MissingApiKeyError(DocumentServiceError):
    """未配置 Embedding API Key。"""


class EmbeddingError(DocumentServiceError):
    """向量化或向量库写入失败（网络/额度/维度不匹配等）。"""


def _slugify(model_name: str) -> str:
    """把模型名转成合法的 collection 名片段：'BAAI/bge-m3' -> 'baai_bge_m3'"""
    return model_name.lower().replace("/", "_").replace("-", "_")


# collection 名绑定 embedding 模型：换模型自动落到新 collection，避免维度冲突
COLLECTION_NAME = f"petcare_{_slugify(settings.embedding_model)}"

# ===== 单例：Embedding 客户端与向量库（懒加载，首次使用时初始化）=====
_embeddings: OpenAIEmbeddings | None = None
_vector_store: Chroma | None = None


def _get_embeddings() -> OpenAIEmbeddings:
    """SiliconFlow 的 Embedding 客户端（OpenAI 兼容协议）。"""
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.siliconflow_api_key,
            base_url=settings.embedding_base_url,
            # SiliconFlow bge-m3 固定输出 1024 维：不传 dimensions 参数（传了会 400）
            # tiktoken 不认识 bge-m3：必须关闭上下文长度检查，否则直接崩溃
            check_embedding_ctx_length=False,
            # langchain-openai 1.x 直接接受 timeout/max_retries 参数
            #（旧版的 request_options 参数已移除，传了会报 TypeError）
            max_retries=3,
            timeout=60,
        )
    return _embeddings


def _get_vector_store() -> Chroma:
    """Chroma 持久化向量库（backend/data/chroma）。"""
    global _vector_store
    if _vector_store is None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=_get_embeddings(),
            persist_directory=str(settings.chroma_dir),
            # 余弦空间：检索时 similarity = 1 - distance
            collection_metadata={"hnsw:space": "cosine"},
        )
    return _vector_store


class DocumentService:
    """文档入库 / 列表 / 删除的统一入口（路由层只调用它）。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    # ---------- 索引读写（documents.json）----------
    def _index_path(self) -> Path:
        return settings.data_dir / "documents.json"

    def _load_index(self) -> list[dict[str, Any]]:
        path = self._index_path()
        if not path.exists():
            return []
        with self._lock:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _save_index(self, entries: list[dict[str, Any]]) -> None:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._index_path(), "w", encoding="utf-8") as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)

    # ---------- 上传与入库 ----------
    def upload_and_index(self, file: UploadFile) -> dict[str, Any]:
        """核心入库流程：校验 → 落盘 → 解析 → 切片 → 向量化 → 写索引。"""
        if not settings.siliconflow_api_key:
            raise MissingApiKeyError(
                "未配置 SILICONFLOW_API_KEY，请在 backend/.env 中填写"
            )

        filename = (file.filename or "").strip()
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError("仅支持 PDF 和 TXT 文件")

        # 分块读出内容并检查大小（UploadFile 是流式对象）
        content = file.file.read()
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise FileTooLargeError(f"文件超过 {settings.max_upload_mb}MB 限制")

        doc_id = uuid.uuid4().hex
        file_type = ext.lstrip(".")

        # 落盘：磁盘文件名用 uuid，原始文件名（可能是中文）只进索引
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        disk_path = settings.uploads_dir / f"{doc_id}{ext}"
        disk_path.write_bytes(content)

        try:
            # 1) 解析：PDF 逐页提取，TXT 编码兜底解码
            if file_type == "pdf":
                sections = self._parse_pdf(disk_path)
            else:
                sections = self._parse_txt(disk_path)

            # 2) 切片：中文标点感知的递归切片
            chunks = self._split(sections, doc_id=doc_id, filename=filename)

            # 3) 向量化 + 写入 Chroma
            self._embed_and_store(chunks, doc_id)
        except DocumentServiceError:
            disk_path.unlink(missing_ok=True)  # 清理未入库的半成品文件
            raise
        except Exception as e:
            disk_path.unlink(missing_ok=True)
            raise DocumentParseError(f"文档处理失败：{e}") from e

        # 全部成功后才写索引（原子性：失败路径不会走到这里）
        entry = {
            "doc_id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "size_bytes": len(content),
            "chunk_count": len(chunks),
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        entries = self._load_index()
        entries.append(entry)
        self._save_index(entries)
        return entry

    def _parse_pdf(self, path: Path) -> list[dict[str, Any]]:
        """逐页提取 PDF 文本，每页为一个切片单元（页码将进入引用来源）。"""
        reader = PdfReader(str(path))
        sections = []
        for page_no, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                sections.append({"text": text, "page": page_no})
        total = sum(len(s["text"]) for s in sections)
        if total < 50:
            raise DocumentParseError("无法提取文本：可能是扫描版或加密 PDF")
        return sections

    def _parse_txt(self, path: Path) -> list[dict[str, Any]]:
        text = decode_text_bytes(path.read_bytes()).strip()
        if len(text) < 10:
            raise DocumentParseError("文本内容为空或无法解析")
        return [{"text": text, "page": None}]

    def _split(
        self, sections: list[dict[str, Any]], *, doc_id: str, filename: str
    ) -> list[Document]:
        """按中文标点感知的规则切片，metadata 记录文档归属与页码。

        separators 中显式加入中文标点：默认的英文分隔符（空格/换行）
        无法把连续的中文句子切开，会把整篇文章切成一整块。
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
            length_function=len,
        )
        chunks: list[Document] = []
        for section in sections:
            for piece in splitter.split_text(section["text"]):
                chunks.append(
                    Document(
                        page_content=piece,
                        metadata={
                            "doc_id": doc_id,
                            "filename": filename,
                            "page": section["page"],
                        },
                    )
                )
        if not chunks:
            raise DocumentParseError("文档切片结果为空")
        return chunks

    def _embed_and_store(self, chunks: list[Document], doc_id: str) -> None:
        """向量化并写入 Chroma；失败时清理已写入的部分向量，不留半份文档。"""
        ids = [f"{doc_id}:{i}" for i in range(len(chunks))]
        try:
            _get_vector_store().add_documents(documents=chunks, ids=ids)
        except Exception as e:
            # 原子性：可能已写入部分向量，按 doc_id 清理
            try:
                _get_vector_store().delete(where={"doc_id": doc_id})
            except Exception:
                pass  # 清理失败不影响主错误抛出
            detail = str(e)
            if "dimension" in detail.lower():
                detail += (
                    "（向量维度与已有数据不一致：请确认 .env 中 EMBEDDING_MODEL 未更换，"
                    "或删除 backend/data/chroma 目录重建向量库）"
                )
            raise EmbeddingError(f"向量化或入库失败：{detail}") from e

    # ---------- 列表 / 删除 ----------
    def list_documents(self) -> list[dict[str, Any]]:
        """返回索引中的全部文档条目。"""
        return self._load_index()

    def delete_document(self, doc_id: str) -> bool:
        """删除文档：向量 → 索引 → 磁盘文件。返回是否找到并删除。"""
        entries = self._load_index()
        target = next((e for e in entries if e["doc_id"] == doc_id), None)
        if target is None:
            return False
        _get_vector_store().delete(where={"doc_id": doc_id})
        entries.remove(target)
        self._save_index(entries)
        disk_path = settings.uploads_dir / f"{doc_id}.{target['file_type']}"
        disk_path.unlink(missing_ok=True)
        return True


# 模块级单例：路由直接使用
document_service = DocumentService()
