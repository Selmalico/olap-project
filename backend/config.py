from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    aws_region: str = "eu-central-1"
    s3_data_bucket: str = "olap-bi-data"
    s3_reports_bucket: str = "olap-bi-reports"
    ses_sender_email: str = ""
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096

    class Config:
        env_file = ".env"


settings = Settings()
