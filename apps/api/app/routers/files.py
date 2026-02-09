"""
通过应用路由鉴权下发文件。路径支持按用户分目录：/files/avatars/<user_id>/<filename> 或旧格式 /files/avatars/<filename>。
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.services.storage import get_file_path, SUBDIR_AVATARS, SUBDIR_QUESTIONS, SUBDIR_PDFS

router = APIRouter()


def _decode_token(token: str) -> dict | None:
    try:
        import jwt
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except Exception:
        return None


def require_auth(authorization: str | None = Header(None, alias="Authorization")) -> int:
    """要求 Bearer token 有效，返回 user_id。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    payload = _decode_token(authorization[7:].strip())
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="登录已过期")
    return payload["sub"]


CACHE_CONTROL_IMAGE = "public, max-age=86400"


@router.get("/avatars/{path:path}")
async def serve_avatar(path: str):
    """头像：path 为 <user_id>/<filename> 或旧格式 <filename>。"""
    full_url = f"/files/{SUBDIR_AVATARS}/{path}"
    p = get_file_path(full_url)
    if not p:
        raise HTTPException(status_code=404, detail="文件不存在")
    resp = FileResponse(p, media_type="image/jpeg")
    resp.headers["Cache-Control"] = CACHE_CONTROL_IMAGE
    return resp


@router.get("/questions/{path:path}")
async def serve_question_image(path: str):
    """题目图：path 为 <user_id>/<filename> 或旧格式 <filename>。"""
    full_url = f"/files/{SUBDIR_QUESTIONS}/{path}"
    p = get_file_path(full_url)
    if not p:
        raise HTTPException(status_code=404, detail="文件不存在")
    resp = FileResponse(p, media_type="image/jpeg")
    resp.headers["Cache-Control"] = CACHE_CONTROL_IMAGE
    return resp


@router.get("/pdfs/{path:path}")
async def serve_pdf(
    path: str,
    _: int = Depends(require_auth),
):
    """PDF：path 为 <user_id>/<filename> 或旧格式 <filename>，需登录。"""
    full_url = f"/files/{SUBDIR_PDFS}/{path}"
    p = get_file_path(full_url)
    if not p:
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(p, media_type="application/pdf")
