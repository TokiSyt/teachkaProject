"""
Base models for Stellax applications.

These abstract models provide common functionality across all apps.
"""

from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    """
    Abstract model that provides self-updating created_at and updated_at fields.

    Usage:
        class MyModel(TimestampedModel):
            name = models.CharField(max_length=100)
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserOwnedModel(TimestampedModel):
    """
    Abstract model for resources owned by a user.

    Extends TimestampedModel with a user foreign key.

    Usage:
        class MyModel(UserOwnedModel):
            name = models.CharField(max_length=100)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)ss",
    )

    class Meta:
        abstract = True
