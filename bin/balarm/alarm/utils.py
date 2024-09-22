from datetime import datetime
from celery import current_app
from django.db import transaction
import time


def schedule_alarm(alarm):
    print("hi")
    delay = (alarm.date - datetime.now()).total_seconds()
    

    transaction.on_commit(lambda:(
        print(f"트랜잭션 커밋 후 celery 작업 실행 :{alarm.id} at {datetime.now()}"),
        current_app.send_task(
            'alarm.tasks.send_alarm_notification',
            args = [alarm.id],
            countdown = delay
        )
    ))