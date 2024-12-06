from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str
    CORS_ORIGINS: List[str] = ["*"]
    DATABASE_URL: str
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
