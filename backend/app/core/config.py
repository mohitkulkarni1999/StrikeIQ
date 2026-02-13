import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    LOG_LEVEL: str = "INFO"
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Load with fallback to empty string - SECURITY: No hardcoded credentials
    UPSTOX_API_KEY: str = os.getenv('UPSTOX_API_KEY', "")
    UPSTOX_API_SECRET: str = os.getenv('UPSTOX_API_SECRET', "")
    REDIRECT_URI: str = os.getenv('UPSTOX_REDIRECT_URI', "http://localhost:8000/api/v1/auth/upstox/callback")
    
    # Security settings
    SECRET_KEY: str = os.getenv('SECRET_KEY', "your-secret-key-change-in-production")
    
    # Frontend URL for OAuth initiation
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', "http://localhost:3000")
    
    # Database Settings
    DATABASE_URL: str = os.getenv('DATABASE_URL', "postgresql://strikeiq:strikeiq123@localhost:5432/strikeiq")
    REDIS_URL: str = os.getenv('REDIS_URL', "redis://localhost:6379")
    
    # Redis Settings
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    
    def __init__(self):
        # Additional initialization if needed, but class attributes cover defaults
        pass

settings = Settings()
