"""
ASGI config for teachkaBaseProject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teachkaBaseProject.settings")
# Note: The settings module auto-detects environment (dev/prod/test)

application = get_asgi_application()
