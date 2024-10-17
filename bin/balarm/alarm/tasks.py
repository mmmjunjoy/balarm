from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Alarm ,Userbungry
from balarm.celery import app
from asgiref.sync import sync_to_async
import asyncio
import time
from pyfcm import FCMNotification  # 푸시 알림 모듈

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

            api_key = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDag3kKK+H+jkvI\nGa0k6irpVJiEgtGopa3WXMQyuutqLAwg3PW4E2xaRTZfxbEi2ra4EVgmh84EqhNM\nANeFMAK6nB+eJvOTSM9ty5QRH0LzqwPj9vN53VsJH3HNSkRdU7cBEJa5FYakkfLy\n3dBbCNPs8eS33lRRmYMnnpq8olXbsQzGS/aKSBP9Snmxq8PYGujTeItviQ0e2Rxm\n/XyB52ttXRaZar3yya13N/aXemMgsK3r4Axu8yoXz4QGroWfhxQpJKV3BPP4uOiD\nwdkPB9Mq6KIyAOHRPVNs0DGUdA8H3Bkt49X+BDWjbaXhvbYBKhFf4UuVHyI3NWRN\nD6ZxWFLXAgMBAAECggEAVUir9KLU9R+/hw0ybS5x6hiI4GsYfiyP0RLqxmv61rjz\nUN48jwgRqZfK1Y1YieR4HRYz4/HsIBjrKCZJ96MZ5ZBqrLTCK1FnGBC1LQuY+3Zb\nMd2gAIe68LAToA6k6RHz4pgBY6J5pwCJpG2bVPR4lkmAvZyqJyD1tgBqn0Xyoafb\nK2DGXSBaupYKWng+EWe4BUFA0G+H2m/3QO8UnrW0TaJhLZ/wjbcxiaZhjf+kNIev\n/cPyK1pwwlLs3YMkNso9wYXZv3KpPepYV30iq0J3CAXZzipE44Or+WAQMk48gxxG\nuEmUYwuw3Tp8NcmymHL0PibHJ4ik/kHs7/wMDTqThQKBgQD2+5kXKNAoC2mwTgVh\n4XMNLobn0HNXr2a0E9WNRSOKLkbLyn42Bol2UdgWcK1gYDTSvpO2gl9DOligpJDK\npOMJqPb1W7uAcZ6b74qZNsKtyaGnsvre5SNgn55WIP+5ZjNsFykRjnV1gOgosAMK\nEBNidnVhzfXrXaBl+2fA+tV75QKBgQDifcoo43IHNVT/+FGfANdkxlWOr9xFyXG9\nc8uJUFkuHNOT/BXwXngjzSLfT+NsKzCDPlpnMhXDxynxE0zEg0QXCJjTP4SskywI\nDZaF2DqN4LxIovuh1Ti24sCi7MHJT2bkf+t/GzYEU/MPyiXq+m0LOnB6ndLC6d3S\nmSBDFrwACwKBgQDNkN17xDF0kwM1hcq/DBlpaEdKnFnUKp5N1ZBR07Df6uJr7i8c\nIla5TyeOjdwQMiLlIU/qgRpu5xorIq2MrK53NNXPo7ktD+RWn4p5OXXRldfhr3tU\nl9zZKCFuSGrv0duM5L3+6dZjpZYVf2IYNwcbVcMfU4CSlMvS9ewGV//l7QKBgFR+\neumQGF0KD2DCwahgxvooZ4iooLNEOHNl/HuIhwyF4oSlmYWnqIgqoiTPB9e1sQ51\nN4KiE66K4WG3Qn9ZPRCeu2yrmJJNATMr5oieJxIA0h0C+H7iLZtEsnrVemHghlEe\nS7uKajdpHhc44bZsoDt9HLMRp6vhVUiYqYl9tLsLAoGAdfn6xqH0U9jJ4W9VEIUg\nvskY6aIjtcawBXajK7UTihjD9isf024kKasuNJT57kaYSQ5jW+mox4WZPVLhhsRD\nyxdnIWTIpJjPDVT/P5dDhCSPZt5cHM5MwnRjgxN9TkVwhOgWZlo3vmjklGjo4PnM\nOPEIoAq3I9Tt/dQtc5bNoFM"
            # 푸시 알림 전송 로직
            push_service = FCMNotification(api_key , project_id)
            
            print("api_key 문제?")

            message_title = alarm.title
            message_body = alarm.date.isoformat()

            print("message ->>" , message_title , message_body)

            result = push_service.notify_single_device(
                registration_id=user.fcm_token,
                message_title=message_title,
                message_body=message_body
            )
            
            print(f"푸시 알림 전송 성공: {result}")
        except Exception as e:
            print(f"푸시 알림 전송 실패: {str(e)}")
    else:
        print("유효하지 않은 유저 상태 또는 유저를 찾을 수 없습니다.")





