"""微信支付 APIv3：小程序 JSAPI 下单与支付回调解密。"""
import base64
import json
import os
import time
import secrets
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend


def _load_private_key(key_path: str):
    path = Path(key_path)
    if not path.is_file():
        raise FileNotFoundError(f"微信支付商户私钥文件不存在: {key_path}")
    data = path.read_bytes()
    return serialization.load_pem_private_key(data, password=None, backend=default_backend())


def _sign_message(private_key, message: str) -> str:
    signature = private_key.sign(
        message.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def _build_v3_authorization(
    method: str,
    url_path: str,
    body: str,
    mch_id: str,
    serial_no: str,
    private_key,
) -> tuple[str, str, str]:
    """构造 V3 请求的 Authorization 头。返回 (authorization, timestamp, nonce_str)。"""
    timestamp = str(int(time.time()))
    nonce_str = secrets.token_hex(16)
    message = f"{method}\n{url_path}\n{timestamp}\n{nonce_str}\n{body}\n"
    signature = _sign_message(private_key, message)
    auth = (
        f'WECHATPAY2-SHA256-RSA2048 mchid="{mch_id}",nonce_str="{nonce_str}",'
        f'serial_no="{serial_no}",timestamp="{timestamp}",signature="{signature}"'
    )
    return auth, timestamp, nonce_str


def create_jsapi_order(
    *,
    appid: str,
    mch_id: str,
    out_trade_no: str,
    description: str,
    amount_fen: int,
    openid: str,
    notify_url: str,
    private_key_path: str,
    serial_no: str,
    client_ip: str = "127.0.0.1",
) -> str:
    """
    调用微信支付 V3 JSAPI 下单，返回 prepay_id。
    金额单位：分。
    """
    url_path = "/v3/pay/transactions/jsapi"
    body = json.dumps({
        "appid": appid,
        "mchid": mch_id,
        "description": description,
        "out_trade_no": out_trade_no,
        "notify_url": notify_url,
        "amount": {"total": amount_fen, "currency": "CNY"},
        "payer": {"openid": openid},
        "scene_info": {"payer_client_ip": client_ip},
    }, ensure_ascii=False)

    private_key = _load_private_key(private_key_path)
    auth, _, _ = _build_v3_authorization("POST", url_path, body, mch_id, serial_no, private_key)

    import httpx
    resp = httpx.post(
        "https://api.mch.weixin.qq.com" + url_path,
        content=body.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": auth,
        },
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    if "prepay_id" not in data:
        raise ValueError(f"微信支付下单响应缺少 prepay_id: {data}")
    return data["prepay_id"]


def build_miniprogram_payment_params(
    appid: str,
    prepay_id: str,
    private_key_path: str,
) -> dict:
    """
    根据 prepay_id 生成小程序 wx.requestPayment 所需参数。
    返回: timeStamp, nonceStr, package, signType, paySign
    """
    private_key = _load_private_key(private_key_path)
    time_stamp = str(int(time.time()))
    nonce_str = secrets.token_hex(16)
    package = f"prepay_id={prepay_id}"
    # 调起支付签名串：appId\n时间戳\n随机串\npackage\n
    sign_message = f"{appid}\n{time_stamp}\n{nonce_str}\n{package}\n"
    pay_sign = _sign_message(private_key, sign_message)
    return {
        "timeStamp": time_stamp,
        "nonceStr": nonce_str,
        "package": package,
        "signType": "RSA",
        "paySign": pay_sign,
    }


def decrypt_notify_resource(
    api_v3_key: str,
    ciphertext_b64: str,
    nonce: str,
    associated_data: str,
) -> dict:
    """
    使用 APIv3 密钥解密回调中的 resource（AEAD_AES_256_GCM）。
    associated_data 通常为 "transaction" 或空。
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = api_v3_key.encode("utf-8")
    if len(key) != 32:
        raise ValueError("APIv3 密钥必须为 32 字节")
    ciphertext = base64.b64decode(ciphertext_b64)
    nonce_b = nonce.encode("utf-8")
    aad = associated_data.encode("utf-8") if associated_data else b""
    aesgcm = AESGCM(key)
    plain = aesgcm.decrypt(nonce_b, ciphertext, aad)
    return json.loads(plain.decode("utf-8"))
