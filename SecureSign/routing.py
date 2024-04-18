from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from . import consumers

application = ProtocolTypeRouter(
    {
        "http" : get_asgi_application(),
        "websocket" : AuthMiddlewareStack(URLRouter([
            re_path("chat/stream/", consumers.ChatConsumer.as_asgi()),
            re_path("OpenChat/", consumers.OpenChatConsumer.as_asgi()),
            re_path("RoomManager/", consumers.RoomManagementDaemon.as_asgi()),
            re_path("AlertAgent/", consumers.AlertSupportAgent.as_asgi())
            ]))
    }
)

#websocket_urlpatterns = [re_path("", consumers.ChatConsumer),]