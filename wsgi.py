#!/usr/bin/env python3
"""
WSGI entry point for Gunicorn - только веб-интерфейс
"""

import os
import logging
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

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 