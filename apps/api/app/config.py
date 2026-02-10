from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mistake_book"
    storage_type: str = "local"
    storage_local_path: str = "./uploads"
    # 生产 HTTPS：反向代理后若仍为 http 则重定向到 https
    force_https: bool = False
    # 对外 API 基地址（可选，用于生成绝对 URL 时，如 https://api.example.com）
    api_base_url: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    # Coze 工作流（优先于 OpenAI）：鉴权 PAT、工作流 ID、图片参数名
    coze_api_key: str = ""
    coze_base_url: str = "https://api.coze.cn"
    coze_workflow_id: str = ""
    coze_image_parameter: str = "image"
    # 学习报告 Coze 工作流：输入为 JSON 字符串（见文档 COZE_REPORT_WORKFLOW.md）
    coze_report_workflow_id: str = ""
    coze_report_workflow_parameter: str = "input"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "mistake-book"
    # 微信小程序登录
    wechat_appid: str = ""
    wechat_secret: str = ""
    # 微信支付（商户号、APIv3 密钥、商户私钥与证书序列号、支付结果回调地址）
    wechat_mch_id: str = ""
    wechat_pay_api_v3_key: str = ""
    wechat_pay_private_key_path: str = ""
    wechat_pay_serial_no: str = ""
    wechat_pay_notify_url: str = ""
    # 积分与广告：每次观看激励视频奖励积分、每用户每日上限次数
    points_per_ad_reward: int = 10
    max_ad_rewards_per_day: int = 20
    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 720  # 30 天

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
