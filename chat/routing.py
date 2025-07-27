# chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_id>\w+_\d+_\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/chat/(?P<room_id>\w+)/$", consumers.ChatConsumer.as_asgi()),
]
