import time
import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import jwt

from app.config import settings
from app.database import get_db
from app.models import User
from app.deps import get_current_user_id
from app.schemas.auth import WechatLoginIn, UpdateProfileIn, LoginOut, UserOut, StorageOut, StorageIncreaseIn

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
        errcode = data.get("errcode", "")
        errmsg = data.get("errmsg", "微信登录失败")
        detail = f"{errmsg}" + (f" (errcode={errcode})" if errcode else "")
        if errcode == 40029:
            detail += "。请确保：1) 每次登录都用 wx.login() 新拿的 code；2) code 只用一次、不重复请求；3) code 在约 5 分钟内使用。"
        print(f"[auth/wechat/login] 微信登录失败: errcode={errcode}, errmsg={errmsg}, 完整响应: {data}")
        raise HTTPException(status_code=400, detail=detail)
    openid = data["openid"]
    unionid = data.get("unionid")

    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()
    if not user:
        try:
            user = User(openid=openid, unionid=unionid)
            db.add(user)
            await db.flush()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            result = await db.execute(select(User).where(User.openid == openid))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=500, detail="登录冲突，请重试")
    print(f"[auth/wechat/login] 收到 body: code=*** nickname={body.nickname!r} avatar_url={body.avatar_url!r}")
    if body.nickname is not None:
        user.nickname = body.nickname or None
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url or None
    await db.flush()
    await db.refresh(user)
    print(f"[auth/wechat/login] 用户 id={user.id} 保存后 avatar_url={user.avatar_url!r}")
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
async def get_me(
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
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
    print(f"[auth/me GET] user_id={user.id} nickname={user.nickname!r} avatar_url={user.avatar_url!r}")
    return UserOut(
        id=user.id,
        openid=user.openid,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UpdateProfileIn,
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户昵称、头像。"""
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
    if body.nickname is not None:
        user.nickname = body.nickname or None
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url or None
    await db.flush()
    await db.refresh(user)
    return UserOut(
        id=user.id,
        openid=user.openid,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


@router.get("/storage", response_model=StorageOut)
async def get_storage(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """查询当前用户存储配额与已用空间（字节）。"""
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return StorageOut(
        limit_bytes=user.storage_limit_bytes or 0,
        used_bytes=user.storage_used_bytes or 0,
    )


@router.post("/storage/increase", response_model=StorageOut)
async def increase_storage(
    body: StorageIncreaseIn,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """增加当前用户存储上限（如购买扩容）。生产环境应在支付成功回调或校验购买凭证后调用。"""
    if body.add_bytes <= 0:
        raise HTTPException(status_code=400, detail="add_bytes 须为正整数")
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    user.storage_limit_bytes = (user.storage_limit_bytes or 0) + body.add_bytes
    await db.flush()
    await db.refresh(user)
    return StorageOut(
        limit_bytes=user.storage_limit_bytes or 0,
        used_bytes=user.storage_used_bytes or 0,
    )
