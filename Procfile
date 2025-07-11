release: python init_production_db.py
web: gunicorn --bind 0.0.0.0:$PORT wsgi:app
worker: python bot_worker.py
