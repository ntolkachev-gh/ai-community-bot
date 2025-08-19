import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from database.models import User, Event, Registration, get_db
from config import Config
from bot.scheduler import NotificationScheduler
from bot.registration_flow import RegistrationFlow
import urllib.parse
import pytz

logger = logging.getLogger(__name__)

def convert_to_user_timezone(event_datetime, user_timezone='UTC'):
    """
    Конвертирует время мероприятия в часовой пояс пользователя
    
    Args:
        event_datetime (datetime): Время мероприятия в UTC
        user_timezone (str): Часовой пояс пользователя
    
    Returns:
        str: Отформатированное время в часовом поясе пользователя
    """
    try:
        # Создаем timezone объект
        user_tz = pytz.timezone(user_timezone)
        
        # Если event_datetime не имеет timezone info, считаем что это UTC
        if event_datetime.tzinfo is None:
            utc_tz = pytz.UTC
            event_datetime = utc_tz.localize(event_datetime)
        
        # Конвертируем в часовой пояс пользователя
        user_time = event_datetime.astimezone(user_tz)
        
        # Форматируем время
        return user_time.strftime("%d.%m.%Y %H:%M")
    except Exception as e:
        logger.error(f"Ошибка конвертации времени: {e}")
        # Возвращаем время в UTC если что-то пошло не так
        return event_datetime.strftime("%d.%m.%Y %H:%M")

def generate_google_calendar_link(event_title, event_datetime, description="", location=""):
    """
    Генерирует ссылку на Google Calendar для добавления события
    
    Args:
        event_title (str): Название мероприятия
        event_datetime (datetime): Дата и время мероприятия
        description (str): Описание мероприятия
        location (str): Место проведения (ссылка на Zoom и т.д.)
    
    Returns:
        str: URL для добавления события в Google Calendar
    """
    # Форматируем дату и время для Google Calendar
    start_time = event_datetime.strftime("%Y%m%dT%H%M%SZ")
    # Предполагаем, что мероприятие длится 1 час
    end_time = (event_datetime + timedelta(hours=1)).strftime("%Y%m%dT%H%M%SZ")
    
    # Формируем описание
    full_description = description
    if location:
        full_description += f"\n\nСсылка для подключения: {location}"
    
    # Кодируем параметры для URL
    params = {
        'action': 'TEMPLATE',
        'text': event_title,
        'dates': f"{start_time}/{end_time}",
        'details': full_description,
        'sf': 'true',
        'output': 'xml'
    }
    
    # Создаем URL
    base_url = "https://calendar.google.com/calendar/render"
    query_string = urllib.parse.urlencode(params)
    calendar_url = f"{base_url}?{query_string}"
    
    return calendar_url

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
        self.app.add_handler(CommandHandler("edit_profile", self.edit_profile_command))
        self.app.add_handler(CommandHandler("timezone", self.timezone_command))
        
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
            events = db.query(Event).filter(Event.event_datetime > datetime.utcnow()).order_by(Event.event_datetime.asc()).all()
            
            if not events:
                await update.message.reply_text("В данный момент нет доступных мероприятий.")
                return
            
            message = "🗓 **Доступные мероприятия:**\n\n"
            keyboard = []
            
            for i, event in enumerate(events, 1):
                # Конвертируем время в часовой пояс пользователя
                event_date = convert_to_user_timezone(event.event_datetime, user_obj.timezone)
                spots_left = event.available_spots
                
                # Показываем только номер, название и дату
                message += f"{i}. **{event.title}**\n"
                message += f"🕐 {event_date}\n"
                message += f"👥 Свободных мест: {spots_left}\n\n"
                
                # Создаем inline кнопку для каждого события
                if not event.is_full:
                    button_text = f"Записаться #{i}"
                    keyboard.append([InlineKeyboardButton(
                        button_text,
                        callback_data=f"register_{event.id}"
                    )])
                else:
                    button_text = f"❌ ЗАПОЛНЕНО #{i}"
                    keyboard.append([InlineKeyboardButton(
                        button_text,
                        callback_data=f"full_{event.id}"
                    )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
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
            
            # Получаем активные регистрации (только на будущие мероприятия)
            registrations = db.query(Registration).join(Event).filter(
                Registration.user_id == user_obj.id,
                Event.event_datetime > datetime.utcnow()
            ).order_by(Event.event_datetime.asc()).all()
            
            if not registrations:
                await update.message.reply_text("У вас нет активных регистраций на мероприятия.")
                return
            
            message = "📋 Ваши регистрации:\n\n"
            keyboard = []
            
            for reg in registrations:
                event = reg.event
                if not event:  # Проверяем, что мероприятие существует
                    continue
                    
                # Конвертируем время в часовой пояс пользователя
                event_date = convert_to_user_timezone(event.event_datetime, user_obj.timezone)
                reg_date = reg.registration_time.strftime("%d.%m.%Y %H:%M")
                
                message += f"📅 {event.title}\n"
                message += f"🕐 {event_date}\n"
                message += f"✅ Зарегистрирован: {reg_date}\n"
                
                # Добавляем ссылку на мероприятие, если она есть
                if event.webinar_link:
                    message += f"🔗 {event.webinar_link}\n"
                
                message += "\n"
                
                # Генерируем ссылку на Google Calendar для кнопки
                calendar_link = generate_google_calendar_link(
                    event_title=event.title,
                    event_datetime=event.event_datetime,
                    description=event.description or "",
                    location=event.webinar_link or ""
                )
                
                # Создаем кнопки для каждого мероприятия
                event_buttons = []
                
                # Кнопка "Добавить в календарь"
                event_buttons.append(InlineKeyboardButton(
                    "📅 Добавить в календарь",
                    url=calendar_link
                ))
                
                event_buttons.append(InlineKeyboardButton(
                    "Отменить",
                    callback_data=f"cancel_{reg.id}"
                ))
                
                keyboard.append(event_buttons)
            
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
/edit_profile - Редактирование профиля
/events - Просмотр доступных мероприятий
/my_events - Мои регистрации
/timezone - Настройка часового пояса
/help - Эта справка

Как использовать:
1. Начните с команды /start для регистрации
2. Заполните информацию о себе (имя, компания, роль, опыт с ИИ, email)
3. Используйте /events для просмотра мероприятий
4. Нажмите на кнопку "Записаться" для регистрации
5. Проверьте свои регистрации через /my_events
6. Отмените регистрацию при необходимости
7. Просмотрите свой профиль через /profile
8. Измените данные профиля через /edit_profile

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
        elif data.startswith("timezone_"):
            await self.handle_timezone_selection(query, user, data)
        elif data.startswith("edit_"):
            await self.handle_profile_edit_selection(query, user, data)
    
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
            # Конвертируем время в часовой пояс пользователя
            event_date = convert_to_user_timezone(event.event_datetime, user_obj.timezone)
            message += f"🕐 {event_date}\n"
            message += f"👥 Осталось мест: {event.available_spots - 1}\n"
            
            # Добавляем ссылку на мероприятие, если она есть
            if event.webinar_link:
                message += f"🔗 {event.webinar_link}\n"
            
            message += "\nВы получите напоминание за день до мероприятия."
            
            # Генерируем ссылку на Google Calendar для кнопки
            calendar_link = generate_google_calendar_link(
                event_title=event.title,
                event_datetime=event.event_datetime,
                description=event.description or "",
                location=event.webinar_link or ""
            )
            
            # Создаем кнопку "Добавить в календарь"
            keyboard = [[InlineKeyboardButton(
                "📅 Добавить в календарь",
                url=calendar_link
            )]]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
            
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
    
    async def handle_timezone_selection(self, query, user, data):
        """Обработка выбора часового пояса"""
        timezone_name = data.split("_", 1)[1]  # Получаем название часового пояса
        db = next(get_db())
        
        try:
            user_obj = db.query(User).filter(User.telegram_id == user.id).first()
            if not user_obj:
                await query.edit_message_text("Вы не зарегистрированы. Используйте /start")
                return
            
            # Проверяем, что часовой пояс существует
            try:
                pytz.timezone(timezone_name)
            except pytz.exceptions.UnknownTimeZoneError:
                await query.edit_message_text(f"❌ Неизвестный часовой пояс: {timezone_name}")
                return
            
            # Обновляем часовой пояс пользователя
            user_obj.timezone = timezone_name
            db.commit()
            
            # Получаем текущее время в выбранном часовом поясе для демонстрации
            user_tz = pytz.timezone(timezone_name)
            current_time = datetime.now(user_tz).strftime("%H:%M")
            
            message = f"✅ Ваш часовой пояс обновлен!\n\n"
            message += f"🕐 Новый часовой пояс: {timezone_name}\n"
            message += f"⏰ Текущее время: {current_time}\n\n"
            message += "Теперь время всех мероприятий будет отображаться в вашем часовом поясе."
            
            await query.edit_message_text(message)
            
        except Exception as e:
            logger.error(f"Ошибка при выборе часового пояса: {e}")
            await query.edit_message_text("Произошла ошибка при настройке часового пояса.")
        finally:
            db.close()
    
    async def handle_profile_edit_selection(self, query, user, data):
        """Обработка выбора поля для редактирования профиля"""
        field = data.split("_", 1)[1]  # Получаем название поля
        db = next(get_db())
        
        try:
            user_obj = db.query(User).filter(User.telegram_id == user.id).first()
            if not user_obj:
                await query.edit_message_text("Вы не зарегистрированы. Используйте /start")
                return
            
            # Сохраняем состояние редактирования для пользователя
            if not hasattr(self, 'edit_states'):
                self.edit_states = {}
            
            self.edit_states[user.id] = {
                'field': field,
                'user_id': user_obj.id
            }
            
            # Определяем сообщение в зависимости от поля
            field_messages = {
                'full_name': "📝 Введите ваше полное имя:",
                'company': "🏢 Введите название компании:",
                'role': "💼 Введите вашу роль/должность:",
                'ai_experience': "🤖 Выберите ваш опыт работы с ИИ:",
                'email': "📧 Введите ваш email:"
            }
            
            message = field_messages.get(field, "Введите новое значение:")
            
            if field == 'ai_experience':
                # Для опыта с ИИ показываем кнопки выбора
                keyboard = [
                    [
                        InlineKeyboardButton("Новичок", callback_data="ai_exp_novice"),
                        InlineKeyboardButton("Начинающий", callback_data="ai_exp_beginner")
                    ],
                    [
                        InlineKeyboardButton("Средний", callback_data="ai_exp_intermediate"),
                        InlineKeyboardButton("Продвинутый", callback_data="ai_exp_advanced")
                    ],
                    [
                        InlineKeyboardButton("Эксперт", callback_data="ai_exp_expert")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(message, reply_markup=reply_markup)
            else:
                # Для остальных полей просим ввести текст
                await query.edit_message_text(message)
            
        except Exception as e:
            logger.error(f"Ошибка при выборе поля для редактирования: {e}")
            await query.edit_message_text("Произошла ошибка при редактировании профиля.")
        finally:
            db.close()
    
    async def handle_profile_edit_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода нового значения для редактирования профиля"""
        user = update.effective_user
        text = update.message.text
        edit_state = self.edit_states[user.id]
        field = edit_state['field']
        user_id = edit_state['user_id']
        
        db = next(get_db())
        
        try:
            user_obj = db.query(User).filter(User.id == user_id).first()
            if not user_obj:
                await update.message.reply_text("Пользователь не найден.")
                return
            
            # Валидация и обновление поля
            if field == 'email':
                # Простая валидация email
                if '@' not in text or '.' not in text:
                    await update.message.reply_text("❌ Неверный формат email. Попробуйте еще раз:")
                    return
                user_obj.email = text
            elif field == 'full_name':
                if len(text.strip()) < 2:
                    await update.message.reply_text("❌ Имя должно содержать минимум 2 символа. Попробуйте еще раз:")
                    return
                user_obj.full_name = text.strip()
            elif field == 'company':
                if len(text.strip()) < 2:
                    await update.message.reply_text("❌ Название компании должно содержать минимум 2 символа. Попробуйте еще раз:")
                    return
                user_obj.company = text.strip()
            elif field == 'role':
                if len(text.strip()) < 2:
                    await update.message.reply_text("❌ Роль должна содержать минимум 2 символа. Попробуйте еще раз:")
                    return
                user_obj.role = text.strip()
            
            db.commit()
            
            # Очищаем состояние редактирования
            del self.edit_states[user.id]
            
            # Показываем обновленный профиль
            message = "✅ Профиль успешно обновлен!\n\n"
            message += "👤 Ваш профиль:\n\n"
            message += f"📝 Имя: {user_obj.full_name}\n"
            message += f"🏢 Компания: {user_obj.company}\n"
            message += f"💼 Роль: {user_obj.role}\n"
            message += f"🤖 Опыт с ИИ: {user_obj.ai_experience}\n"
            message += f"📧 Email: {user_obj.email}\n"
            message += f"📅 Дата регистрации: {user_obj.registration_date.strftime('%d.%m.%Y')}"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении профиля: {e}")
            await update.message.reply_text("Произошла ошибка при обновлении профиля.")
        finally:
            db.close()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user = update.effective_user
        text = update.message.text
        
        # Проверяем, находится ли пользователь в процессе редактирования профиля
        if hasattr(self, 'edit_states') and user.id in self.edit_states:
            await self.handle_profile_edit_input(update, context)
            return
        
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
                "/edit_profile - Редактировать профиль\n"
                "/help - Помощь"
            )
    
    async def handle_ai_experience_selection(self, query, user, data):
        """Обработка выбора опыта с ИИ"""
        # Проверяем, находится ли пользователь в процессе редактирования профиля
        if hasattr(self, 'edit_states') and user.id in self.edit_states:
            await self.handle_ai_experience_edit(query, user, data)
        else:
            # Обычная регистрация
            message, reply_markup = self.registration_flow.process_ai_experience_callback(user.id, data)
            await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def handle_ai_experience_edit(self, query, user, data):
        """Обработка выбора опыта с ИИ при редактировании профиля"""
        experience_level = data.split("_", 1)[1]  # Получаем уровень опыта
        edit_state = self.edit_states[user.id]
        user_id = edit_state['user_id']
        
        # Маппинг уровней опыта
        experience_mapping = {
            'novice': 'Новичок',
            'beginner': 'Начинающий',
            'intermediate': 'Средний',
            'advanced': 'Продвинутый',
            'expert': 'Эксперт'
        }
        
        db = next(get_db())
        
        try:
            user_obj = db.query(User).filter(User.id == user_id).first()
            if not user_obj:
                await query.edit_message_text("Пользователь не найден.")
                return
            
            # Обновляем опыт с ИИ
            user_obj.ai_experience = experience_mapping.get(experience_level, experience_level)
            db.commit()
            
            # Очищаем состояние редактирования
            del self.edit_states[user.id]
            
            # Показываем обновленный профиль
            message = "✅ Профиль успешно обновлен!\n\n"
            message += "👤 Ваш профиль:\n\n"
            message += f"📝 Имя: {user_obj.full_name}\n"
            message += f"🏢 Компания: {user_obj.company}\n"
            message += f"💼 Роль: {user_obj.role}\n"
            message += f"🤖 Опыт с ИИ: {user_obj.ai_experience}\n"
            message += f"📧 Email: {user_obj.email}\n"
            message += f"📅 Дата регистрации: {user_obj.registration_date.strftime('%d.%m.%Y')}"
            
            await query.edit_message_text(message)
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении опыта с ИИ: {e}")
            await query.edit_message_text("Произошла ошибка при обновлении профиля.")
        finally:
            db.close()
    
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
    
    async def edit_profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для редактирования профиля"""
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
            
            message = "✏️ Редактирование профиля\n\n"
            message += "Выберите поле, которое хотите изменить:"
            
            # Создаем кнопки для редактирования полей
            keyboard = [
                [
                    InlineKeyboardButton("📝 Полное имя", callback_data="edit_full_name"),
                    InlineKeyboardButton("🏢 Компания", callback_data="edit_company")
                ],
                [
                    InlineKeyboardButton("💼 Роль", callback_data="edit_role"),
                    InlineKeyboardButton("🤖 Опыт с ИИ", callback_data="edit_ai_experience")
                ],
                [
                    InlineKeyboardButton("📧 Email", callback_data="edit_email")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка при редактировании профиля: {e}")
            await update.message.reply_text("Произошла ошибка при редактировании профиля.")
        finally:
            db.close()
    
    async def timezone_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для настройки часового пояса"""
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
            
            # Проверяем, есть ли аргумент в команде (для обратной совместимости)
            if context.args:
                new_timezone = context.args[0]
                try:
                    # Проверяем, что часовой пояс существует
                    pytz.timezone(new_timezone)
                    
                    # Обновляем часовой пояс пользователя
                    user_obj.timezone = new_timezone
                    db.commit()
                    
                    message = f"✅ Ваш часовой пояс обновлен на: {new_timezone}\n\n"
                    message += "Теперь время мероприятий будет отображаться в вашем часовом поясе."
                    
                    await update.message.reply_text(message)
                    
                except pytz.exceptions.UnknownTimeZoneError:
                    await update.message.reply_text(
                        f"❌ Неизвестный часовой пояс: {new_timezone}\n\n"
                        "Используйте кнопки ниже для выбора часового пояса."
                    )
            else:
                # Показываем текущий часовой пояс и кнопки для выбора
                current_tz = user_obj.timezone or 'UTC'
                message = f"🕐 Ваш текущий часовой пояс: {current_tz}\n\n"
                message += "Выберите новый часовой пояс:"
                
                # Создаем кнопки для популярных часовых поясов
                keyboard = [
                    [
                        InlineKeyboardButton("🇷🇺 Москва (MSK)", callback_data="timezone_Europe/Moscow"),
                        InlineKeyboardButton("🇬🇧 Лондон (GMT)", callback_data="timezone_Europe/London")
                    ],
                    [
                        InlineKeyboardButton("🇺🇸 Нью-Йорк (EST)", callback_data="timezone_America/New_York"),
                        InlineKeyboardButton("🇺🇸 Лос-Анджелес (PST)", callback_data="timezone_America/Los_Angeles")
                    ],
                    [
                        InlineKeyboardButton("🇯🇵 Токио (JST)", callback_data="timezone_Asia/Tokyo"),
                        InlineKeyboardButton("🇨🇳 Пекин (CST)", callback_data="timezone_Asia/Shanghai")
                    ],
                    [
                        InlineKeyboardButton("🇦🇺 Сидней (AEST)", callback_data="timezone_Australia/Sydney"),
                        InlineKeyboardButton("🇮🇳 Мумбаи (IST)", callback_data="timezone_Asia/Kolkata")
                    ],
                    [
                        InlineKeyboardButton("🌍 UTC (Всемирное время)", callback_data="timezone_UTC")
                    ]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка при настройке часового пояса: {e}")
            await update.message.reply_text("Произошла ошибка при настройке часового пояса.")
        finally:
            db.close()
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск Telegram бота...")
        self.app.run_polling() 