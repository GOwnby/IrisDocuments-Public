import os
import django

#from channels.auth import AuthMiddlewareStack
#from channels.routing import ProtocolTypeRouter, URLRouter
#from channels.security.websocket import AllowedHostsOriginValidator
#from Home import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SecureSign.settings')

#from django.core.asgi import get_asgi_application
#from channels.routing import get_default_application
import importlib

django.setup()
path, name = 'SecureSign.routing.application'.rsplit(".",1)
module = importlib.import_module(path)
application = getattr(module, name)
#application = get_default_application()

#application = ProtocolTypeRouter(
    #{
        #"http" : get_asgi_application() ,
        #"websocket" : AuthMiddlewareStack(URLRouter(routing.websocket_urlpatterns))
    #}
#)