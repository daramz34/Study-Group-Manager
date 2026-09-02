from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Setting(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    ALGORITHM:str

    APP_NAME: str = "STUDY GROUP MANAGER"
    VERSION: str = "1.0.0"

    GEMINI_API_KEY: str
    REDIS_URL: str



    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parent.parent / ".env")

settings = Setting()