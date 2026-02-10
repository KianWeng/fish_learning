from pydantic import BaseModel


class WechatLoginIn(BaseModel):
    code: str
    nickname: str | None = None
    avatar_url: str | None = None


class UpdateProfileIn(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None


class UserOut(BaseModel):
    id: int
    openid: str  # 前端一般不展示，仅调试用；可改为不返回
    nickname: str | None
    avatar_url: str | None
    created_at: str

    class Config:
        from_attributes = True


class LoginOut(BaseModel):
    token: str
    user: UserOut


class StorageOut(BaseModel):
    """用户存储配额与用量（字节），以及当前积分（用于扩容页）。"""
    limit_bytes: int
    used_bytes: int
    points: int = 0


class StorageIncreaseIn(BaseModel):
    """永久增加存储空间（字节）。一般由支付回调或管理端调用。"""
    add_bytes: int


class StoragePurchaseIn(BaseModel):
    """购买扩容包（字节），有效期 1 年。"""
    add_bytes: int


class StorageRedeemIn(BaseModel):
    """使用积分兑换扩容包（字节），有效期 1 年。"""
    add_bytes: int


class StorageOrderPaymentParamsOut(BaseModel):
    """小程序调起微信支付所需参数。"""
    timeStamp: str
    nonceStr: str
    package: str
    signType: str
    paySign: str
    order_no: str
