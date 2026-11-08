"""
文本处理工具。
"""
import re

# 疑问词 / 虚词：从问题中提取关键词时过滤掉，避免它们干扰窗口打分
_QUESTION_FILLER_CHARS = set(
    "吗呢吧啊呀么的了是什么怎么为什么可以能不能请问告诉"
    "我一下哪些多少什么时候哪里哪个是不是有关对于在把被"
)


def decode_text_bytes(data: bytes) -> str:
    """按 utf-8 → gbk 顺序尝试解码文本字节，最后用 utf-8 容错模式兜底。

    覆盖中文用户常见场景：现代文本多为 UTF-8，老旧 Windows 文本多为 GBK；
    两种编码都失败时用 errors="replace" 保证不崩溃（乱码优于报错）。
    """
    for encoding in ("utf-8", "gbk"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def make_snippet(text: str, query: str, max_len: int = 200) -> str:
    """从切片文本中截取与 query 最相关的一段作为摘要。

    RAG 检索是语义匹配，query 往往不会逐字出现在文本中；
    因此从 query 提取关键词（去掉标点与疑问词/虚词后的相邻两字组合），
    在文本上滑动打分，返回命中关键词最多的窗口；
    完全无字面命中时回退到开头 max_len 字。
    相比固定取前 N 字，引用卡片能展示真正回答问题的部分。
    """
    text = text.strip()
    if len(text) <= max_len:
        return text

    # 提取关键词：去掉标点/数字/空白后，过滤疑问词与虚词
    cleaned = re.sub(r"[\W\d_]+", "", query, flags=re.UNICODE)
    cleaned = "".join(ch for ch in cleaned if ch not in _QUESTION_FILLER_CHARS)
    grams = {cleaned[i : i + 2] for i in range(len(cleaned) - 1)}
    if not grams:
        return text[:max_len] + "…"

    # 滑动打分：步长为半个窗口，取命中次数最多的窗口位置
    best_start, best_score = 0, 0
    step = max_len // 2
    for start in range(0, len(text) - max_len + 1, step):
        window = text[start : start + max_len]
        score = sum(window.count(g) for g in grams)
        if score > best_score:
            best_start, best_score = start, score

    if best_score == 0:
        return text[:max_len] + "…"
    snippet = text[best_start : best_start + max_len]
    prefix = "…" if best_start > 0 else ""
    suffix = "…" if best_start + max_len < len(text) else ""
    return f"{prefix}{snippet}{suffix}"
