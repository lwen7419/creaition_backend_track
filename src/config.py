from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Creaition Backend"
    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"
    task_list_cache_ttl_seconds: int = 30
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"
    chroma_persist_directory: str = "./chroma_data"
    chroma_collection_name: str = "tasks"


settings = Settings()
