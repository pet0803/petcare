"""
纯逻辑单元测试：不依赖网络与 API Key，不启动后端。

用法（在 backend/ 目录下）：
    python -m pip install pytest
    python -m pytest tests -v
"""
import sys
from pathlib import Path

# 允许从任意目录运行：把 backend/ 加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document

from app.prompts.rag_prompt import format_context
from app.services.document_service import DocumentService
from app.services.session_service import HISTORY_LIMIT, Session, SessionManager
from app.utils.text_utils import decode_text_bytes, make_snippet


# ==================== 编码兜底（text_utils） ====================

def test_decode_utf8() -> None:
    assert decode_text_bytes("宠物知识".encode("utf-8")) == "宠物知识"


def test_decode_gbk_fallback() -> None:
    # UTF-8 解码失败后自动按 GBK 解码（老 Windows 文本文件场景）
    assert decode_text_bytes("幼猫不能喝牛奶".encode("gbk")) == "幼猫不能喝牛奶"


def test_decode_replace_fallback() -> None:
    # 两种编码都失败：容错模式兜底，不抛异常、返回非空
    assert decode_text_bytes(b"\xff\xfe\x00garbage") != ""


# ==================== 关键词窗口摘要（make_snippet） ====================

def test_make_snippet_finds_keyword_window() -> None:
    # 关键内容在文本中段：窗口应定位到它，而不是固定取开头
    text = (
        "宠物日常护理知识。" * 10
        + "幼猫绝对不能喝牛奶，会乳糖不耐受导致腹泻。"
        + "疫苗知识。" * 10
    )
    snippet = make_snippet(text, "幼猫可以喝牛奶吗", max_len=50)
    assert "牛奶" in snippet
    assert len(snippet) <= 52  # 50 字窗口 + 两端省略号各 1 字


def test_make_snippet_short_text_passthrough() -> None:
    assert make_snippet("短文本", "任何问题", max_len=200) == "短文本"


def test_make_snippet_no_match_head_fallback() -> None:
    # 完全无字面命中（纯语义匹配场景）：回退到开头
    text = "开头的内容。" * 20 + "结尾的内容。" * 20
    assert make_snippet(text, "完全无关的查询词", max_len=30).startswith("开头的内容")


# ==================== 中文标点切片（DocumentService._split） ====================

def test_split_chinese_punctuation() -> None:
    service = DocumentService()
    text = "。".join(f"第{i}条宠物知识：幼猫需要按时接种疫苗" for i in range(60))
    chunks = service._split([{"text": text, "page": None}], doc_id="t1", filename="测试.txt")
    assert len(chunks) > 1  # 600 字切片上限：长文本必须切成多块
    assert all(c.metadata["doc_id"] == "t1" for c in chunks)
    assert all(c.metadata["filename"] == "测试.txt" for c in chunks)
    # overlap=120：切片内容总和应大于原文（有重叠）
    assert sum(len(c.page_content) for c in chunks) > len(text)


def test_split_keeps_page_metadata() -> None:
    service = DocumentService()
    chunks = service._split(
        [{"text": "宠物护理要点。" * 30, "page": 3}], doc_id="t2", filename="x.pdf"
    )
    assert chunks, "切片结果不应为空"
    assert all(c.metadata["page"] == 3 for c in chunks)  # PDF 页码进入引用来源


# ==================== 会话管理（SessionManager） ====================

def test_session_manager_get_or_create() -> None:
    mgr = SessionManager()
    s1 = mgr.get_or_create(None)  # 生成新 id
    assert mgr.get_or_create(s1.session_id) is s1  # 同 id 返回同一对象
    assert mgr.get_or_create("custom-id").session_id == "custom-id"
    assert mgr.get_or_create("custom-id") is mgr.get("custom-id")


def test_session_history_crop() -> None:
    s = Session("s1")
    for i in range(10):
        s.append("user", f"问题{i}")
    history = s.history()
    assert len(history) == HISTORY_LIMIT  # 历史裁剪，控制 token 消耗
    assert history[0]["content"] == f"问题{10 - HISTORY_LIMIT}"


def test_session_stores_sources() -> None:
    s = Session("s1")
    s.append("user", "幼猫可以喝牛奶吗？")
    s.append(
        "assistant",
        "不能。",
        [{"index": 1, "filename": "宠物喂养知识.txt", "page": None}],
    )
    assert s.messages[-1]["sources"][0]["index"] == 1
    assert "sources" not in s.messages[-2]  # user 消息不携带引用


# ==================== 引用编号格式化（format_context） ====================

def test_format_context_numbering() -> None:
    docs = [
        Document(page_content="内容A", metadata={"filename": "a.txt", "page": 1}),
        Document(page_content="内容B", metadata={"filename": "b.txt", "page": None}),
    ]
    ctx = format_context(docs)
    assert "[1] 来源《a.txt》第1页：" in ctx  # PDF 带页码
    assert "[2] 来源《b.txt》：" in ctx  # TXT 无页码
