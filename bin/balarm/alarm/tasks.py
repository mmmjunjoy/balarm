from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Alarm ,Userbungry
from balarm.celery import app
from asgiref.sync import sync_to_async
import asyncio
import time
from pyfcm import FCMNotification  # 푸시 알림 모듈
import os
import json
from google.oauth2 import service_account
from datetime import datetime

#correct

def fetch_alarm(alarm_id):
    for _ in range(5):  # 5번 재시도
        try:
            alarm = Alarm.objects.get(id=alarm_id)
            return alarm
        except Alarm.DoesNotExist:
            print("해당 알림을 찾을 수 없습니다. 재시도 중...")
            time.sleep(1)  # 1초 대기 후 재시도
    return None


def get_user_web_active_status(user_id):
    """
    유저의 web_active 상태를 반환합니다.
    """
    try:
        user = Userbungry.objects.get(id=user_id)
        return user.web_active
    except Userbungry.DoesNotExist:
        print(f"유저를 찾을 수 없습니다. id: {user_id}")
        return None

@shared_task
def send_alarm_notification(alarm_id):
    try:
        print(f"Celery 작업 시작:알림 id = {alarm_id}")
    
    except Exception as e:
        print(f"error:{e}")
        raise


    # 동기적으로 fetch_alarm을 호출하도록 수정
    alarm = fetch_alarm(alarm_id)
    
    if not alarm:
        print("알림을 찾을 수 없습니다.")
        return

    user_id = alarm.id_user.id
    channel_layer = get_channel_layer()
    room_group_name = f"user_{user_id}_notifications"
    print("이방의 유저 아이디는 ->", user_id)
    # room_group_name = "alarm_notifications"


    # <----병행 처리----->
    
    # 유저의 web_active 상태 확인
    web_active = get_user_web_active_status(user_id)
    
    if web_active == 1:
        # 웹소켓으로 알림 전송
        try:
            # 동기 함수로 group_send를 호출
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    "type": "send_alarm",
                    "message": f"{alarm.title}",
                    'time': f"{alarm.date}"
                }
            )
            print(f"웹소켓 알림 전송 성공: {alarm.title} ")

        except Exception as e:
            print(f"웹소켓 알림 전송 실패: {str(e)}")

    elif web_active == 0:
        # 푸시 알림 전송
        try:
            user = Userbungry.objects.get(id=user_id)
            
            if not user.fcm_token:
                print("FCM 토큰이 없습니다.")
                return
            

            if user.device_type == 'ios':
                api_key = "AIzaSyAwyOfEI7-rNz7lB4VeX3L_azMg1Pbu2TE"
            
            elif user.device_type == 'android':
                api_key = "AIzaSyA9wog-McyIrpg87egkxCcVahpaV0Ne_dg"
            
            else:
                print("알 수 없는 Device_type")
                return

            project_id = "bungry-alarm"

    
            # 푸시 알림 전송 로직
            gcp_json_credentials_dict = json.loads(os.getenv('GCP_CREDENTIALS', None))
            credentials = service_account.Credentials.from_service_account_info(gcp_json_credentials_dict, scopes=['https://www.googleapis.com/auth/firebase.messaging'])

            fcm = FCMNotification(service_account_file=None, credentials=credentials, project_id=project_id)
                        
            print("api_key 문제?")


            notification_title = f'"{alarm.title}" 할 시간 :)'


            iso_string = alarm.date.isoformat()
            time_only = iso_string[11:16]
            notification_body = f"{time_only}!!!"


            print("message ->>" , notification_title , notification_body)

            result = fcm.notify(
                fcm_token=user.fcm_token,
                notification_title=notification_title,
                notification_body=notification_body
            )

            print(f"푸시 알림 전송 성공: {result}")
        except Exception as e:
            print(f"푸시 알림 전송 실패: {str(e)}")
    else:
        print("유효하지 않은 유저 상태 또는 유저를 찾을 수 없습니다.")





