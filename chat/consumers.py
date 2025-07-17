import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = f"chat_{self.scope['url_route']['kwargs']['room_id']}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Handles incoming WebSocket messages from client.
        Supports:
        - typing
        - message
        - read
        - call
        - webrtc_offer
        - webrtc_answer
        - ice_candidate
        """
        try:
            data = json.loads(text_data)
            event_type = data.get("type")

            if event_type == "typing":
                await self.channel_layer.group_send(
                    self.room_group_name, {
                        "type": "user_typing",
                        "user": self.scope['user'].username
                    }
                )

            elif event_type == "message":
                message = data.get("message")
                await self.channel_layer.group_send(
                    self.room_group_name, {
                        "type": "chat_message",
                        "message": message,
                        "user": self.scope['user'].username
                    }
                )

            elif event_type == "read":
                await self.channel_layer.group_send(
                    self.room_group_name, {
                        "type": "read_receipt",
                        "message_id": data["message_id"],
                        "user": self.scope["user"].username
                    }
                )

            elif event_type == "call":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "call_notification",
                        "call_type": data["call_type"],
                        "from_user": self.scope["user"].username,
                        "to_user": data["target_user"]
                    }
                )

            elif event_type == "webrtc_offer":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "webrtc_offer",
                        "offer": data["offer"],
                        "from": self.scope["user"].username
                    }
                )
            elif event_type == "webrtc_answer":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "webrtc_answer",
                        "answer": data["answer"],
                        "from": self.scope["user"].username
                    }
                )
            elif event_type == "ice_candidate":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "ice_candidate",
                        "candidate": data["candidate"],
                        "from": self.scope["user"].username
                    }
                )
            else:
                await self.send(text_data=json.dumps({"error": "Unknown event type"}))
        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))
    async def webrtc_offer(self, event):
        await self.send(text_data=json.dumps(event))

    async def webrtc_answer(self, event):
        await self.send(text_data=json.dumps(event))

    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps(event))

    # Typing indicator handler
    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "user": event["user"]
        }))

    # Message broadcast handler
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "user": event["user"]
        }))

    # Read receipt broadcast handler
    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            "type": "read",
            "message_id": event["message_id"],
            "user": event["user"]
        }))

    # Notification sent from Django signal on message save
    async def new_message_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "event": "new_message",
            "message": event["message"],
            "sender": event["sender"],
            "group_id": event["group_id"]
        }))

    # Notification when user joins or leaves group
    async def group_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "event": event["event"],  # "user_joined" or "user_left"
            "user_id": event["user_id"],
            "group_id": event["group_id"]
        }))

    # Video/audio call event notification
    async def call_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "event": "call",
            "call_type": event["call_type"],  # video / audio
            "from_user": event["from_user"],
            "to_user": event["to_user"]
        }))
