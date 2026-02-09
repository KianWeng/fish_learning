"""
本地文件存储：按用户分目录 uploads/<storage_key>/avatars|questions|pdfs，
storage_key 由用户微信 openid 安全化得到，URL 形如 /files/<subdir>/<storage_key>/<filename>。
兼容旧 URL：/files/<subdir>/<filename> 及 /files/<subdir>/<user_id>/<filename>（数字 user_id）。
"""
import hashlib
import uuid
from io import BytesIO
from pathlib import Path

from app.config import settings

SUBDIR_AVATARS = "avatars"
SUBDIR_QUESTIONS = "questions"
SUBDIR_PDFS = "pdfs"


def _safe_filename(name: str) -> bool:
    return len(name) <= 64 and all(c.isalnum() or c in ".-_" for c in name)


def _safe_storage_key(s: str) -> bool:
    """路径段仅允许字母数字与 _-，长度 1~64。"""
    return 1 <= len(s) <= 64 and all(c.isalnum() or c in "_-" for c in s)


def user_storage_key(openid: str) -> str:
    """
    用微信 openid 生成存储目录名（唯一且安全）。
    若 openid 仅含字母数字与 _- 则直接使用，否则用 sha256 前 32 位 hex，避免暴露 openid 且兼容文件系统。
    """
    if not openid:
        raise ValueError("openid 为空")
    if _safe_storage_key(openid):
        return openid
    return hashlib.sha256(openid.encode()).hexdigest()[:32]


def _user_base(storage_key: str) -> Path:
    """用户存储根目录 uploads/<storage_key>。"""
    return Path(settings.storage_local_path) / storage_key


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


def save_avatar(file_content: bytes, filename: str, storage_key: str) -> tuple[str, int]:
    """保存用户头像到 uploads/<storage_key>/avatars/，返回 (访问路径, 写入字节数)。storage_key 由 user_storage_key(openid) 得到。"""
    compressed = _compress_image(file_content, max_width=400, max_height=400, quality=85)
    base = _user_base(storage_key) / SUBDIR_AVATARS
    base.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.jpg"
    (base / name).write_bytes(compressed)
    return f"/files/{SUBDIR_AVATARS}/{storage_key}/{name}", len(compressed)


def save_question_image(file_content: bytes, filename: str, storage_key: str) -> tuple[str, int]:
    """保存拍题图片到 uploads/<storage_key>/questions/，返回 (访问路径, 写入字节数)。"""
    compressed = _compress_image(file_content, max_width=1200, max_height=1600, quality=88)
    base = _user_base(storage_key) / SUBDIR_QUESTIONS
    base.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or ".jpg"
    if ext.lower() not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    (base / name).write_bytes(compressed)
    return f"/files/{SUBDIR_QUESTIONS}/{storage_key}/{name}", len(compressed)


def save_upload_file(
    file_content: bytes, filename: str, subdir: str, storage_key: str
) -> tuple[str, int]:
    """保存到 uploads/<storage_key>/<subdir>/，返回 (访问路径, 写入字节数)。subdir 用 SUBDIR_PDFS 等。"""
    base = _user_base(storage_key) / subdir
    base.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or (".pdf" if subdir == SUBDIR_PDFS else ".jpg")
    name = f"{uuid.uuid4().hex}{ext}"
    (base / name).write_bytes(file_content)
    return f"/files/{subdir}/{storage_key}/{name}", len(file_content)


def get_file_path(url_path: str) -> Path | None:
    """
    根据访问路径解析本地文件路径。
    - 新格式: /files/avatars/<user_id>/<filename> -> uploads/<user_id>/avatars/<filename>
    - 旧格式(迁移前): /files/avatars/<filename> -> uploads/avatars/<filename>
    """
    url_path = url_path.strip().lstrip("/")
    if not url_path.startswith("files/"):
        return None
    rest = url_path[6:]
    parts = rest.split("/")
    root = Path(settings.storage_local_path)
    if len(parts) == 2:
        subdir, name = parts
        if subdir not in (SUBDIR_AVATARS, SUBDIR_QUESTIONS, SUBDIR_PDFS) or not _safe_filename(name):
            return None
        path = root / subdir / name
    elif len(parts) == 3:
        subdir, key, name = parts
        if subdir not in (SUBDIR_AVATARS, SUBDIR_QUESTIONS, SUBDIR_PDFS):
            return None
        if not _safe_storage_key(key) or not _safe_filename(name):
            return None
        path = root / key / subdir / name
    else:
        return None
    return path if path.is_file() else None


def get_local_url_legacy(relative_path: str) -> str:
    """兼容旧数据。"""
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
    """若 url 为本应用 /files/... 路径则删除文件，返回 (True, 释放字节数)；否则 (False, 0)。"""
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
