#!/usr/bin/env python3
"""
Скрипт для запуска миграции на Heroku
Используется для обновления существующих баз данных
"""

import os
import sys

def main():
    """Основная функция миграции"""
    print("🚀 Запуск миграции на Heroku...")
    
    try:
        # Проверяем переменные окружения
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL не найден")
            sys.exit(1)
        
        print(f"🔗 Подключение к: {database_url.split('@')[0]}@***")
        
        # Импортируем и запускаем миграцию
        from migrate_database import migrate_database
        
        success = migrate_database()
        
        if success:
            print("✅ Миграция успешно завершена!")
            sys.exit(0)
        else:
            print("❌ Ошибка миграции")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 