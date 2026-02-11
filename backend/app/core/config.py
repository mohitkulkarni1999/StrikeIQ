import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    LOG_LEVEL: str = "INFO"
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Load with fallback to empty string, but preferably valid env vars should be present
    UPSTOX_API_KEY: str = os.getenv('UPSTOX_API_KEY', "53c878a9-3f5d-44f9-aa2d-2528d34a24cd")
    # Secret must come from env to avoid 401
    UPSTOX_API_SECRET: str = os.getenv('UPSTOX_API_SECRET', "your_api_secret_here")
    REDIRECT_URI: str = os.getenv('UPSTOX_REDIRECT_URI', "http://localhost:8000/api/v1/auth/upstox/callback")
    
    # Frontend URL for OAuth initiation
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', "http://localhost:3000")
    
    # Database Settings
    DATABASE_URL: str = os.getenv('DATABASE_URL', "postgresql://strikeiq:strikeiq123@localhost:5432/strikeiq")
    REDIS_URL: str = os.getenv('REDIS_URL', "redis://localhost:6379")
    
    def __init__(self):
        # Additional initialization if needed, but class attributes cover defaults
        pass

settings = Settings()
