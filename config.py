import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/ai_community_bot')
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # APScheduler
    SCHEDULER_API_ENABLED = True
    
    # Web interface
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('PORT', 5000))
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 