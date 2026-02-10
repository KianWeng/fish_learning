"""支付回调：微信支付异步通知（无需登录）。"""
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import StorageOrder, UserStorageAddon
from app.services.wechat_pay import decrypt_notify_resource

router = APIRouter()


@router.post("/wechat/notify")
async def wechat_pay_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """
    微信支付支付成功回调。验签可选（需平台证书）；此处仅解密并处理，生产建议验签。
    处理逻辑：解密 resource -> 取 out_trade_no、trade_state -> 已支付则幂等返回 200；
    未支付则更新订单、创建扩容包（1 年有效），再返回 200。
    """
    body = await request.body()
    try:
        data = json.loads(body.decode("utf-8"))
    except Exception:
        return Response(content='{"code":"FAIL","message":"无效报文"}', status_code=400, media_type="application/json")

    if data.get("event_type") != "TRANSACTION.SUCCESS":
        return Response(status_code=200)

    resource = data.get("resource") or {}
    ciphertext = resource.get("ciphertext")
    nonce = resource.get("nonce", "")
    associated_data = resource.get("associated_data", "")
    if not ciphertext or not settings.wechat_pay_api_v3_key:
        return Response(content='{"code":"FAIL","message":"缺少密文或APIv3密钥"}', status_code=400, media_type="application/json")

    try:
        decrypted = decrypt_notify_resource(
            settings.wechat_pay_api_v3_key,
            ciphertext,
            nonce,
            associated_data,
        )
    except Exception as e:
        return Response(content='{"code":"FAIL","message":"解密失败"}', status_code=400, media_type="application/json")

    out_trade_no = decrypted.get("out_trade_no")
    trade_state = decrypted.get("trade_state")
    if trade_state != "SUCCESS" or not out_trade_no:
        return Response(status_code=200)

    result = await db.execute(select(StorageOrder).where(StorageOrder.out_trade_no == out_trade_no))
    order = result.scalar_one_or_none()
    if not order:
        return Response(status_code=200)

    if order.status == "paid":
        return Response(status_code=200)

    order.status = "paid"
    order.paid_at = datetime.utcnow()
    expires_at = datetime.utcnow() + timedelta(days=365)
    addon = UserStorageAddon(user_id=order.user_id, add_bytes=order.add_bytes, expires_at=expires_at)
    db.add(addon)
    await db.commit()
    return Response(status_code=200)
