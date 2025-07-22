#!/usr/bin/env python3
"""
Скрипт для миграции базы данных
Добавляет новые поля в таблицу users для расширенной регистрации
"""

import os
import sys
from sqlalchemy import text
from database.models import get_database_url, engine

def migrate_database():
    """Миграция базы данных"""
    print("🔄 Начинаем миграцию базы данных...")
    
    try:
        # Получаем URL базы данных
        database_url = get_database_url()
        print(f"📋 Подключение к: {database_url.split('@')[0]}@***")
        
        # Проверяем, существует ли таблица users
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                print("❌ Таблица users не найдена. Создайте базу данных заново.")
                return False
            
            # Проверяем, существуют ли уже новые поля
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            
            new_columns = [
                ('full_name', 'VARCHAR(200)'),
                ('company', 'VARCHAR(200)'),
                ('role', 'VARCHAR(200)'),
                ('ai_experience', 'VARCHAR(100)'),
                ('is_profile_complete', 'INTEGER DEFAULT 0')
            ]
            
            added_columns = []
            for column_name, column_type in new_columns:
                if column_name not in columns:
                    print(f"➕ Добавляем колонку: {column_name}")
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                    added_columns.append(column_name)
                else:
                    print(f"✅ Колонка {column_name} уже существует")
            
            # Обновляем существующих пользователей
            if added_columns:
                print("🔄 Обновляем существующих пользователей...")
                
                # Устанавливаем is_profile_complete = 0 для всех существующих пользователей
                conn.execute(text("UPDATE users SET is_profile_complete = 0 WHERE is_profile_complete IS NULL"))
                
                # Устанавливаем full_name для пользователей, у которых его нет
                conn.execute(text("""
                    UPDATE users 
                    SET full_name = CASE 
                        WHEN first_name IS NOT NULL AND last_name IS NOT NULL 
                        THEN first_name || ' ' || last_name
                        WHEN first_name IS NOT NULL 
                        THEN first_name
                        ELSE NULL
                    END
                    WHERE full_name IS NULL
                """))
                
                conn.commit()
                print(f"✅ Добавлено колонок: {len(added_columns)}")
                print("✅ Миграция завершена успешно!")
            else:
                print("✅ Все необходимые колонки уже существуют")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1) 