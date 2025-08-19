# API Документация

## Получение списка событий

### Endpoint
```
GET /api/events
```

### Авторизация
Требуется Basic Authentication:
- Username: значение переменной `API_USERNAME` (по умолчанию: `admin`)
- Password: значение переменной `API_PASSWORD` (по умолчанию: `ai-community-1`)

### Параметры запроса
- `page` (необязательный): номер страницы, по умолчанию 1
- `per_page` (необязательный): количество событий на страницу, по умолчанию 50, максимум 100

### Пример запроса с curl
```bash
curl -X GET "http://89.169.154.41/api/events?page=1&per_page=10" \
     -u admin:ai-community-1
```

### Пример запроса с Python
```python
import requests
from requests.auth import HTTPBasicAuth

url = "http://89.169.154.41/api/events"
auth = HTTPBasicAuth('admin', 'ai-community-1')
params = {'page': 1, 'per_page': 10}

response = requests.get(url, auth=auth, params=params)
data = response.json()

print(f"Всего событий: {data['pagination']['total']}")
for event in data['events']:
    print(f"- {event['title']} ({event['event_datetime']})")
```

### Ответ
```json
{
  "events": [
    {
      "id": 1,
      "title": "Название события",
      "description": "Описание события",
      "event_datetime": "2024-01-15T18:00:00",
      "webinar_link": "https://example.com/webinar",
      "max_participants": 100,
      "image_url": "https://example.com/image.jpg",
      "registered_participants": 25,
      "available_spots": 75,
      "is_full": false
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1,
    "pages": 1
  }
}
```

### Статусы ответов
- `200 OK`: Успешный запрос
- `401 Unauthorized`: Неверные учетные данные или отсутствие авторизации

### Настройка учетных данных
Установите переменные окружения:
```bash
export API_USERNAME=your_username
export API_PASSWORD=your_secure_password
```

Или добавьте их в `.env` файл:
```
API_USERNAME=your_username
API_PASSWORD=your_secure_password
```