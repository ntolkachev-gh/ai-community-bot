from enum import Enum
from typing import Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class RegistrationStep(Enum):
    """Шаги процесса регистрации"""
    FULL_NAME = "full_name"
    COMPANY = "company"
    ROLE = "role"
    AI_EXPERIENCE = "ai_experience"
    EMAIL = "email"
    COMPLETE = "complete"

class AIExperienceOption(Enum):
    """Варианты опыта с ИИ"""
    NO_AI_NO_NEED = "Не использую ИИ, нет потребности"
    NO_AI_WANT_TO = "Не использую ИИ, но хотелось бы"
    BASIC_AI = "Использую базовые нейросети (ChatGPT и другие)"
    AI_AGENTS = "Создаю отдельных ИИ-агентов"
    AI_PRODUCT = "Создаю ИИ-продукт"
    INDUSTRIAL_AI = "Создаю промышленные ИИ-решения"
    OTHER = "Иное"

class RegistrationFlow:
    """Управление процессом регистрации пользователей"""
    
    def __init__(self):
        self.user_states: Dict[int, Dict[str, Any]] = {}
    
    def start_registration(self, user_id: int) -> tuple[str, InlineKeyboardMarkup]:
        """Начало процесса регистрации"""
        self.user_states[user_id] = {
            'step': RegistrationStep.FULL_NAME,
            'data': {}
        }
        
        message = "👋 Добро пожаловать в AI Community!\n\n"
        message += "Для завершения регистрации нам нужно узнать немного о вас.\n\n"
        message += "Как вас зовут? (полное имя)"
        
        return message, None
    
    def process_step(self, user_id: int, text: str) -> tuple[str, InlineKeyboardMarkup]:
        """Обработка текущего шага регистрации"""
        if user_id not in self.user_states:
            return "Произошла ошибка. Начните регистрацию заново с /start", None
        
        state = self.user_states[user_id]
        current_step = state['step']
        
        if current_step == RegistrationStep.FULL_NAME:
            return self._process_full_name(user_id, text)
        elif current_step == RegistrationStep.COMPANY:
            return self._process_company(user_id, text)
        elif current_step == RegistrationStep.ROLE:
            return self._process_role(user_id, text)
        elif current_step == RegistrationStep.AI_EXPERIENCE:
            return self._process_ai_experience(user_id, text)
        elif current_step == RegistrationStep.EMAIL:
            return self._process_email(user_id, text)
        
        return "Неизвестный шаг регистрации", None
    
    def _process_full_name(self, user_id: int, text: str) -> tuple[str, InlineKeyboardMarkup]:
        """Обработка ввода полного имени"""
        self.user_states[user_id]['data']['full_name'] = text
        self.user_states[user_id]['step'] = RegistrationStep.COMPANY
        
        message = f"Спасибо, {text}! 👋\n\n"
        message += "В какой компании вы работаете?"
        
        return message, None
    
    def _process_company(self, user_id: int, text: str) -> tuple[str, InlineKeyboardMarkup]:
        """Обработка ввода компании"""
        self.user_states[user_id]['data']['company'] = text
        self.user_states[user_id]['step'] = RegistrationStep.ROLE
        
        message = f"Компания: {text} ✅\n\n"
        message += "В какой роли вы там работаете?"
        
        return message, None
    
    def _process_role(self, user_id: int, text: str) -> tuple[str, InlineKeyboardMarkup]:
        """Обработка ввода роли"""
        self.user_states[user_id]['data']['role'] = text
        self.user_states[user_id]['step'] = RegistrationStep.AI_EXPERIENCE
        
        message = f"Роль: {text} ✅\n\n"
        message += "Что ближе вас описывает?\n\n"
        message += "Выберите один из вариантов:"
        
        keyboard = []
        for option in AIExperienceOption:
            keyboard.append([InlineKeyboardButton(
                option.value,
                callback_data=f"ai_exp_{option.name}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        return message, reply_markup
    
    def _process_ai_experience(self, user_id: int, text: str) -> tuple[str, InlineKeyboardMarkup]:
        """Обработка выбора опыта с ИИ"""
        # Этот метод будет вызываться через callback
        return "Ошибка обработки", None
    
    def process_ai_experience_callback(self, user_id: int, callback_data: str) -> tuple[str, InlineKeyboardMarkup]:
        """Обработка выбора опыта с ИИ через callback"""
        try:
            ai_exp_option = callback_data.split('_')[2]  # ai_exp_OPTION_NAME
            option = AIExperienceOption[ai_exp_option]
            self.user_states[user_id]['data']['ai_experience'] = option.value
            self.user_states[user_id]['step'] = RegistrationStep.EMAIL
            
            message = f"Опыт с ИИ: {option.value} ✅\n\n"
            
            if option == AIExperienceOption.OTHER:
                message += "Пожалуйста, укажите ваш e-mail для добавления в календарь события с ссылкой на Zoom:"
            else:
                message += "Для добавления в календарь события с ссылкой на Zoom, укажите ваш e-mail:"
            
            return message, None
            
        except (KeyError, IndexError) as e:
            print(f"Ошибка обработки callback: {callback_data}, ошибка: {e}")
            return "Ошибка обработки выбора", None
    
    def _process_email(self, user_id: int, text: str) -> tuple[str, InlineKeyboardMarkup]:
        """Обработка ввода email"""
        # Простая валидация email
        if '@' not in text or '.' not in text:
            return "Пожалуйста, введите корректный email адрес:", None
        
        self.user_states[user_id]['data']['email'] = text
        self.user_states[user_id]['step'] = RegistrationStep.COMPLETE
        
        message = "🎉 Регистрация завершена!\n\n"
        message += "Ваш профиль:\n"
        data = self.user_states[user_id]['data']
        message += f"👤 Имя: {data['full_name']}\n"
        message += f"🏢 Компания: {data['company']}\n"
        message += f"💼 Роль: {data['role']}\n"
        message += f"🤖 Опыт с ИИ: {data['ai_experience']}\n"
        message += f"📧 Email: {data['email']}\n\n"
        message += "Теперь вы можете:\n"
        message += "/events - Просмотр мероприятий\n"
        message += "/my_events - Мои регистрации\n"
        message += "/help - Помощь"
        
        return message, None
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Получение данных пользователя из состояния"""
        if user_id in self.user_states:
            return self.user_states[user_id]['data']
        return {}
    
    def clear_user_state(self, user_id: int):
        """Очистка состояния пользователя"""
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    def is_user_registering(self, user_id: int) -> bool:
        """Проверка, находится ли пользователь в процессе регистрации"""
        return user_id in self.user_states
    
    def is_registration_complete(self, user_id: int) -> bool:
        """Проверка, завершена ли регистрация"""
        if user_id not in self.user_states:
            return False
        return self.user_states[user_id]['step'] == RegistrationStep.COMPLETE 