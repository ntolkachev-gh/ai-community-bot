import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Database - автоматическое определение типа БД
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
    
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
    
    @staticmethod
    def init_app(app):
        # Настройки для продакшна
        import logging
        
        if not app.debug:
            # Настройка логирования для Heroku
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('AI Community Bot startup')

class HerokuConfig(ProductionConfig):
    # Специальная конфигурация для Heroku
    LOG_TO_STDOUT = True
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Обработка Heroku proxy headers
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'default': DevelopmentConfig
}
