#!/usr/bin/env python3
"""
WSGI entry point for Gunicorn
"""

import os
import logging
import threading
import asyncio
from database.models import init_db
from web.app import create_app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
logger.info("Инициализация базы данных...")
init_db()

# Создание приложения
logger.info("Создание Flask приложения...")
app = create_app()

def start_bot():
    """Запуск бота в отдельном потоке"""
    try:
        from bot.telegram_bot import TelegramBot
        
        # Создаем новый event loop для потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("Запуск Telegram бота...")
        bot = TelegramBot()
        bot.scheduler.start()
        
        # Запускаем бота
        bot.app.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

# Запуск бота в отдельном потоке только если есть BOT_TOKEN
if os.getenv('BOT_TOKEN'):
    logger.info("Запуск бота в фоновом режиме...")
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
else:
    logger.warning("BOT_TOKEN не найден, бот не запущен")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 