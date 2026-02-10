"""用户存储配额：基础容量 + 未过期扩容包。"""
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserStorageAddon


def _utc_now() -> datetime:
    return datetime.utcnow()


async def get_effective_storage_limit(db: AsyncSession, user_id: int) -> int:
    """返回用户当前有效存储上限（字节）= 基础容量 + 所有未过期扩容包之和。"""
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        return 0
    base = user.storage_limit_bytes or 0
    now = _utc_now()
    r2 = await db.execute(
        select(func.coalesce(func.sum(UserStorageAddon.add_bytes), 0)).where(
            UserStorageAddon.user_id == user_id,
            UserStorageAddon.expires_at > now,
        )
    )
    addon_sum = r2.scalar() or 0
    return int(base + addon_sum)
