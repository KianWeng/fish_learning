from pydantic import Field, model_validator
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
    # 与 OPENAI_API_KEY 二选一：阿里百炼 DashScope API Key（写入后等价于 OPENAI_API_KEY）
    dashscope_api_key: str = Field(default="", validation_alias="DASHSCOPE_API_KEY")
    # 默认：阿里百炼 OpenAI 兼容接口 https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-by-calling-api
    openai_base_url: str = "https://coding.dashscope.aliyuncs.com/v1"
    # 识图（多模态）：百炼常用 qwen-vl-plus；OpenAI 可用 gpt-4o-mini；DeepSeek 用 deepseek-chat 等
    openai_vision_model: str = "kimi-k2.5"
    # 纯文本（学习报告、PDF 页解析等）：百炼常用 qwen-plus；OpenAI 可用 gpt-4o-mini
    openai_chat_model: str = "glm-5"
    # 识图回退到 DeepSeek/OpenAI 时的系统 prompt（可选）；也可用 OPENAI_QUESTION_SYSTEM_PROMPT_FILE 指定文件路径
    openai_question_system_prompt: str = ""
    openai_question_system_prompt_file: str = ""
    # 识图回退：豆包 Doubao（火山方舟 Ark），Coze 失败时使用
    ark_api_key: str = ""
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ark_vision_model: str = "doubao-seed-1-8-251228"
    # 识图供应商优先级（OPENAI_* 与 Coze 均配置时）：bailian=百炼 OpenAI 兼容先；coze=Coze 工作流先
    vision_image_priority: str = "bailian"
    # Coze 工作流：鉴权 PAT、工作流 ID、图片参数名、识图请求超时（秒）
    coze_api_key: str = ""
    coze_base_url: str = "https://api.coze.cn"
    coze_workflow_id: str = ""
    coze_image_parameter: str = "image"
    coze_workflow_timeout: int = 60  # 识图工作流 HTTP 超时，Coze 处理慢时可调大（如 180、240）
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

    @model_validator(mode="after")
    def _merge_dashscope_api_key(self) -> "Settings":
        if not (self.openai_api_key or "").strip() and (self.dashscope_api_key or "").strip():
            object.__setattr__(self, "openai_api_key", self.dashscope_api_key.strip())
        return self


settings = Settings()
