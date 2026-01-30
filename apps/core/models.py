"""
Base models for Teachka applications.

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


class Member(TimestampedModel):
    """
    A member belonging to a group.

    This is the single source of truth for group members across all apps.
    The karma-related fields (positive_data, negative_data, totals) are used
    by the point_system app but stored here for simplicity.
    """

    group = models.ForeignKey(
        "group_maker.GroupCreationModel",
        on_delete=models.CASCADE,
        related_name="members",
    )
    name = models.CharField(max_length=50)

    # Karma/points data (used by point_system app)
    positive_data = models.JSONField(default=dict)
    negative_data = models.JSONField(default=dict)
    positive_total = models.IntegerField(default=0, blank=True)
    negative_total = models.IntegerField(default=0, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} ({self.group.title})"
