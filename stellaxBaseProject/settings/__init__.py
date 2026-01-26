"""
Django settings module.

Automatically selects the appropriate settings based on environment:
- DJANGO_SETTINGS_MODULE env var (if set explicitly)
- RENDER env var -> production
- Otherwise -> development
"""

import os

# Determine which settings to use
env = os.environ.get("DJANGO_ENV", "").lower()

if env == "production" or "RENDER" in os.environ:
    from .production import *  # noqa: F401, F403
elif env == "test":
    from .test import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
