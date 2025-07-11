# Быстрый старт 🚀

## Быстрый запуск локально (5 минут)

### 1. Подготовка окружения
```bash
# Клонируйте проект
git clone https://github.com/yourusername/ai-community-bot.git
cd ai-community-bot

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка базы данных
```bash
# Установите PostgreSQL или используйте SQLite для тестов
# Для SQLite замените в config.py:
# DATABASE_URL = 'sqlite:///./test.db'

# Создайте БД PostgreSQL (если используете PostgreSQL)
createdb ai_community_bot
```

### 3. Настройка переменных окружения
Создайте файл `.env`:
```env
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://user:password@localhost/ai_community_bot
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```

### 4. Получение токена бота
1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `.env`

### 5. Запуск приложения
```bash
# Создайте тестовые данные (опционально)
python seed_data.py

# Запустите приложение
python app.py
```

### 6. Проверка работы
- Откройте в браузере: http://localhost:5000
- Найдите вашего бота в Telegram
- Отправьте `/start`

## Быстрый деплой на Heroku (2 минуты)

### 1. Кнопка деплоя
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### 2. Настройка
1. Введите имя приложения
2. Укажите `BOT_TOKEN` от @BotFather
3. Нажмите "Deploy app"
4. Дождитесь завершения деплоя

### 3. Готово!
- Бот автоматически запущен
- Веб-интерфейс доступен по адресу: `https://your-app-name.herokuapp.com`

## Основные команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация пользователя |
| `/events` | Просмотр доступных мероприятий |
| `/my_events` | Мои регистрации |
| `/help` | Справка |

## Веб-интерфейс

### Доступные страницы:
- `/` - Главная страница с статистикой
- `/users` - Список пользователей
- `/events` - Управление мероприятиями  
- `/events/new` - Создание нового мероприятия
- `/registrations` - Просмотр регистраций

## Устранение проблем

### База данных
```bash
# Переинициализация БД
python -c "from database.models import init_db; init_db()"

# Добавление тестовых данных
python seed_data.py
```

### Логи
```bash
# Локально
tail -f logs/app.log

# Heroku
heroku logs --tail
```

### Проблемы с ботом
1. Проверьте токен в `.env`
2. Убедитесь, что бот активирован через @BotFather
3. Проверьте подключение к интернету

## Дополнительные возможности

### Добавление новых команд
1. Откройте `bot/telegram_bot.py`
2. Добавьте новый метод обработчик
3. Зарегистрируйте в `setup_handlers()`

### Кастомизация веб-интерфейса
1. Шаблоны: `templates/`
2. Стили: `templates/base.html`
3. Роуты: `web/app.py`

### Мониторинг
- Статистика: `/api/stats`
- Логи: системные логи
- Метрики: встроенные в Heroku

## Что дальше?

1. 📚 Прочитайте полный [README.md](README.md)
2. 🛠 Настройте дополнительные функции
3. 🚀 Задеплойте на продакшн
4. 📊 Настройте мониторинг
5. 🔐 Добавьте авторизацию в веб-интерфейс

## Поддержка

Если что-то не работает:
1. Проверьте логи
2. Убедитесь, что все зависимости установлены
3. Создайте Issue на GitHub с подробным описанием проблемы 