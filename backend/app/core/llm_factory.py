from langchain_core.language_models import BaseChatModel
from app.core.config import settings


def get_llm() -> BaseChatModel:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0,
        )
    elif provider == "gigachat":
        try:
            from langchain_community.chat_models.gigachat import GigaChat
            return GigaChat(
                credentials=settings.GIGACHAT_CREDENTIALS,
                scope=settings.GIGACHAT_SCOPE,
                model=settings.GIGACHAT_MODEL,
                verify_ssl_certs=False,
                temperature=0,
            )
        except ImportError:
            raise RuntimeError("gigachat package not installed. Run: pip install gigachat")
    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise RuntimeError("langchain-anthropic not installed. Run: pip install langchain-anthropic")
        return ChatAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL,
            temperature=0,
        )
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: openai, gigachat, anthropic, ollama")
