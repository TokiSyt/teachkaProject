"""
Test Django settings for Stellax project.

Fast password hasher, in-memory database options.
"""

from .base import *  # noqa: F401, F403

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "test-secret-key-for-testing-only"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]


# Use fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


# Disable logging during tests (optional: set to WARNING to see warnings)
LOGGING["root"]["level"] = "WARNING"  # type: ignore[index]  # noqa: F405
LOGGING["loggers"]["apps"]["handlers"] = ["console"]  # type: ignore[index]  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "WARNING"  # type: ignore[index]  # noqa: F405


# Use in-memory SQLite for faster tests (optional, can use PostgreSQL if needed)
# Uncomment below to use SQLite for tests:
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": ":memory:",
#     }
# }


# Email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
