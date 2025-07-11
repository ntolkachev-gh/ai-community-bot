#!/usr/bin/env python3
"""
AI Community Bot - только веб-интерфейс для локального тестирования
"""

import os
import logging
from config import config
from database.models import init_db
from web.app import create_app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Главная функция для запуска только веб-интерфейса"""
    logger.info("Инициализация базы данных...")
    init_db()
    
    logger.info("Запуск веб-интерфейса AI Community Bot...")
    
    # Создаем и запускаем только веб-приложение
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n🎉 Веб-интерфейс запущен!")
    print(f"🌐 Откройте в браузере: http://localhost:{port}")
    print(f"📊 Дашборд: http://localhost:{port}/")
    print(f"👥 Пользователи: http://localhost:{port}/users")
    print(f"📅 Мероприятия: http://localhost:{port}/events")
    print(f"📋 Регистрации: http://localhost:{port}/registrations")
    print(f"\n🛑 Для остановки нажмите Ctrl+C")
    
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    main() 