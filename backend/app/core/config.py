from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_name: str = "OpsPilot API"

    database_url: str

    frontend_origin: str = "http://localhost:3000"

    # Phase 2 and Phase 3 temporarily
    # still use Gemini.
    gemini_api_key: str

    gemini_model: str = (
        "gemini-2.5-flash-lite"
    )

    # Phase 4 agent loop uses Groq.
    groq_api_key: str

    groq_model: str = (
        "llama-3.3-70b-versatile"
    )

    langgraph_checkpoint_db_uri: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()