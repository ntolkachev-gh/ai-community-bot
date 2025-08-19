from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from database.models import User, Event, Registration, get_db
from sqlalchemy.orm import joinedload
from config import Config
import base64
from functools import wraps

def create_app():
    import os
    # Указываем путь к шаблонам относительно корня проекта
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(Config)
    
    def check_basic_auth(username, password):
        """Проверка Basic авторизации"""
        return username == Config.API_USERNAME and password == Config.API_PASSWORD
    
    def authenticate():
        """Отправка запроса авторизации"""
        return jsonify({'error': 'Authentication required'}), 401, {'WWW-Authenticate': 'Basic realm="API"'}
    
    def requires_auth(f):
        """Декоратор для проверки Basic авторизации"""
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_basic_auth(auth.username, auth.password):
                return authenticate()
            return f(*args, **kwargs)
        return decorated
    
    @app.route('/')
    def index():
        """Главная страница"""
        db = next(get_db())
        try:
            users_count = db.query(User).count()
            completed_profiles_count = db.query(User).filter(User.is_profile_complete == 1).count()
            events_count = db.query(Event).count()
            registrations_count = db.query(Registration).count()
            
            recent_registrations = db.query(Registration).options(
                joinedload(Registration.user),
                joinedload(Registration.event)
            ).order_by(Registration.registration_time.desc()).limit(5).all()
            
            return render_template('index.html', 
                                 users_count=users_count,
                                 completed_profiles_count=completed_profiles_count,
                                 events_count=events_count,
                                 registrations_count=registrations_count,
                                 recent_registrations=recent_registrations)
        finally:
            db.close()
    
    @app.route('/users')
    def users():
        """Страница пользователей"""
        db = next(get_db())
        try:
            users_list = db.query(User).order_by(User.registration_date.desc()).all()
            return render_template('users.html', users=users_list)
        finally:
            db.close()
    
    @app.route('/events')
    def events():
        """Страница мероприятий"""
        db = next(get_db())
        try:
            events_list = db.query(Event).order_by(Event.event_datetime.desc()).all()
            return render_template('events.html', events=events_list)
        finally:
            db.close()
    
    @app.route('/events/new', methods=['GET', 'POST'])
    def new_event():
        """Создание нового мероприятия"""
        if request.method == 'POST':
            db = next(get_db())
            try:
                event = Event(
                    title=request.form['title'],
                    description=request.form['description'],
                    event_datetime=datetime.strptime(request.form['event_datetime'], '%Y-%m-%dT%H:%M'),
                    webinar_link=request.form.get('webinar_link'),
                    max_participants=int(request.form.get('max_participants', 100)),
                    image_url=request.form.get('image_url') if request.form.get('image_url') else None
                )
                db.add(event)
                db.commit()
                flash('Мероприятие создано успешно!', 'success')
                return redirect(url_for('events'))
            except Exception as e:
                flash(f'Ошибка создания мероприятия: {str(e)}', 'error')
            finally:
                db.close()
        
        return render_template('new_event.html')
    
    @app.route('/events/<int:event_id>')
    def event_detail(event_id):
        """Детали мероприятия"""
        db = next(get_db())
        try:
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                flash('Мероприятие не найдено', 'error')
                return redirect(url_for('events'))
            
            registrations = db.query(Registration).options(
                joinedload(Registration.user)
            ).filter(Registration.event_id == event_id).all()
            
            return render_template('event_detail.html', event=event, registrations=registrations)
        finally:
            db.close()
    
    @app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
    def edit_event(event_id):
        """Редактирование мероприятия"""
        db = next(get_db())
        try:
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                flash('Мероприятие не найдено', 'error')
                return redirect(url_for('events'))
            
            if request.method == 'POST':
                event.title = request.form['title']
                event.description = request.form['description']
                event.event_datetime = datetime.strptime(request.form['event_datetime'], '%Y-%m-%dT%H:%M')
                event.webinar_link = request.form.get('webinar_link')
                event.max_participants = int(request.form.get('max_participants', 100))
                event.image_url = request.form.get('image_url') if request.form.get('image_url') else None
                
                db.commit()
                flash('Мероприятие обновлено успешно!', 'success')
                return redirect(url_for('event_detail', event_id=event_id))
            
            return render_template('edit_event.html', event=event)
        finally:
            db.close()
    
    @app.route('/events/<int:event_id>/delete', methods=['POST'])
    def delete_event(event_id):
        """Удаление мероприятия"""
        db = next(get_db())
        try:
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                flash('Мероприятие не найдено', 'error')
                return redirect(url_for('events'))
            
            # Удаляем все регистрации
            db.query(Registration).filter(Registration.event_id == event_id).delete()
            db.delete(event)
            db.commit()
            
            flash('Мероприятие удалено успешно!', 'success')
            return redirect(url_for('events'))
        finally:
            db.close()
    
    @app.route('/registrations')
    def registrations():
        """Страница регистраций"""
        db = next(get_db())
        try:
            registrations_list = db.query(Registration).options(
                joinedload(Registration.user),
                joinedload(Registration.event)
            ).order_by(Registration.registration_time.desc()).all()
            
            return render_template('registrations.html', registrations=registrations_list)
        finally:
            db.close()
    
    @app.route('/api/stats')
    def api_stats():
        """API для получения статистики"""
        db = next(get_db())
        try:
            users_count = db.query(User).count()
            events_count = db.query(Event).count()
            registrations_count = db.query(Registration).count()
            
            return jsonify({
                'users': users_count,
                'events': events_count,
                'registrations': registrations_count
            })
        finally:
            db.close()
    
    @app.route('/api/events')
    @requires_auth
    def api_events():
        """API для получения списка событий с Basic авторизацией"""
        db = next(get_db())
        try:
            events_query = db.query(Event).order_by(Event.event_datetime.desc())
            
            # Поддержка пагинации
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            
            # Ограничиваем количество событий на страницу
            if per_page > 100:
                per_page = 100
            
            offset = (page - 1) * per_page
            events_list = events_query.offset(offset).limit(per_page).all()
            total_events = events_query.count()
            
            # Преобразуем события в JSON
            events_data = []
            for event in events_list:
                event_data = {
                    'id': event.id,
                    'title': event.title,
                    'description': event.description,
                    'event_datetime': event.event_datetime.isoformat() if event.event_datetime else None,
                    'webinar_link': event.webinar_link,
                    'max_participants': event.max_participants,
                    'image_url': event.image_url,
                    'registered_participants': len(event.registrations),
                    'available_spots': event.available_spots,
                    'is_full': event.is_full
                }
                events_data.append(event_data)
            
            return jsonify({
                'events': events_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_events,
                    'pages': (total_events + per_page - 1) // per_page
                }
            })
        finally:
            db.close()
    
    # Фильтры для шаблонов
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%d.%m.%Y %H:%M'):
        """Форматирование даты и времени"""
        if value is None:
            return ""
        return value.strftime(format)
    
    # Добавляем переменные в контекст шаблонов
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    return app 