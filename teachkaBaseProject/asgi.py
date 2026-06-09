"""
ASGI config for teachkaBaseProject project.

Routes HTTP to the Django app and WebSocket to the Channels stack used by the
live quiz feature.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teachkaBaseProject.settings")
# Note: The settings module auto-detects environment (dev/prod/test)

# Initialise Django (populates the app registry) before importing anything that
# touches models, e.g. the WebSocket routing/consumers.
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from django.conf import settings  # noqa: E402

from apps.quizzmaker.routing import websocket_urlpatterns  # noqa: E402

websocket_app = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))

# In production, restrict WebSocket origins to ALLOWED_HOSTS. In dev (DEBUG) we
# skip this so players can join from other LAN devices (phones on the teacher's
# network), whose origin host isn't in ALLOWED_HOSTS.
if not settings.DEBUG:
    websocket_app = AllowedHostsOriginValidator(websocket_app)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": websocket_app,
    }
)
