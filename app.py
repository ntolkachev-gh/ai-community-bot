#!/usr/bin/env python3
"""
AI Community Bot - Telegram Bot for Event Management
"""

import os
import logging
from threading import Thread
from config import config
from database.models import init_db
from bot.telegram_bot import TelegramBot
from web.app import create_app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_bot():
    """Запуск Telegram бота"""
    try:
        import asyncio
        bot = TelegramBot()
        
        # Создаем новый event loop для потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем бота
        bot.scheduler.start()
        bot.app.run_polling()
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

def run_web():
    """Запуск веб-интерфейса"""
    try:
        app = create_app()
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Ошибка запуска веб-интерфейса: {e}")

def main():
    """Главная функция"""
    logger.info("Инициализация базы данных...")
    init_db()
    
    logger.info("Запуск AI Community Bot...")
    
    # Запуск бота в отдельном потоке
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запуск веб-интерфейса в основном потоке
    run_web()

if __name__ == "__main__":
    main() 