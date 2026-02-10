import secrets
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

import httpx
import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import get_db
from app.models import User, UserStorageAddon
from app.deps import get_current_user_id
from app.schemas.auth import (
    WechatLoginIn, UpdateProfileIn, LoginOut, UserOut,
    StorageOut, StorageIncreaseIn, StoragePurchaseIn, StorageOrderPaymentParamsOut,
    StorageRedeemIn,
)
from app.services.storage_quota import get_effective_storage_limit
from app.services.storage import (
    get_file_path,
    delete_file_by_url,
    save_avatar,
    user_storage_key,
)
from app.services.wechat_pay import create_jsapi_order, build_miniprogram_payment_params
from app.models import StorageOrder, PointsAdLog
from sqlalchemy import func

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
        avatar_url = (body.avatar_url or "").strip()
        # 若为登录临时目录 /files/avatars/login/xxx，迁移到用户个人目录
        path_from_url = urlparse(avatar_url).path if avatar_url.startswith("http") else avatar_url
        if "/files/avatars/login/" in path_from_url:
            local_path = get_file_path(path_from_url)
            if local_path and local_path.is_file():
                try:
                    content = local_path.read_bytes()
                    storage_key = user_storage_key(user.openid)
                    limit = await get_effective_storage_limit(db, user.id)
                    new_path, size = save_avatar(content, "avatar.jpg", storage_key)
                    if (user.storage_used_bytes or 0) + size <= limit:
                        user.avatar_url = new_path
                        user.storage_used_bytes = (user.storage_used_bytes or 0) + size
                        delete_file_by_url(path_from_url)
                    else:
                        user.avatar_url = avatar_url
                except Exception as e:
                    print(f"[auth/wechat/login] 迁移登录头像到用户目录失败: {e}")
                    user.avatar_url = avatar_url
            else:
                user.avatar_url = avatar_url
        else:
            user.avatar_url = avatar_url or None
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
    """查询当前用户有效存储配额、已用空间与积分（含未过期扩容包）。"""
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    limit = await get_effective_storage_limit(db, user_id)
    return StorageOut(
        limit_bytes=limit,
        used_bytes=user.storage_used_bytes or 0,
        points=user.points or 0,
    )


@router.post("/points/ad-reward", response_model=StorageOut)
async def ad_reward_points(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """观看激励视频广告完成后的奖励：增加积分，每用户每日有上限。"""
    reward = settings.points_per_ad_reward
    if reward <= 0:
        raise HTTPException(status_code=503, detail="未配置广告奖励积分")
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    start_of_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count_result = await db.execute(
        select(func.count(PointsAdLog.id)).where(
            PointsAdLog.user_id == user_id,
            PointsAdLog.created_at >= start_of_today,
        )
    )
    today_count = count_result.scalar() or 0
    if today_count >= settings.max_ad_rewards_per_day:
        raise HTTPException(
            status_code=429,
            detail=f"今日观看次数已达上限（{settings.max_ad_rewards_per_day} 次），明天再来吧",
        )

    user.points = (user.points or 0) + reward
    db.add(PointsAdLog(user_id=user_id))
    await db.flush()
    await db.refresh(user)
    limit = await get_effective_storage_limit(db, user_id)
    return StorageOut(
        limit_bytes=limit,
        used_bytes=user.storage_used_bytes or 0,
        points=user.points or 0,
    )


# 扩容包字节数 -> 兑换所需积分（与前端套餐一致）
STORAGE_PACKAGE_POINTS = {
    50 * 1024 * 1024: 500,   # 50MB
    100 * 1024 * 1024: 1000, # 100MB
    200 * 1024 * 1024: 2000, # 200MB
}

# 扩容包字节数 -> 金额（分），与前端套餐一致（微信支付用，个人小程序可不用）
STORAGE_PACKAGE_AMOUNT_FEN = {
    50 * 1024 * 1024: 600,   # 50MB -> 6 元
    100 * 1024 * 1024: 1000, # 100MB -> 10 元
    200 * 1024 * 1024: 1800, # 200MB -> 18 元
}


@router.post("/storage/redeem", response_model=StorageOut)
async def redeem_storage(
    body: StorageRedeemIn,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """使用积分兑换存储扩容包，有效期 1 年。"""
    if body.add_bytes <= 0:
        raise HTTPException(status_code=400, detail="add_bytes 须为正整数")
    cost = STORAGE_PACKAGE_POINTS.get(body.add_bytes)
    if cost is None:
        raise HTTPException(status_code=400, detail="不支持的扩容套餐，请选择 50MB/100MB/200MB")
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    current = user.points or 0
    if current < cost:
        raise HTTPException(status_code=400, detail=f"积分不足，当前 {current}，需要 {cost}")

    user.points = current - cost
    expires_at = datetime.utcnow() + timedelta(days=365)
    addon = UserStorageAddon(user_id=user_id, add_bytes=body.add_bytes, expires_at=expires_at)
    db.add(addon)
    await db.flush()
    await db.refresh(user)
    limit = await get_effective_storage_limit(db, user_id)
    return StorageOut(
        limit_bytes=limit,
        used_bytes=user.storage_used_bytes or 0,
        points=user.points or 0,
    )


@router.post("/storage/create-order", response_model=StorageOrderPaymentParamsOut)
async def create_storage_order(
    body: StoragePurchaseIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """创建存储扩容订单并返回小程序调起微信支付所需参数。"""
    if body.add_bytes <= 0:
        raise HTTPException(status_code=400, detail="add_bytes 须为正整数")
    amount_fen = STORAGE_PACKAGE_AMOUNT_FEN.get(body.add_bytes)
    if amount_fen is None:
        raise HTTPException(status_code=400, detail="不支持的扩容套餐，请选择 50MB/100MB/200MB")
    if not all([
        settings.wechat_appid,
        settings.wechat_mch_id,
        settings.wechat_pay_api_v3_key,
        settings.wechat_pay_private_key_path,
        settings.wechat_pay_serial_no,
        settings.wechat_pay_notify_url,
    ]):
        raise HTTPException(status_code=503, detail="未配置微信支付参数")

    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user or not user.openid:
        raise HTTPException(status_code=401, detail="用户不存在或无 openid")

    out_trade_no = f"SO{int(datetime.utcnow().timestamp() * 1000)}{secrets.token_hex(4)}"[:32]
    order = StorageOrder(
        out_trade_no=out_trade_no,
        user_id=user_id,
        add_bytes=body.add_bytes,
        amount_fen=amount_fen,
        status="pending",
    )
    db.add(order)
    await db.flush()

    client_ip = request.client.host if request.client else "127.0.0.1"
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

    try:
        prepay_id = create_jsapi_order(
            appid=settings.wechat_appid,
            mch_id=settings.wechat_mch_id,
            out_trade_no=out_trade_no,
            description="存储扩容包",
            amount_fen=amount_fen,
            openid=user.openid,
            notify_url=settings.wechat_pay_notify_url,
            private_key_path=settings.wechat_pay_private_key_path,
            serial_no=settings.wechat_pay_serial_no,
            client_ip=client_ip,
        )
    except Exception as e:
        order.status = "failed"
        await db.flush()
        raise HTTPException(status_code=502, detail=f"微信下单失败: {e!s}")

    params = build_miniprogram_payment_params(
        appid=settings.wechat_appid,
        prepay_id=prepay_id,
        private_key_path=settings.wechat_pay_private_key_path,
    )
    params["order_no"] = out_trade_no
    return StorageOrderPaymentParamsOut(**params)


@router.post("/storage/purchase", response_model=StorageOut)
async def purchase_storage(
    body: StoragePurchaseIn,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """购买扩容包，有效期 1 年。生产环境应在支付成功回调后调用。"""
    if body.add_bytes <= 0:
        raise HTTPException(status_code=400, detail="add_bytes 须为正整数")
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    expires_at = datetime.utcnow() + timedelta(days=365)
    addon = UserStorageAddon(user_id=user_id, add_bytes=body.add_bytes, expires_at=expires_at)
    db.add(addon)
    await db.flush()
    limit = await get_effective_storage_limit(db, user_id)
    return StorageOut(limit_bytes=limit, used_bytes=user.storage_used_bytes or 0)


@router.post("/storage/increase", response_model=StorageOut)
async def increase_storage(
    body: StorageIncreaseIn,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """永久增加当前用户存储上限（如管理端或支付回调）。"""
    if body.add_bytes <= 0:
        raise HTTPException(status_code=400, detail="add_bytes 须为正整数")
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    user.storage_limit_bytes = (user.storage_limit_bytes or 0) + body.add_bytes
    await db.flush()
    await db.refresh(user)
    limit = await get_effective_storage_limit(db, user_id)
    return StorageOut(limit_bytes=limit, used_bytes=user.storage_used_bytes or 0)
