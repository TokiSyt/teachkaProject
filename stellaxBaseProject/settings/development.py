"""
Development Django settings for Stellax project.

DEBUG=True, verbose logging, relaxed security.
"""

from .base import *  # noqa: F401, F403

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "dev-secret-key-not-for-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


# Development-specific logging
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # type: ignore[index]  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # type: ignore[index]  # noqa: F405


# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
