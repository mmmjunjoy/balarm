import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class AlarmConsumer(AsyncWebsocketConsumer):
    async def connect(self):
       
        self.user_id = self.scope['query_string'].decode().split('user_id=')[1]
        self.room_group_name = f"user_{self.user_id}_notifications"
        
        await self.set_user_web_active(1)
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print("웹소켓 연결되었습니다.")

    
    # disconnect 시점에, data를 받고 , 방 삭제
    async def receive(self, text_data):
        data = json.loads(text_data)
        if 'disconnect_user' in data:
            self.user_id = data['disconnect_user']
            self.room_group_name = f"user_{self.user_id}_notifications"
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print(f"웹소켓 연결이 종료되었습니다: {self.room_group_name}")
    
    # async def disconnect(self, close_code):

    #     self.user_id = self.scope['query_string'].decode().split('user_id=')[1]
    #     self.room_group_name = f"user_{self.user_id}_notifications"

    #     await self.set_user_web_active(0)

    #     await self.channel_layer.group_discard(
    #         self.room_group_name,
    #         self.channel_name
    #     )

    #     print("웹소켓 연결이 끊겼습니다.")
    
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