from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTING_MODULE', 'balarm.settings')

app = Celery('balarm')

app.config_from_object('django.conf:settings',namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.imports = ('alarm.tasks',)


@app.task(bind=True)
def debung_task(self):
    print(f'Request: {self.request!r}')
