import asyncio
from django.core.management.base import BaseCommand
from alarm.models import Alarm, Userbungry
from alarm.tasks import send_alarm_notification
from balarm.asgi import application
from channels.testing import WebsocketCommunicator
from django.utils import timezone
from asgiref.sync import sync_to_async

class Command(BaseCommand):
    help = '웹소켓과 알림 관련 테스트를 management command로 실행'

    def handle(self, *args, **kwargs):
        # 이벤트 루프를 생성하여 비동기 작업 실행
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run_test())

    async def run_test(self):
        # 유저 생성 (또는 기존 유저 사용)
        user_a = await sync_to_async(Userbungry.objects.create)(b_id='user_a', password='password123', nickname='User A')
        user_b = await sync_to_async(Userbungry.objects.create)(b_id='user_b', password='password456', nickname='User B')
        
        print(f"유저 A: {user_a.nickname}, 유저 B: {user_b.nickname}")
        
        # 알림 생성 및 POST 요청 시뮬레이션
        alarm = await sync_to_async(Alarm.objects.create)(
            title="testalarm",
            date=timezone.now() + timezone.timedelta(seconds=10),
            detail="testdetail",
            id_user=user_a  # 유저 A에게 알림을 보냄
        )
        print(f"알림 생성됨: {alarm.title}, 예정 시간: {alarm.date}")

        # Celery 작업 예약 (10초 후 실행)
        # send_alarm_notification.apply_async((alarm.id,), eta=timezone.now() + timezone.timedelta(seconds=10))

        # 웹소켓 설정
        communicator_a = WebsocketCommunicator(application, f"/ws/alarm/")
        # communicator_a.scope['user'] = user_a  # 유저 A 웹소켓 연결
        connected_a, subprotocol_a = await communicator_a.connect()
        print(f"유저 A 웹소켓 연결: {connected_a}")

        communicator_b = WebsocketCommunicator(application, f"/ws/alarm/")
        # communicator_b.scope['user'] = user_b  # 유저 B 웹소켓 연결
        connected_b, subprotocol_b = await communicator_b.connect()
        print(f"유저 B 웹소켓 연결: {connected_b}")

        # 일정 시간 대기 (ETA가 지나 Celery 작업이 실행될 때까지)
        print("알림 전송까지 대기 중...")
        await asyncio.sleep(15)

        # 유저 A에게 알림 전송 확인
        try:
            response_a = await communicator_a.receive_json_from(timeout=30)
            print(f"유저 A가 받은 메시지: {response_a['message']}")
        except:
            print("유저 A가 예상 시간 내에 알림을 수신하지 못했습니다.")
        
        # 유저 B에게는 알림이 없어야 함
        try:
            await communicator_b.receive_nothing(timeout=10)
            print("유저 B에게 알림이 전송되지 않음 (정상)")
        except:
            print("유저 B에게 알림이 잘못 전송되었습니다.")

        # Websocket 연결 종료
        await communicator_a.disconnect()
        await communicator_b.disconnect()