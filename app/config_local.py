import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database SQLite para teste local
    DATABASE_URL = 'sqlite+aiosqlite:///telegram_bots.db'
    DATABASE_SYNC_URL = 'sqlite:///telegram_bots.db'
    
    # Redis desabilitado para teste local
    REDIS_URL = None
    CACHE_TTL = 300
    
    # Server
    SERVER_URL = 'http://localhost:8000'
    SECRET_KEY = 'super-secret-key-123456'
    DEBUG = True
    
    # Telegram
    TELEGRAM_API_URL = 'https://api.telegram.org'
    WEBHOOK_PATH = '/webhook'
    
    # Rate Limiting
    RATE_LIMIT_PER_BOT = 30
    
    # Pool Settings
    DB_POOL_SIZE = 5
    DB_MAX_OVERFLOW = 10
    REDIS_MAX_CONNECTIONS = 50
    HTTP_POOL_SIZE = 100

settings = Settings()