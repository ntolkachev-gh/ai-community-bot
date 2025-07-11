from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    registration_date = Column(DateTime, default=datetime.utcnow)
    
    # Связь с регистрациями
    registrations = relationship("Registration", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.telegram_id} - {self.first_name} {self.last_name}>"

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_datetime = Column(DateTime, nullable=False)
    webinar_link = Column(String(500), nullable=True)
    max_participants = Column(Integer, default=100)
    
    # Связь с регистрациями
    registrations = relationship("Registration", back_populates="event")
    
    @property
    def available_spots(self):
        """Количество доступных мест"""
        return self.max_participants - len(self.registrations)
    
    @property
    def is_full(self):
        """Проверка заполненности мероприятия"""
        return len(self.registrations) >= self.max_participants
    
    def __repr__(self):
        return f"<Event {self.id} - {self.title}>"

class Registration(Base):
    __tablename__ = 'registrations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    registration_time = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")
    
    def __repr__(self):
        return f"<Registration {self.id} - User {self.user_id} -> Event {self.event_id}>"

def get_database_url():
    """Получение URL базы данных с обработкой Heroku"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Локальная разработка - используем SQLite
        return 'sqlite:///./test.db'
    
    # Heroku предоставляет URL в формате postgres://, но SQLAlchemy 1.4+ требует postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return database_url

# Создание engine с правильной обработкой URL
database_url = get_database_url()
print(f"🔗 Подключение к базе данных: {database_url.split('@')[0]}@***")

engine = create_engine(
    database_url,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    echo=False  # Отключаем логирование SQL в продакшне
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Инициализация базы данных"""
    print("📋 Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы успешно")

def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
