# Location: src/app/core/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "contract-api"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    API_VERSION: str = "v1"
    DEBUG: bool = True
    
    # Neo4j Settings
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # FPDS Settings
    BASE_URL: str = "https://your-atom-feed-url/"
    FPDS_BATCH_SIZE: int = 100
    FPDS_RATE_LIMIT: float = 0.5
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()ws