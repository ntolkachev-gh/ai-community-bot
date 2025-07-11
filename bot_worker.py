#!/usr/bin/env python3
"""
Telegram Bot Worker - отдельный процесс для бота
"""

import logging
import os
from database.models import init_db
from bot.telegram_bot import TelegramBot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Главная функция для запуска бота"""
    try:
        logger.info("Инициализация базы данных для бота...")
        init_db()
        
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            logger.error("BOT_TOKEN не найден в переменных окружения")
            return
            
        logger.info("Запуск Telegram бота...")
        bot = TelegramBot()
        
        # Запуск планировщика
        bot.scheduler.start()
        
        # Запуск бота (run_polling создает свой event loop)
        bot.app.run_polling()
        
    except Exception as e:
        logger.error(f"Критическая ошибка бота: {e}")
        raise

if __name__ == "__main__":
    main() 