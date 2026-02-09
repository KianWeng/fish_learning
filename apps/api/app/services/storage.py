"""
本地文件存储：按类型分目录（头像 / 题目图 / PDF），图片压缩节省空间，返回 /files/* 路径由后端鉴权下发。
"""
import uuid
from io import BytesIO
from pathlib import Path

from app.config import settings

SUBDIR_AVATARS = "avatars"
SUBDIR_QUESTIONS = "questions"
SUBDIR_PDFS = "pdfs"

# 仅允许文件名为 字母数字+点，防止路径穿越
def _safe_filename(name: str) -> bool:
    return len(name) <= 64 and all(c.isalnum() or c in ".-_" for c in name)


def _compress_image(content: bytes, max_width: int, max_height: int, quality: int = 85) -> bytes:
    """压缩图片为 JPEG，限制最大宽高，节省存储。"""
    try:
        from PIL import Image
        img = Image.open(BytesIO(content)).convert("RGB")
        w, h = img.size
        if w > max_width or h > max_height:
            ratio = min(max_width / w, max_height / h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        out = BytesIO()
        img.save(out, "JPEG", quality=quality, optimize=True)
        return out.getvalue()
    except Exception:
        return content


def save_avatar(file_content: bytes, filename: str = "avatar.jpg") -> tuple[str, int]:
    """保存用户头像到 avatars/，压缩后存储，返回 (访问路径, 写入字节数)。"""
    compressed = _compress_image(file_content, max_width=400, max_height=400, quality=85)
    base = Path(settings.storage_local_path) / SUBDIR_AVATARS
    base.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.jpg"
    (base / name).write_bytes(compressed)
    return f"/files/avatars/{name}", len(compressed)


def save_question_image(file_content: bytes, filename: str = "image.jpg") -> tuple[str, int]:
    """保存拍题图片到 questions/，压缩后存储，返回 (访问路径, 写入字节数)。"""
    compressed = _compress_image(file_content, max_width=1200, max_height=1600, quality=88)
    base = Path(settings.storage_local_path) / SUBDIR_QUESTIONS
    base.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or ".jpg"
    if ext.lower() not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    (base / name).write_bytes(compressed)
    return f"/files/questions/{name}", len(compressed)


def save_upload_file(file_content: bytes, filename: str, subdir: str = "questions") -> tuple[str, int]:
    """
    通用保存：subdir 建议用 SUBDIR_QUESTIONS / SUBDIR_PDFS。
    返回 (访问路径, 写入字节数)。
    """
    base = Path(settings.storage_local_path) / subdir
    base.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or (".pdf" if subdir == SUBDIR_PDFS else ".jpg")
    name = f"{uuid.uuid4().hex}{ext}"
    (base / name).write_bytes(file_content)
    return f"/files/{subdir}/{name}", len(file_content)


def get_file_path(url_path: str) -> Path | None:
    """
    根据访问路径 /files/avatars/xxx 或 /files/questions/xxx 得到本地文件路径。
    若路径不合法或文件不存在则返回 None。
    """
    url_path = url_path.strip().lstrip("/")
    if not url_path.startswith("files/"):
        return None
    rest = url_path[6:]  # after "files/"
    if "/" in rest:
        subdir, name = rest.split("/", 1)
    else:
        return None
    if subdir not in (SUBDIR_AVATARS, SUBDIR_QUESTIONS, SUBDIR_PDFS) or not _safe_filename(name):
        return None
    path = Path(settings.storage_local_path) / subdir / name
    return path if path.is_file() else None


def get_local_url_legacy(relative_path: str) -> str:
    """兼容旧数据：原 /uploads/... 仍可经静态或重定向处理。"""
    return relative_path


def get_file_size(url: str | None) -> int:
    """若 url 为本应用 /files/... 路径且文件存在，返回文件字节数，否则返回 0。"""
    if not url or not (url.strip().startswith("/files/")):
        return 0
    path = get_file_path(url.strip())
    if not path:
        return 0
    try:
        return path.stat().st_size
    except OSError:
        return 0


def delete_file_by_url(url: str | None) -> tuple[bool, int]:
    """
    若 url 为本应用 /files/... 路径，则删除对应本地文件，返回 (True, 释放字节数)；
    否则返回 (False, 0)。忽略文件不存在等错误。
    """
    if not url or not (url.strip().startswith("/files/")):
        return False, 0
    path = get_file_path(url.strip())
    if not path:
        return False, 0
    size = 0
    try:
        size = path.stat().st_size
    except OSError:
        pass
    try:
        path.unlink()
        return True, size
    except OSError:
        return False, 0
