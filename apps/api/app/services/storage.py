import os
import uuid
from pathlib import Path

from app.config import settings


def save_upload_file(file_content: bytes, filename: str, subdir: str = "images") -> str:
    """保存上传文件到本地，返回可访问的 URL 路径（相对路径，用于存储）。"""
    base = Path(settings.storage_local_path) / subdir
    base.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    path = base / name
    path.write_bytes(file_content)
    return f"/uploads/{subdir}/{name}"


def get_local_url(relative_path: str) -> str:
    """将存储相对路径转为可访问 URL（本地开发）。"""
    return relative_path
