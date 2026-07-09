from langchain_groq import ChatGroq

from app.core.config import settings


def get_ops_chat_model() -> ChatGroq:
    return ChatGroq(
        model=settings.groq_model,

        api_key=settings.groq_api_key,

        temperature=0.1,

        max_tokens=1200,

        timeout=60,

        max_retries=2,
    )