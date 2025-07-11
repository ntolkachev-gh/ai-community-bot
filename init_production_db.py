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
    
    # Проверяем наличие DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Переменная DATABASE_URL не найдена")
        sys.exit(1)
    
    print(f"🔗 Подключение к базе данных: {database_url.split('@')[0] if '@' in database_url else 'SQLite'}@***")
    
    try:
        # Импортируем модели после проверки URL
        from database.models import User, Event, Registration, SessionLocal, init_db
        
        # Инициализация таблиц
        init_db()
        
        db = SessionLocal()
        
        try:
            # Проверяем, есть ли уже данные
            user_count = db.query(User).count()
            event_count = db.query(Event).count()
            
            if user_count > 0 or event_count > 0:
                print(f"ℹ️  База данных уже содержит данные (пользователей: {user_count}, мероприятий: {event_count})")
                return
            
            print("📝 Создание начальных мероприятий...")
            
            # Создаем несколько демонстрационных мероприятий
            events = [
                Event(
                    title="Добро пожаловать в AI Community! 🎉",
                    description="Вводное мероприятие для новых участников сообщества. Узнайте о наших целях, планах и возможностях для развития в области искусственного интеллекта.",
                    event_datetime=datetime.now() + timedelta(days=7),
                    webinar_link="https://meet.google.com/welcome-ai-community",
                    max_participants=100
                ),
                Event(
                    title="Машинное обучение для начинающих 🤖",
                    description="Базовые концепции ML, популярные алгоритмы и практические примеры. Идеально подходит для новичков в области искусственного интеллекта.",
                    event_datetime=datetime.now() + timedelta(days=14),
                    webinar_link="https://zoom.us/j/ml-beginners-course",
                    max_participants=50
                ),
                Event(
                    title="Нейронные сети и Deep Learning 🧠",
                    description="Глубокое погружение в архитектуры нейронных сетей, CNN, RNN и трансформеры. Практические задачи и современные подходы.",
                    event_datetime=datetime.now() + timedelta(days=21),
                    webinar_link="https://teams.microsoft.com/neural-networks-workshop",
                    max_participants=30
                ),
                Event(
                    title="ChatGPT и большие языковые модели 💬",
                    description="Изучаем принципы работы LLM, prompt engineering и практическое применение ChatGPT в различных задачах.",
                    event_datetime=datetime.now() + timedelta(days=28),
                    webinar_link="https://discord.gg/chatgpt-workshop",
                    max_participants=75
                ),
                Event(
                    title="Компьютерное зрение и обработка изображений 👁️",
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
            print("\n📊 Статистика базы данных:")
            print(f"👥 Пользователей: {db.query(User).count()}")
            print(f"📅 Мероприятий: {db.query(Event).count()}")
            print(f"📋 Регистраций: {db.query(Registration).count()}")
            
            print("\n🎉 Продакшн база данных готова к работе!")
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
        sys.exit(1)

if __name__ == "__main__":
    create_production_data()
