#!/usr/bin/env python3
"""
Скрипт для добавления тестовых данных в базу данных
"""

from datetime import datetime, timedelta
from database.models import User, Event, Registration, SessionLocal, init_db

def create_sample_data():
    """Создание тестовых данных"""
    print("Инициализация базы данных...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже данные
        if db.query(User).count() > 0:
            print("База данных уже содержит данные. Пропускаем создание тестовых данных.")
            return
        
        print("Создание тестовых пользователей...")
        # Создаем тестовых пользователей
        users = [
            User(
                telegram_id=123456789,
                username="john_doe",
                first_name="Иван",
                last_name="Иванов",
                email="ivan@example.com"
            ),
            User(
                telegram_id=987654321,
                username="jane_smith",
                first_name="Мария",
                last_name="Петрова",
                email="maria@example.com"
            ),
            User(
                telegram_id=555666777,
                username="alex_dev",
                first_name="Александр",
                last_name="Сидоров"
            )
        ]
        
        for user in users:
            db.add(user)
        db.commit()
        print(f"Создано {len(users)} тестовых пользователей")
        
        print("Создание тестовых мероприятий...")
        # Создаем тестовые мероприятия
        events = [
            Event(
                title="Введение в машинное обучение",
                description="Базовый курс по основам ML для начинающих. Рассмотрим основные алгоритмы и их применение.",
                event_datetime=datetime.now() + timedelta(days=7),
                webinar_link="https://zoom.us/j/1234567890",
                max_participants=50
            ),
            Event(
                title="Python для анализа данных",
                description="Изучим pandas, numpy и matplotlib для работы с данными. Практические примеры и задачи.",
                event_datetime=datetime.now() + timedelta(days=14),
                webinar_link="https://meet.google.com/abc-defg-hij",
                max_participants=30
            ),
            Event(
                title="Создание Telegram ботов",
                description="Пошаговое руководство по созданию ботов для Telegram. От простых команд до сложной логики.",
                event_datetime=datetime.now() + timedelta(days=21),
                webinar_link="https://zoom.us/j/9876543210",
                max_participants=40
            ),
            Event(
                title="Веб-разработка с Flask",
                description="Изучаем создание веб-приложений на Flask. Шаблоны, базы данных, деплой.",
                event_datetime=datetime.now() + timedelta(days=28),
                webinar_link="https://discord.gg/webdev",
                max_participants=25
            ),
            Event(
                title="Прошедшее мероприятие",
                description="Это мероприятие уже прошло - для демонстрации архивных данных.",
                event_datetime=datetime.now() - timedelta(days=7),
                webinar_link="https://zoom.us/j/archived",
                max_participants=20
            )
        ]
        
        for event in events:
            db.add(event)
        db.commit()
        print(f"Создано {len(events)} тестовых мероприятий")
        
        print("Создание тестовых регистраций...")
        # Создаем тестовые регистрации
        registrations = [
            Registration(user_id=1, event_id=1),
            Registration(user_id=2, event_id=1),
            Registration(user_id=3, event_id=1),
            Registration(user_id=1, event_id=2),
            Registration(user_id=2, event_id=3),
            Registration(user_id=3, event_id=4),
            Registration(user_id=1, event_id=5),  # Прошедшее мероприятие
        ]
        
        for registration in registrations:
            db.add(registration)
        db.commit()
        print(f"Создано {len(registrations)} тестовых регистраций")
        
        print("✅ Тестовые данные успешно созданы!")
        
        # Выводим статистику
        print("\n📊 Статистика:")
        print(f"Пользователей: {db.query(User).count()}")
        print(f"Мероприятий: {db.query(Event).count()}")
        print(f"Регистраций: {db.query(Registration).count()}")
        
    except Exception as e:
        print(f"❌ Ошибка при создании тестовых данных: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data() 