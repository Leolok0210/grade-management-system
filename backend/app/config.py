from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://leo@localhost:5432/grade_management"

    # JWT
    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI Providers
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.llmhub.com.cn/v1"
    OPENAI_MODEL: str = "qwen3.5-flash"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    LOCAL_MODEL_URL: str = "http://localhost:11434"  # Ollama default
    LOCAL_MODEL_NAME: str = "qwen2.5:7b"

    # AI Router
    DEFAULT_PROVIDER: str = "openai"  # openai / anthropic / local

    # CORS
    CORS_ORIGINS: str = '["*"]'

    # App
    APP_NAME: str = "成績管理系統"
    APP_VERSION: str = "1.0.0"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()