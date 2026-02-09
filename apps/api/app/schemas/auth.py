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
    """用户存储配额与用量（字节）。"""
    limit_bytes: int
    used_bytes: int


class StorageIncreaseIn(BaseModel):
    """购买/增加存储空间（字节）。生产环境应由支付回调或凭证校验后再增加。"""
    add_bytes: int
