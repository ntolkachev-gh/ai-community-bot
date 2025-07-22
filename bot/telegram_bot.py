import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from database.models import User, Event, Registration, get_db
from config import Config
from bot.scheduler import NotificationScheduler
from bot.registration_flow import RegistrationFlow

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.bot_token = Config.BOT_TOKEN
        if not self.bot_token:
            raise ValueError("BOT_TOKEN не установлен в переменных окружения")
        self.app = Application.builder().token(self.bot_token).build()
        self.scheduler = NotificationScheduler(self.app.bot)
        self.registration_flow = RegistrationFlow()
        self.setup_handlers()
        
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # Команды
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("events", self.events_command))
        self.app.add_handler(CommandHandler("my_events", self.my_events_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("profile", self.profile_command))
        
        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Текстовые сообщения
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Проверяем, зарегистрирован ли пользователь
        db = next(get_db())
        try:
            existing_user = db.query(User).filter(User.telegram_id == user.id).first()
            
            if not existing_user:
                # Начинаем процесс регистрации
                message, reply_markup = self.registration_flow.start_registration(user.id)
                await update.message.reply_text(message, reply_markup=reply_markup)
            else:
                if existing_user.is_profile_complete:
                    message = f"С возвращением, {existing_user.full_name or user.first_name}! 😊\n\n"
                    message += "Вы уже зарегистрированы в системе.\n\n"
                    message += "Используйте /events для просмотра мероприятий."
                else:
                    # Пользователь есть, но профиль не завершен
                    message = "Добро пожаловать обратно! 👋\n\n"
                    message += "Ваша регистрация не была завершена. Давайте продолжим:\n\n"
                    message += "Как вас зовут? (полное имя)"
                    self.registration_flow.user_states[user.id] = {
                        'step': self.registration_flow.RegistrationStep.FULL_NAME,
                        'data': {}
                    }
                
                await update.message.reply_text(message)
                
        except Exception as e:
            logger.error(f"Ошибка при проверке пользователя: {e}")
            message = "Произошла ошибка. Попробуйте позже."
            await update.message.reply_text(message)
        finally:
            db.close()
    
    async def events_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список доступных мероприятий"""
        user = update.effective_user
        db = next(get_db())
        
        try:
            # Проверяем, зарегистрирован ли пользователь и завершен ли профиль
            user_obj = db.query(User).filter(User.telegram_id == user.id).first()
            if not user_obj:
                await update.message.reply_text("Вы не зарегистрированы. Используйте /start")
                return
            
            if not user_obj.is_profile_complete:
                await update.message.reply_text("Ваш профиль не завершен. Используйте /start для завершения регистрации.")
                return
            
            # Получаем будущие мероприятия
            events = db.query(Event).filter(Event.event_datetime > datetime.utcnow()).all()
            
            if not events:
                await update.message.reply_text("В данный момент нет доступных мероприятий.")
                return
            
            message = "🗓 Доступные мероприятия:\n\n"
            keyboard = []
            
            for event in events:
                event_date = event.event_datetime.strftime("%d.%m.%Y %H:%M")
                spots_left = event.available_spots
                
                message += f"📅 {event.title}\n"
                message += f"📝 {event.description[:100]}{'...' if len(event.description) > 100 else ''}\n"
                message += f"🕐 {event_date}\n"
                message += f"👥 Свободных мест: {spots_left}\n\n"
                
                if not event.is_full:
                    keyboard.append([InlineKeyboardButton(
                        f"Записаться на '{event.title[:30]}...'",
                        callback_data=f"register_{event.id}"
                    )])
                else:
                    keyboard.append([InlineKeyboardButton(
                        f"'{event.title[:30]}...' - ЗАПОЛНЕНО",
                        callback_data=f"full_{event.id}"
                    )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка при получении мероприятий: {e}")
            await update.message.reply_text("Произошла ошибка при загрузке мероприятий.")
        finally:
            db.close()
    
    async def my_events_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать мои регистрации"""
        user = update.effective_user
        db = next(get_db())
        
        try:
            user_obj = db.query(User).filter(User.telegram_id == user.id).first()
            if not user_obj:
                await update.message.reply_text("Вы не зарегистрированы. Используйте /start")
                return
            
            if not user_obj.is_profile_complete:
                await update.message.reply_text("Ваш профиль не завершен. Используйте /start для завершения регистрации.")
                return
            
            registrations = db.query(Registration).filter(Registration.user_id == user_obj.id).all()
            
            if not registrations:
                await update.message.reply_text("У вас нет активных регистраций на мероприятия.")
                return
            
            message = "📋 Ваши регистрации:\n\n"
            keyboard = []
            
            for reg in registrations:
                event = reg.event
                event_date = event.event_datetime.strftime("%d.%m.%Y %H:%M")
                reg_date = reg.registration_time.strftime("%d.%m.%Y %H:%M")
                
                message += f"📅 {event.title}\n"
                message += f"🕐 {event_date}\n"
                message += f"✅ Зарегистрирован: {reg_date}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"Отменить '{event.title[:30]}...'",
                    callback_data=f"cancel_{reg.id}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка при получении регистраций: {e}")
            await update.message.reply_text("Произошла ошибка при загрузке ваших регистраций.")
        finally:
            db.close()
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда помощи"""
        help_text = """
🤖 AI Community Bot - Помощь

Доступные команды:
/start - Регистрация в системе
/profile - Просмотр вашего профиля
/events - Просмотр доступных мероприятий
/my_events - Мои регистрации
/help - Эта справка

Как использовать:
1. Начните с команды /start для регистрации
2. Заполните информацию о себе (имя, компания, роль, опыт с ИИ, email)
3. Используйте /events для просмотра мероприятий
4. Нажмите на кнопку "Записаться" для регистрации
5. Проверьте свои регистрации через /my_events
6. Отмените регистрацию при необходимости
7. Просмотрите свой профиль через /profile

За день до мероприятия вы получите напоминание!
        """
        await update.message.reply_text(help_text)
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий кнопок"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = update.effective_user
        
        if data.startswith("register_"):
            await self.handle_registration(query, user, data)
        elif data.startswith("cancel_"):
            await self.handle_cancellation(query, user, data)
        elif data.startswith("full_"):
            await query.edit_message_text("Это мероприятие уже заполнено!")
        elif data.startswith("ai_exp_"):
            await self.handle_ai_experience_selection(query, user, data)
    
    async def handle_registration(self, query, user, data):
        """Обработка регистрации на мероприятие"""
        event_id = int(data.split("_")[1])
        db = next(get_db())
        
        try:
            user_obj = db.query(User).filter(User.telegram_id == user.id).first()
            if not user_obj:
                await query.edit_message_text("Вы не зарегистрированы. Используйте /start")
                return
            
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                await query.edit_message_text("Мероприятие не найдено.")
                return
            
            # Проверка, не зарегистрирован ли уже
            existing_reg = db.query(Registration).filter(
                Registration.user_id == user_obj.id,
                Registration.event_id == event_id
            ).first()
            
            if existing_reg:
                await query.edit_message_text("Вы уже зарегистрированы на это мероприятие!")
                return
            
            if event.is_full:
                await query.edit_message_text("К сожалению, мероприятие уже заполнено.")
                return
            
            # Создание регистрации
            registration = Registration(
                user_id=user_obj.id,
                event_id=event_id
            )
            db.add(registration)
            db.commit()
            
            # Добавление напоминания
            self.scheduler.add_reminder(user.id, event)
            
            message = f"✅ Вы успешно зарегистрированы на мероприятие!\n\n"
            message += f"📅 {event.title}\n"
            message += f"🕐 {event.event_datetime.strftime('%d.%m.%Y %H:%M')}\n"
            message += f"👥 Осталось мест: {event.available_spots - 1}\n\n"
            message += "Вы получите напоминание за день до мероприятия."
            
            await query.edit_message_text(message)
            
        except Exception as e:
            logger.error(f"Ошибка при регистрации: {e}")
            await query.edit_message_text("Произошла ошибка при регистрации.")
        finally:
            db.close()
    
    async def handle_cancellation(self, query, user, data):
        """Обработка отмены регистрации"""
        registration_id = int(data.split("_")[1])
        db = next(get_db())
        
        try:
            registration = db.query(Registration).filter(Registration.id == registration_id).first()
            if not registration:
                await query.edit_message_text("Регистрация не найдена.")
                return
            
            event_title = registration.event.title
            db.delete(registration)
            db.commit()
            
            message = f"❌ Регистрация отменена!\n\n"
            message += f"Мероприятие: {event_title}\n"
            message += "Вы можете зарегистрироваться снова, если передумаете."
            
            await query.edit_message_text(message)
            
        except Exception as e:
            logger.error(f"Ошибка при отмене регистрации: {e}")
            await query.edit_message_text("Произошла ошибка при отмене регистрации.")
        finally:
            db.close()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user = update.effective_user
        text = update.message.text
        
        # Проверяем, находится ли пользователь в процессе регистрации
        if self.registration_flow.is_user_registering(user.id):
            message, reply_markup = self.registration_flow.process_step(user.id, text)
            
            if self.registration_flow.is_registration_complete(user.id):
                # Завершаем регистрацию в базе данных
                await self.complete_registration(user)
                self.registration_flow.clear_user_state(user.id)
            
            await update.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(
                "Используйте команды для взаимодействия с ботом:\n"
                "/events - Просмотр мероприятий\n"
                "/my_events - Мои регистрации\n"
                "/help - Помощь"
            )
    
    async def handle_ai_experience_selection(self, query, user, data):
        """Обработка выбора опыта с ИИ"""
        message, reply_markup = self.registration_flow.process_ai_experience_callback(user.id, data)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def complete_registration(self, user):
        """Завершение регистрации пользователя в базе данных"""
        db = next(get_db())
        try:
            user_data = self.registration_flow.get_user_data(user.id)
            
            # Создаем или обновляем пользователя
            existing_user = db.query(User).filter(User.telegram_id == user.id).first()
            
            if existing_user:
                # Обновляем существующего пользователя
                existing_user.full_name = user_data.get('full_name')
                existing_user.company = user_data.get('company')
                existing_user.role = user_data.get('role')
                existing_user.ai_experience = user_data.get('ai_experience')
                existing_user.email = user_data.get('email')
                existing_user.is_profile_complete = 1
            else:
                # Создаем нового пользователя
                new_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    full_name=user_data.get('full_name'),
                    company=user_data.get('company'),
                    role=user_data.get('role'),
                    ai_experience=user_data.get('ai_experience'),
                    email=user_data.get('email'),
                    is_profile_complete=1
                )
                db.add(new_user)
            
            db.commit()
            logger.info(f"Пользователь {user.id} успешно зарегистрирован")
            
        except Exception as e:
            logger.error(f"Ошибка при завершении регистрации: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для просмотра профиля"""
        user = update.effective_user
        db = next(get_db())
        
        try:
            user_obj = db.query(User).filter(User.telegram_id == user.id).first()
            if not user_obj:
                await update.message.reply_text("Вы не зарегистрированы. Используйте /start")
                return
            
            if not user_obj.is_profile_complete:
                await update.message.reply_text("Ваш профиль не завершен. Используйте /start для завершения регистрации.")
                return
            
            message = "👤 Ваш профиль:\n\n"
            message += f"📝 Имя: {user_obj.full_name}\n"
            message += f"🏢 Компания: {user_obj.company}\n"
            message += f"💼 Роль: {user_obj.role}\n"
            message += f"🤖 Опыт с ИИ: {user_obj.ai_experience}\n"
            message += f"📧 Email: {user_obj.email}\n"
            message += f"📅 Дата регистрации: {user_obj.registration_date.strftime('%d.%m.%Y')}"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Ошибка при получении профиля: {e}")
            await update.message.reply_text("Произошла ошибка при загрузке профиля.")
        finally:
            db.close()
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск Telegram бота...")
        self.app.run_polling() 