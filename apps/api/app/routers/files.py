"""
通过应用路由鉴权下发文件，不直接暴露 uploads 目录。
- /files/avatars/{filename}、/files/questions/{filename}：公开（链接为 UUID，难以猜测）
- /files/pdfs/{filename}：需登录
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


# 图片缓存：浏览器/H5 可缓存，减少重复请求（前端小程序侧另有本地文件缓存）
CACHE_CONTROL_IMAGE = "public, max-age=86400"

@router.get("/avatars/{filename}")
async def serve_avatar(filename: str):
    """头像文件，公开访问。"""
    path = get_file_path(f"/files/{SUBDIR_AVATARS}/{filename}")
    if not path:
        raise HTTPException(status_code=404, detail="文件不存在")
    resp = FileResponse(path, media_type="image/jpeg")
    resp.headers["Cache-Control"] = CACHE_CONTROL_IMAGE
    return resp


@router.get("/questions/{filename}")
async def serve_question_image(filename: str):
    """题目图片，公开访问（链接为 UUID，难以猜测，便于前端 img 直接引用）。"""
    path = get_file_path(f"/files/{SUBDIR_QUESTIONS}/{filename}")
    if not path:
        raise HTTPException(status_code=404, detail="文件不存在")
    resp = FileResponse(path, media_type="image/jpeg")
    resp.headers["Cache-Control"] = CACHE_CONTROL_IMAGE
    return resp


@router.get("/pdfs/{filename}")
async def serve_pdf(
    filename: str,
    _: int = Depends(require_auth),
):
    """PDF 文件，需登录后访问。"""
    path = get_file_path(f"/files/{SUBDIR_PDFS}/{filename}")
    if not path:
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(path, media_type="application/pdf")
