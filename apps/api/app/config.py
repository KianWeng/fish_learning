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
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "mistake-book"
    # 微信小程序登录
    wechat_appid: str = ""
    wechat_secret: str = ""
    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 720  # 30 天

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
