from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Creaition Backend"
    database_url: str = "sqlite:///./app.db"


settings = Settings()
