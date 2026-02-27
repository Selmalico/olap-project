"""
Configuration settings for the OLAP BI Platform backend.
Loads from environment variables with sensible defaults.
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Backend configuration loaded from environment variables."""

    # AWS S3 Configuration (for parquet data storage - optional)
    aws_region: str = "us-east-1"
    s3_data_bucket: str = "olap-data-dev"
    s3_reports_bucket: str = "olap-reports-dev"

    # API Configuration
    api_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # LLM Configuration
    openai_api_key: str = ""
    use_huggingface: bool = True
    huggingface_api_key: str = ""

    # Database
    duckdb_path: str = "data/olap.duckdb"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


# Global settings instance
settings = Settings()
