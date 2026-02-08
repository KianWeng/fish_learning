from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mistake_book"
    storage_type: str = "local"
    storage_local_path: str = "./uploads"
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

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
