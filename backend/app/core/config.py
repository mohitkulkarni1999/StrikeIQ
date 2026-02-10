from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    UPSTOX_API_KEY: str = "53c878a9-3f5d-44f9-aa2d-2528d34a24cd"
    UPSTOX_API_SECRET: str = "your_api_secret_here"
    REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/upstox/callback"
    
    class Config:
        env_file = ".env"

settings = Settings()
