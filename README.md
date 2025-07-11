# AI Community Bot 🤖

Telegram бот для управления мероприятиями с веб-интерфейсом CRM.

## Функционал

### Telegram Bot
- `/start` - Регистрация пользователя
- `/events` - Просмотр доступных мероприятий  
- `/my_events` - Мои регистрации
- Запись на мероприятия
- Отмена регистрации
- Автоматические напоминания за день до мероприятия

### CRM Веб-интерфейс
- Панель управления с статистикой
- Управление пользователями
- Создание и редактирование мероприятий
- Просмотр регистраций
- Экспорт данных

## Технологии

- **Python** 3.11+
- **python-telegram-bot** - Telegram Bot API
- **Flask** - веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **PostgreSQL** - база данных
- **APScheduler** - планировщик задач
- **Bootstrap 5** - UI фреймворк

## Структура проекта

```
├── app.py                 # Главный файл приложения
├── config.py              # Конфигурация
├── requirements.txt       # Зависимости
├── bot/                   # Telegram бот
│   ├── telegram_bot.py    # Основной класс бота
│   └── scheduler.py       # Планировщик напоминаний
├── web/                   # Веб-интерфейс
│   └── app.py            # Flask приложение
├── database/              # Модели базы данных
│   └── models.py         # SQLAlchemy модели
├── templates/             # HTML шаблоны
│   ├── base.html         # Базовый шаблон
│   ├── index.html        # Главная страница
│   ├── events.html       # Список мероприятий
│   ├── users.html        # Список пользователей
│   └── ...
└── static/               # Статические файлы
```

## Установка и запуск

### Локальная установка

1. **Клонируйте репозиторий**
   ```bash
   git clone https://github.com/yourusername/ai-community-bot.git
   cd ai-community-bot
   ```

2. **Создайте виртуальное окружение**
   ```bash
   python -m venv venv
   source venv/bin/activate  # На Windows: venv\\Scripts\\activate
   ```

3. **Установите зависимости**
   ```bash
   pip install -r requirements.txt
   ```

4. **Настройте базу данных PostgreSQL**
   ```bash
   createdb ai_community_bot
   ```

5. **Создайте файл `.env`**
   ```env
   BOT_TOKEN=your_bot_token_here
   DATABASE_URL=postgresql://user:password@localhost/ai_community_bot
   SECRET_KEY=your_secret_key_here
   FLASK_ENV=development
   ```

6. **Запустите приложение**
   ```bash
   python app.py
   ```

### Получение токена бота

1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Введите название бота
4. Введите username бота (должен заканчиваться на `bot`)
5. Скопируйте токен в переменную `BOT_TOKEN`

## Деплой на Heroku

### Быстрый деплой

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Ручной деплой

1. **Установите Heroku CLI**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Windows
   # Скачайте с https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Войдите в Heroku**
   ```bash
   heroku login
   ```

3. **Создайте приложение**
   ```bash
   heroku create your-app-name
   ```

4. **Добавьте PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

5. **Установите переменные окружения**
   ```bash
   heroku config:set BOT_TOKEN=your_bot_token_here
   heroku config:set SECRET_KEY=your_secret_key_here
   ```

6. **Задеплойте приложение**
   ```bash
   git push heroku main
   ```

## Использование

### Веб-интерфейс

После запуска откройте в браузере:
- Локально: `http://localhost:5000`
- Heroku: `https://your-app-name.herokuapp.com`

### Telegram Bot

1. Найдите вашего бота в Telegram
2. Отправьте `/start` для регистрации
3. Используйте `/events` для просмотра мероприятий
4. Записывайтесь на мероприятия кнопками
5. Просматривайте свои регистрации через `/my_events`

## База данных

### Схема БД

```sql
-- Пользователи
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Мероприятия
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_datetime TIMESTAMP NOT NULL,
    webinar_link VARCHAR(500),
    max_participants INTEGER DEFAULT 100
);

-- Регистрации
CREATE TABLE registrations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_id INTEGER REFERENCES events(id),
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### Веб-интерфейс
- `GET /` - Главная страница
- `GET /users` - Список пользователей
- `GET /events` - Список мероприятий
- `POST /events/new` - Создание мероприятия
- `GET /events/<id>` - Детали мероприятия
- `GET /registrations` - Список регистраций

### API
- `GET /api/stats` - Статистика системы

## Разработка

### Добавление новых команд бота

1. Создайте метод в `bot/telegram_bot.py`
2. Добавьте обработчик в `setup_handlers()`
3. Обновите справку в `help_command()`

### Добавление страниц в CRM

1. Создайте route в `web/app.py`
2. Создайте HTML шаблон в `templates/`
3. Добавьте ссылку в навигацию `base.html`

## Мониторинг

### Логи Heroku
```bash
heroku logs --tail
```

### Подключение к БД
```bash
heroku pg:psql
```

## Безопасность

- Переменные окружения хранятся в `.env` (локально) или в Heroku Config Vars
- Токен бота не должен попадать в код
- Используйте HTTPS для продакшена
- Регулярно обновляйте зависимости

## Лицензия

MIT License - см. файл LICENSE

## Поддержка

Если у вас есть вопросы или проблемы:
1. Проверьте Issues на GitHub
2. Создайте новый Issue с подробным описанием
3. Включите логи ошибок и шаги для воспроизведения 