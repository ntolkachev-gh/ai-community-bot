#!/usr/bin/env python3
"""
Миграция для добавления поля image_url в таблицу events
"""

import sys
import os
from sqlalchemy import create_engine, text
from config import Config

def get_database_url():
    """Получение URL базы данных с правильной обработкой для Heroku"""
    database_url = Config.DATABASE_URL
    
    if not database_url or database_url == 'sqlite:///./test.db':
        # Локальная разработка - используем SQLite
        print("🔗 Локальная разработка: используем SQLite")
        return 'sqlite:///./test.db'
    
    # Heroku предоставляет URL в формате postgres://, но SQLAlchemy 1.4+ требует postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print("🔗 Heroku PostgreSQL: конвертирован postgres:// -> postgresql://")
    
    print(f"🔗 Подключение к базе данных: {database_url.split('@')[0]}@***")
    return database_url

def run_migration():
    """Запуск миграции для добавления поля image_url"""
    print("🚀 Запуск миграции для добавления поля image_url в таблицу events...")
    
    database_url = get_database_url()
    
    # Настройки engine в зависимости от типа БД
    if database_url.startswith('sqlite'):
        # SQLite настройки
        engine = create_engine(database_url, echo=True)
    else:
        # PostgreSQL настройки
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=True
        )
    
    try:
        with engine.connect() as connection:
            # Проверяем, существует ли уже поле image_url
            if database_url.startswith('sqlite'):
                # SQLite проверка
                result = connection.execute(text("PRAGMA table_info(events)"))
                columns = [row[1] for row in result.fetchall()]
                if 'image_url' in columns:
                    print("✅ Поле image_url уже существует в таблице events")
                    return
                
                # Добавляем поле для SQLite
                connection.execute(text("ALTER TABLE events ADD COLUMN image_url VARCHAR(500)"))
                connection.commit()
                
            else:
                # PostgreSQL проверка
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'events' AND column_name = 'image_url'
                """))
                
                if result.fetchone():
                    print("✅ Поле image_url уже существует в таблице events")
                    return
                
                # Добавляем поле для PostgreSQL
                connection.execute(text("ALTER TABLE events ADD COLUMN image_url VARCHAR(500)"))
                connection.commit()
            
            print("✅ Миграция успешно выполнена! Поле image_url добавлено в таблицу events")
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
