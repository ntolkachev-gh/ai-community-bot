# Миграция на Heroku

## Проблема
Если вы получаете ошибку:
```
column users.full_name does not exist
```

Это означает, что в продакшн базе данных на Heroku отсутствуют новые колонки, добавленные в версии 2.0.0.

## Решение

### Вариант 1: Автоматическая миграция (рекомендуется)
Новый код автоматически запустит миграцию при следующем деплое. Просто запушите изменения:

```bash
git push heroku main
```

### Вариант 2: Ручная миграция
Если нужно запустить миграцию немедленно:

```bash
# Подключитесь к Heroku и запустите миграцию
heroku run python heroku_migrate.py
```

### Вариант 3: Через Heroku CLI
```bash
# Подключитесь к PostgreSQL
heroku pg:psql

# Выполните SQL команды вручную:
ALTER TABLE users ADD COLUMN full_name VARCHAR(200);
ALTER TABLE users ADD COLUMN company VARCHAR(200);
ALTER TABLE users ADD COLUMN role VARCHAR(200);
ALTER TABLE users ADD COLUMN ai_experience VARCHAR(100);
ALTER TABLE users ADD COLUMN is_profile_complete INTEGER DEFAULT 0;

# Обновите существующих пользователей
UPDATE users SET is_profile_complete = 0 WHERE is_profile_complete IS NULL;
UPDATE users SET full_name = CASE 
    WHEN first_name IS NOT NULL AND last_name IS NOT NULL 
    THEN first_name || ' ' || last_name
    WHEN first_name IS NOT NULL 
    THEN first_name
    ELSE NULL
END
WHERE full_name IS NULL;

# Выйдите из psql
\q
```

## Проверка
После миграции проверьте, что все работает:

```bash
# Проверьте логи
heroku logs --tail

# Проверьте статус приложения
heroku ps
```

## Новые возможности
После успешной миграции ваш бот будет поддерживать:
- Расширенную регистрацию пользователей
- Сбор информации о компании, роли и опыте с ИИ
- Команду `/profile` для просмотра профиля
- Улучшенный веб-интерфейс с детальной информацией

## Поддержка
Если у вас возникли проблемы, создайте Issue в репозитории с подробным описанием ошибки. 