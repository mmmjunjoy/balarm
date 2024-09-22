from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient , APITestCase 
from django.test import TransactionTestCase
from rest_framework import status
from .models import Userbungry, Alarm
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
import sys
from django.db import transaction
from django.utils.timezone import now,timedelta, datetime
from alarm.tasks import send_alarm_notification
from django.utils.timezone import make_aware
import time
from channels.testing import WebsocketCommunicator , ChannelsLiveServerTestCase
from alarm.routing import websocket_urlpatterns 
from balarm.asgi import application
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.test import override_settings

Userbungry = get_user_model()


#1 - 일단, 지금 post 한 알림을 찾는것 부터가 에러. 
class AlarmTest(TransactionTestCase):
    def setUp(self):
        # 유저 A와 B 생성
        # 생성하지말고, 미리 생성되어있는 애를 가지고 올까?
       self.user_a = Userbungry.objects.create(b_id='user_a', password='password123', nickname='User A')
       self.client = APIClient() 

       try:
            user_a_db = Userbungry.objects.get(b_id='user_a')
            print(f"유저 A 생성 확인: {user_a_db.nickname}, ID: {user_a_db.id}")


       except Userbungry.DoesNotExist:
            self.fail("유저 A  생성되지 않았습니다.")


    def test_alarm(self):
        # 유저 A로 로그인하고 알림 생성
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(reverse('alarm-list'), {
            'title': 'testalarm',
            'date': datetime.now() + timedelta(seconds=10),  # 5초 후 알림
            'detail': 'testdetail'
        })

        transaction.commit()

        time.sleep(40)

#2
class AlarmNotificationTest(ChannelsLiveServerTestCase):
    def setUp(self):
        # 유저 A와 B 생성
        # 생성하지말고, 미리 생성되어있는 애를 가지고 올까?
       self.user_a = Userbungry.objects.create(b_id='user_a', password='password123', nickname='User A')
       self.user_b = Userbungry.objects.create(b_id='user_b', password='password456', nickname='User B')
       self.client = APIClient() 

       try:
            user_a_db = Userbungry.objects.get(b_id='user_a')
            user_b_db = Userbungry.objects.get(b_id='user_b')
            print(f"유저 A 생성 확인: {user_a_db.nickname}, ID: {user_a_db.id}")
            print(f"유저 B 생성 확인: {user_b_db.nickname}, ID: {user_b_db.id}")

       except Userbungry.DoesNotExist:
            self.fail("유저 A 또는 B가 생성되지 않았습니다.")


    async def test_alarm_send_to_user_a_only(self):
        # 유저 A로 로그인하고 알림 생성
        self.client.force_authenticate(user=self.user_a)
        response = await sync_to_async (self.client.post)(reverse('alarm-list'), {
            'title': 'testalarm',
            'date': datetime.now() + timedelta(seconds=10),  # 5초 후 알림
            'detail': 'testdetail'
        })
        print("여기서 오류지")   

        alarm_a = await sync_to_async(Alarm.objects.get)(title="testalarm")

    
        print(f"유저 a가 생성한 알림 잘 들어갔는지 확인:{alarm_a.date}")

        print("response 확인" , response.status_code)

        self.assertEqual(response.status_code, 201)
        alarm_id = response.data['id']
     

        # 유저 A와 B 각각의 Websocket 연결 설정
        communicator_a = WebsocketCommunicator(application, f"/ws/alarm/")
        print("commuicator_a", communicator_a)

        communicator_a.scope['user'] = self.user_a
        print("communicator _user" , communicator_a.scope['user'])

        connected_a, subprotocol_a = await communicator_a.connect()
        print("connect check", connected_a)


        self.assertTrue(connected_a)

        communicator_b = WebsocketCommunicator(application, f"/ws/alarm/")
        communicator_b.scope['user'] = self.user_b
        connected_b, subprotocol_b = await communicator_b.connect()
        self.assertTrue(connected_b)

        # Celery 작업을 예약 시간(ETA)으로 실행
        # send_alarm_notification.apply_async((alarm_id,), eta=datetime.now() + timedelta(seconds=20))




        # 일정 시간 대기 (ETA가 지나 알림 전송이 이루어질 때까지)
        try:
            response_a = await communicator_a.receive_json_from(timeout=30)
            # self.assertIn('testalarm', response_a['message'])
        except :
            self.fail("a알림이 예상 시간 내에 수신되지 않았습니다.")

        # A 사용자에게 알림 전송 확인
        response_a = await communicator_a.receive_json_from()
        self.assertIn('testalarm', response_a['message'])

        # B 사용자에게는 알림이 없어야 함
        try:
            await communicator_b.receive_nothing(timeout=10)
        except :
            self.fail("B 사용자에게 알림이 잘못 전송되었습니다.")

        # Websocket 연결 종료
        await communicator_a.disconnect()
        await communicator_b.disconnect()






#3
# @override_settings(CELERY_TASK_ALWAYS_EAGER =False)
# class AlarmNotificationTest(ChannelsLiveServerTestCase):

#     def setUp(self):
#         self.user_a = Userbungry.objects.create(b_id='user_a', password='password123', nickname='User A')
#         self.user_b = Userbungry.objects.create(b_id='user_b', password='password456', nickname='User B')
#         self.client = APIClient()

#         # 생성된 유저 DB에서 확인
#         self.user_a_db = Userbungry.objects.get(b_id='user_a')
#         self.user_b_db = Userbungry.objects.get(b_id='user_b')

#         print(f"유저 A 생성 확인: {self.user_a_db.id}")
#         print(f"유저 B 생성 확인: {self.user_b_db.id}")

#     @database_sync_to_async
#     def force_commit(self):
#         transaction.commit()

#     async def test_alarm_send_to_user_a_only(self):
#         # 유저 A로 로그인하고 알림 생성
#         self.client.force_authenticate(user=self.user_a)
#         response = await sync_to_async(self.client.post)(
#             reverse('alarm-list'), {
#                 'title': 'testalarm',
#                 'date': datetime.now() + timedelta(seconds=30),
#                 'detail': 'testdetail'
#             }
#         )

#         # 트랜잭션 강제 커밋
#         await self.force_commit()

#         print("여기서 오류지")
#         alarm_a = await sync_to_async(Alarm.objects.get)(title="testalarm")
#         print(f"유저 A가 생성한 알림 잘 들어갔는지 확인: {alarm_a.date}")

#         print(f"response 확인 : {response.status_code}")
#         self.assertEqual(response.status_code, 201)
#         alarm_id = response.data['id']

#         # Celery 작업이 완료될 때까지 대기
#         time.sleep(50)
#         print("Celery 작업이 완료된 후 추가 확인")
