from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Alarm
from balarm.celery import app
from asgiref.sync import sync_to_async
import asyncio
import time

# #비동기로 orm 관리를 해주기 위하여 
# async def fetch_alarm(alarm_id):
#     alarm = await sync_to_async(Alarm.objects.get)(id=alarm_id)
#     return alarm

# @shared_task
# # @app.task(queue='test_queue')
# def send_alarm_notification(alarm_id):
#     print(f"알림전송:{alarm_id}")

#     try:
#         alarm = asyncio.run(fetch_alarm(alarm_id))
#         # alarm = Alarm.objects.get(id=alarm_id)
#         user_id = alarm.id_user.id
#         channel_layer = get_channel_layer()
#         room_group_name = f"user_{user_id}_notifications"

#         async_to_sync(channel_layer.group_send)(
#             "room_group_name",
#             {
#                 "type":"send_alarm",
#                 "message":f"{alarm.title}"
#             }
#         )

#         print(f"알림 전송 성공: {alarm.title}")
    
#     except Alarm.DoesNotExist:
#         print("해당 알림을 찾을 수 없습니다")


#2

def fetch_alarm(alarm_id):
    for _ in range(5):  # 5번 재시도
        try:
            alarm = Alarm.objects.get(id=alarm_id)
            return alarm
        except Alarm.DoesNotExist:
            print("해당 알림을 찾을 수 없습니다. 재시도 중...")
            time.sleep(1)  # 1초 대기 후 재시도
    return None

@shared_task
def send_alarm_notification(alarm_id):
    try:
        print(f"Celery 작업 시작:알림 id = {alarm_id}")
    
    except Exception as e:
        print(f"ERROR -> : {e}")
        raise


    # 동기적으로 fetch_alarm을 호출하도록 수정
    alarm = fetch_alarm(alarm_id)
    
    if not alarm:
        print("알림을 찾을 수 없습니다.")
        return

    user_id = alarm.id_user.id
    channel_layer = get_channel_layer()
    room_group_name = f"user_{user_id}_notifications"

    try:
        # 동기 함수로 group_send를 호출
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "send_alarm",
                "message": f"{alarm.title}"
            }
        )
        print(f"알림 전송 성공: {alarm.title}")

    except Exception as e:
        print(f"알림 전송 실패: {str(e)}")


