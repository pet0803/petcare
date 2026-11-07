"""
文本处理工具。
"""


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
