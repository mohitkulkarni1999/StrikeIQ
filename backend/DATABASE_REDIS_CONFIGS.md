# STRIKEIQ PROJECT DATABASE & REDIS CONFIGURATIONS
# Actual configurations used in the project

# ==================== POSTGRESQL CONFIGURATION ====================

# Default Database URL (from app/core/config.py)
DATABASE_URL=postgresql://strikeiq:strikeiq123@localhost:5432/strikeiq

# Alternative Environment Variable Format
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=strikeiq
POSTGRES_USER=strikeiq
POSTGRES_PASSWORD=strikeiq123

# SQLAlchemy Configuration (from app/models/database.py)
SQLALCHEMY_DATABASE_URL=postgresql://strikeiq:strikeiq123@localhost:5432/strikeiq

# Database Engine Settings
# - Uses SQLAlchemy create_engine with default settings
# - No connection pooling configured (uses SQLAlchemy defaults)
# - No SSL settings (development environment)

# ==================== REDIS CONFIGURATION ====================

# Default Redis URL (from app/core/config.py)
REDIS_URL=redis://localhost:6379

# Individual Redis Settings (from app/core/config.py)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Redis Cache Service Configuration (from app/services/cache_service.py)
REDIS_CACHE_URL=redis://localhost:6379/0
REDIS_ENCODING=utf-8
REDIS_DECODE_RESPONSES=true

# Cache Service Settings
# - Uses redis.asyncio for async operations
# - Default TTL: 300 seconds (5 minutes)
# - JSON serialization for all cached values
# - Connection testing via ping() on initialization

# ==================== CURRENT .ENV FILE ====================

# Actual .env file contents (minimal configuration)
UPSTOX_API_KEY=53c878a9-3f5d-44f9-aa2d-2528d34a24cd
UPSTOX_API_SECRET=db083c9gux
UPSTOX_CLIENT_ID=53c878a9-3f5d-44f9-aa2d-2528d34a24cd
UPSTOX_REDIRECT_URI=http://localhost:8000/api/v1/auth/upstox/callback
LOG_LEVEL=INFO

# NOTE: Database and Redis URLs are NOT set in .env file
# Uses defaults from config.py:
# - DATABASE_URL=postgresql://strikeiq:strikeiq123@localhost:5432/strikeiq
# - REDIS_URL=redis://localhost:6379

# ==================== COMPLETE .ENV.example ====================

# Full configuration template (from .env.example)
UPSTOX_API_KEY=your_upstox_api_key_here
UPSTOX_API_SECRET=your_upstox_api_secret_here
UPSTOX_REDIRECT_URI=http://localhost:8000/api/v1/auth/upstox/callback
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
FRONTEND_URL=http://localhost:3000
DATABASE_URL=postgresql://username:password@localhost:5432/strikeiq
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
LOG_LEVEL=INFO

# ==================== USAGE IN CODE ====================

# Database Usage:
# - app/models/database.py: SQLAlchemy engine creation
# - All database operations use get_db() dependency
# - Connection string: settings.DATABASE_URL

# Redis Usage:
# - app/services/cache_service.py: Async Redis client
# - Cache TTL: 300 seconds default
# - JSON serialization for all values
# - Connection string: "redis://localhost:6379/0" (hardcoded)

# ==================== PRODUCTION RECOMMENDATIONS ====================

# Database Production Settings:
# - Use connection pooling
# - Enable SSL
# - Use environment-specific credentials
# - Set proper connection limits

# Redis Production Settings:
# - Use Redis password
# - Configure connection pooling
# - Use separate databases for different data types
# - Set appropriate eviction policies

# Security:
# - Move credentials to .env file
# - Use strong passwords
# - Enable SSL/TLS
# - Use environment-specific configurations
