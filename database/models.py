from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import Config

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

# Создание engine и session
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 