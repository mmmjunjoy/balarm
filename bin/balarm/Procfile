web: cd bin/balarm && gunicorn balarm.wsgi:application --bind 0.0.0.0:8000 --log-file -
worker: cd bin/balarm && DJANGO_SETTINGS_MODULE=balarm.settings celery -A balarm worker --loglevel=debug
beat: cd bin/balarm && DJANGO_SETTINGS_MODULE=balarm.settings celery -A balarm beat -l info