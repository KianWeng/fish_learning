"""公共依赖：从 JWT 解析当前用户 id，用于需要登录的接口。"""
from fastapi import Header, HTTPException
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Subject


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except Exception:
        return None


async def get_current_user_id(authorization: str | None = Header(None, alias="Authorization")) -> int:
    """要求请求头带 Authorization: Bearer <token>，返回当前用户 id，否则 401。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization[7:].strip()
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="登录已过期")
    return int(payload["sub"])


async def require_subject_owner(
    subject_id: int,
    user_id: int,
    db: AsyncSession,
) -> Subject:
    """校验 subject 属于当前用户，否则 404。返回该 Subject。"""
    r = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == user_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="科目不存在")
    return s


async def require_subject_owner_for_update(
    subject_id: int,
    user_id: int,
    db: AsyncSession,
) -> Subject:
    """校验 subject 属于当前用户并加行锁（FOR UPDATE），用于与删除科目互斥。"""
    r = await db.execute(
        select(Subject).where(Subject.id == subject_id, Subject.user_id == user_id).with_for_update()
    )
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="科目不存在")
    return s
