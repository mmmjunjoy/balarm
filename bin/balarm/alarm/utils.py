from datetime import datetime
from celery import current_app
from django.db import transaction
import time


def schedule_alarm(alarm):
    print("hi")
    delay = (alarm.date - datetime.now()).total_seconds()
    

    now = datetime.now()
    current_time = now.replace(second=0, microsecond=0)
     # 알림시간이 현재 시간보다, 전 시간 알림은 알림이 오지 않도록 변경
    if alarm.date <= current_time:
        print(f"이미 지난 알림입니다: {alarm.title} at {alarm.date}")
        return


    transaction.on_commit(lambda:(
        print(f"트랜잭션 커밋 후 celery 작업 실행 :{alarm.id} at {datetime.now()}"),
        current_app.send_task(
            'alarm.tasks.send_alarm_notification',
            args = [alarm.id],
            countdown = delay
        ),

        print(f"celery 작업 호출 완료:{alarm.id} at {datetime.now()}")
    ))