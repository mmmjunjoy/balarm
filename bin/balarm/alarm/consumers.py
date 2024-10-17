import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class AlarmConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # #1
        # self.room_name ="alarm"
        # self.room_group_name = "alarm_notifications"
        #2
        # user = self.scope['user']
        # print("user -> ", user.id)
        # self.room_group_name = f"user_{user.id}_notifications"
        #3
        self.user_id = self.scope['query_string'].decode().split('user_id=')[1]
        self.room_group_name = f"user_{self.user_id}_notifications"
        
        await self.set_user_web_active(1)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print("웹소켓 연결되었습니다.")
        print("hihi")
    
    async def disconnect(self, close_code):

        self.user_id = self.scope['query_string'].decode().split('user_id=')[1]
        await self.set_user_web_active(0)

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    @database_sync_to_async
    def set_user_web_active(self, status):
        from .models import Userbungry 
        
        try:
            user = Userbungry.objects.get(id=self.user_id)
            user.web_active = status
            user.save()
        except Userbungry.DoesNotExist:
            print(f"유저 {self.user_id}를 찾을 수 없습니다. , web_active 변경 오류입니다.")
        
    async def send_alarm(self, event):
        message = event['message']
        time = event['time']
        print(f"sending message - 웹소켓 : {message}")

        await self.send(text_data=json.dumps({
            'message':message,
            'time':time
        }))