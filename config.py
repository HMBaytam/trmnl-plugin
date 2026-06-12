from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str  # reads env var MONGODB_URI (case-insensitive)
    mongodb: str  # reads env var MONGODB -> the database name

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # validates on import; raises if a var is missing
