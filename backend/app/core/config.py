from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # LLM Provider: "openai" | "gigachat" | "anthropic" | "ollama"
    LLM_PROVIDER: str = "openai"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"

    # GigaChat
    GIGACHAT_CREDENTIALS: Optional[str] = None  # base64 client_id:secret
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"
    GIGACHAT_MODEL: str = "GigaChat-Pro"

    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
