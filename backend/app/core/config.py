"""
全局配置模块。

所有配置项从 backend/.env 文件加载（pydantic-settings 自动读取），
API 密钥等敏感信息不写死在代码中。任何模块需要配置时：

    from app.core.config import settings

注意：.env 路径基于本文件的物理位置解析（backend/ 目录），
与启动命令的工作目录无关，因此从任意目录启动都安全。
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录（app/core/config.py 向上两级）
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """应用配置。字段名与环境变量一一对应（大小写不敏感）。"""

    # --- API 密钥 ---
    deepseek_api_key: str = ""
    siliconflow_api_key: str = ""

    # --- 模型配置（DeepSeek 模型名迁移时只需改 .env，代码零改动）---
    llm_model: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com"
    embedding_model: str = "BAAI/bge-m3"
    embedding_base_url: str = "https://api.siliconflow.cn/v1"

    # --- RAG 参数 ---
    top_k: int = 4                # 检索返回的片段数
    max_top_k: int = 8            # 检索上限
    retrieval_threshold: float = 0.3   # 相似度阈值（score = 1 - 余弦距离）
    chunk_size: int = 600         # 切片字符数
    chunk_overlap: int = 120      # 相邻切片重叠字符数

    # --- 上传限制 ---
    max_upload_mb: int = 20

    # --- 存储路径（运行时自动创建）---
    data_dir: Path = BASE_DIR / "data"
    uploads_dir: Path = BASE_DIR / "data" / "uploads"
    chroma_dir: Path = BASE_DIR / "data" / "chroma"
    sample_dir: Path = BASE_DIR / "data" / "sample"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略 .env 中未定义的其他变量
    )


# 模块级单例：整个后端共享一份配置
settings = Settings()
