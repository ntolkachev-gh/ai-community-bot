import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import asyncio

logger = logging.getLogger(__name__)

class NotificationScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = BackgroundScheduler()
        
    def start(self):
        """Запуск планировщика"""
        self.scheduler.start()
        logger.info("Планировщик напоминаний запущен")
    
    def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        logger.info("Планировщик напоминаний остановлен")
    
    def add_reminder(self, user_id, event):
        """Добавить напоминание за день до мероприятия"""
        reminder_time = event.event_datetime - timedelta(days=1)
        
        # Проверяем, что напоминание не в прошлом
        if reminder_time > datetime.utcnow():
            job_id = f"reminder_{user_id}_{event.id}"
            
            self.scheduler.add_job(
                func=self._send_reminder,
                trigger=DateTrigger(run_date=reminder_time),
                args=[user_id, event],
                id=job_id,
                replace_existing=True
            )
            
            logger.info(f"Напоминание добавлено для пользователя {user_id} на {reminder_time}")
    
    def remove_reminder(self, user_id, event_id):
        """Удалить напоминание"""
        job_id = f"reminder_{user_id}_{event_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Напоминание удалено для пользователя {user_id}")
        except Exception as e:
            logger.warning(f"Не удалось удалить напоминание: {e}")
    
    def _send_reminder(self, user_id, event):
        """Отправить напоминание пользователю"""
        try:
            message = f"⏰ Напоминание о мероприятии!\n\n"
            message += f"📅 {event.title}\n"
            message += f"🕐 Завтра в {event.event_datetime.strftime('%H:%M')}\n"
            message += f"📝 {event.description}\n\n"
            
            if event.webinar_link:
                message += f"🔗 Ссылка на мероприятие: {event.webinar_link}\n\n"
            
            message += "Не забудьте принять участие!"
            
            # Отправка сообщения
            asyncio.create_task(self.bot.send_message(chat_id=user_id, text=message))
            
            logger.info(f"Напоминание отправлено пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания: {e}") 