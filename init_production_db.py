#!/usr/bin/env python3
"""
Скрипт для инициализации продакшн базы данных на Heroku
"""

import os
import sys
from datetime import datetime, timedelta

def create_production_data():
    """Создание начальных данных для продакшна"""
    print("🚀 Инициализация продакшн базы данных...")
    
    # На Heroku DATABASE_URL должен быть установлен автоматически
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("⚠️  DATABASE_URL не найден - это нормально для локальной разработки")
        print("🔗 Используем локальную SQLite базу данных")
    else:
        print(f"🔗 Подключение к Heroku PostgreSQL: {database_url.split('@')[0] if '@' in database_url else database_url[:20]}@***")
    
    try:
        # Импортируем модели
        from database.models import User, Event, Registration, SessionLocal, init_db
        
        # Инициализация таблиц
        init_db()
        
        # Запускаем миграцию для добавления новых полей
        print("🔄 Запуск миграции базы данных...")
        from migrate_database import migrate_database
        migration_success = migrate_database()
        
        if not migration_success:
            print("❌ Ошибка миграции базы данных")
            sys.exit(1)
        
        db = SessionLocal()
        
        try:
            # Проверяем, есть ли уже данные
            user_count = db.query(User).count()
            event_count = db.query(Event).count()
            
            if event_count > 0:
                print(f"ℹ️  База данных уже содержит {event_count} мероприятий и {user_count} пользователей")
                print("✅ Инициализация завершена - данные уже существуют")
                return
            
            print("📝 Создание начальных мероприятий для продакшн...")
            
            # Создаем несколько демонстрационных мероприятий
            events = [
                Event(
                    title="🎉 Добро пожаловать в AI Community!",
                    description="Вводное мероприятие для новых участников сообщества. Узнайте о наших целях, планах и возможностях для развития в области искусственного интеллекта.",
                    event_datetime=datetime.now() + timedelta(days=7),
                    webinar_link="https://meet.google.com/welcome-ai-community",
                    max_participants=100
                ),
                Event(
                    title="🤖 Машинное обучение для начинающих",
                    description="Базовые концепции ML, популярные алгоритмы и практические примеры. Идеально подходит для новичков в области искусственного интеллекта.",
                    event_datetime=datetime.now() + timedelta(days=14),
                    webinar_link="https://zoom.us/j/ml-beginners-course",
                    max_participants=50
                ),
                Event(
                    title="🧠 Нейронные сети и Deep Learning",
                    description="Глубокое погружение в архитектуры нейронных сетей, CNN, RNN и трансформеры. Практические задачи и современные подходы.",
                    event_datetime=datetime.now() + timedelta(days=21),
                    webinar_link="https://teams.microsoft.com/neural-networks-workshop",
                    max_participants=30
                ),
                Event(
                    title="💬 ChatGPT и большие языковые модели",
                    description="Изучаем принципы работы LLM, prompt engineering и практическое применение ChatGPT в различных задачах.",
                    event_datetime=datetime.now() + timedelta(days=28),
                    webinar_link="https://discord.gg/chatgpt-workshop",
                    max_participants=75
                ),
                Event(
                    title="👁️ Компьютерное зрение и обработка изображений",
                    description="Современные методы анализа изображений, детекция объектов, сегментация и генерация изображений с помощью ИИ.",
                    event_datetime=datetime.now() + timedelta(days=35),
                    webinar_link="https://meet.google.com/computer-vision-ai",
                    max_participants=40
                )
            ]
            
            for event in events:
                db.add(event)
            
            db.commit()
            print(f"✅ Создано {len(events)} начальных мероприятий")
            
            # Выводим статистику
            final_user_count = db.query(User).count()
            final_event_count = db.query(Event).count()
            final_reg_count = db.query(Registration).count()
            
            print("\n📊 Финальная статистика базы данных:")
            print(f"👥 Пользователей: {final_user_count}")
            print(f"📅 Мероприятий: {final_event_count}")
            print(f"📋 Регистраций: {final_reg_count}")
            
            if database_url and 'postgres' in database_url:
                print("\n🎉 Heroku PostgreSQL база данных готова к работе!")
            else:
                print("\n🎉 Локальная база данных готова к работе!")
                
            print("📱 Пользователи могут начать регистрироваться через Telegram бота")
            
        except Exception as e:
            print(f"❌ Ошибка при создании данных: {e}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except ImportError as e:
        print(f"❌ Ошибка импорта модулей: {e}")
        print("Убедитесь, что все зависимости установлены")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Критическая ошибка при инициализации: {e}")
        print(f"Тип ошибки: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_production_data()
