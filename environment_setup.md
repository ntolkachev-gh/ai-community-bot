# Настройка переменных окружения

Создайте файл `.env` в корне проекта со следующими переменными:

```
# Telegram Bot Token
BOT_TOKEN=your_bot_token_here

# Database
DATABASE_URL=postgresql://user:password@localhost/ai_community_bot

# Flask
SECRET_KEY=your_secret_key_here

# Environment
FLASK_ENV=development
FLASK_APP=app.py

# Web interface
WEB_HOST=0.0.0.0
PORT=5000
```

## Получение токена бота

1. Напишите @BotFather в Telegram
2. Отправьте `/newbot`
3. Введите название бота
4. Введите username бота (должен заканчиваться на `bot`)
5. Скопируйте полученный токен в переменную `BOT_TOKEN`

## Настройка PostgreSQL

1. Установите PostgreSQL
2. Создайте базу данных: `createdb ai_community_bot`
3. Обновите переменную `DATABASE_URL` с вашими данными подключения 