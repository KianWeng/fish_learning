import time
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas.auth import WechatLoginIn, LoginOut, UserOut

router = APIRouter()

WECHAT_CODE2SESSION = "https://api.weixin.qq.com/sns/jscode2session"


def _create_token(user_id: int) -> str:
    payload = {"sub": user_id, "exp": int(time.time()) + settings.jwt_expire_hours * 3600}
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def _decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except Exception:
        return None


@router.post("/wechat/login", response_model=LoginOut)
async def wechat_login(body: WechatLoginIn, db: AsyncSession = Depends(get_db)):
    """微信小程序登录：前端传 wx.login 的 code，后端换 openid 并创建/更新用户，返回 token。"""
    if not settings.wechat_appid or not settings.wechat_secret:
        raise HTTPException(status_code=503, detail="未配置微信小程序 appid/secret")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            WECHAT_CODE2SESSION,
            params={
                "appid": settings.wechat_appid,
                "secret": settings.wechat_secret,
                "js_code": body.code,
                "grant_type": "authorization_code",
            },
        )
    data = r.json()
    if "openid" not in data:
        raise HTTPException(status_code=400, detail=data.get("errmsg", "微信登录失败"))
    openid = data["openid"]
    unionid = data.get("unionid")

    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()
    if not user:
        user = User(openid=openid, unionid=unionid)
        db.add(user)
        await db.flush()
        await db.refresh(user)
    token = _create_token(user.id)
    return LoginOut(
        token=token,
        user=UserOut(
            id=user.id,
            openid=user.openid,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            created_at=user.created_at.isoformat() if user.created_at else "",
        ),
    )


@router.get("/me", response_model=UserOut)
async def get_me(authorization: str | None = None, db: AsyncSession = Depends(get_db)):
    """根据请求头 Authorization: Bearer <token> 返回当前用户信息。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:].strip()
    payload = _decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="登录已过期")
    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return UserOut(
        id=user.id,
        openid=user.openid,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )
