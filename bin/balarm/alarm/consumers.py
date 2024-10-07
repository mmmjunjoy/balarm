import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AlarmConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        #1
        self.room_name ="alarm"
        self.room_group_name = "alarm_notifications"
        #2
        # user = self.scope['user']
        # print("user -> ", user.id)
        # self.room_group_name = f"user_{user.id}_notifications"
        

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print("웹소켓 연결되었습니다.")
        print("hihi")
    
    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    async def send_alarm(self, event):
        message = event['message']
        print(f"sending message - 웹소켓 : {message}")

        await self.send(text_data=json.dumps({
            'message':message
        }))