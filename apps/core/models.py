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

    # 30 colors evenly spaced around color wheel (12° apart) for smooth transitions at 24 and 30 members
    WHEEL_COLORS = [
        "#d84c4c",  # 0° Red
        "#db5537",  # 12°
        "#e46f2c",  # 24° Orange
        "#d3852d",  # 36°
        "#f3b93c",  # 48° Yellow-Orange
        "#f0c848",  # 60° Yellow
        "#dee05a",  # 72°
        "#c3e05a",  # 84° Lime
        "#a1cf4a",  # 96°
        "#83dd5a",  # 108° Green
        "#59db80",  # 120°
        "#58d8a3",  # 132° Green-Teal
        "#40d3c2",  # 144°
        "#5ac7d7",  # 156° Teal
        "#3fc2f1",  # 168° Cyan
        "#58a0df",  # 180°
        "#4973e9",  # 192° Sky Blue
        "#5b59e4",  # 204°
        "#9a43eb",  # 216° Blue
        "#a545e6",  # 228°
        "#cc5bdb",  # 240° Indigo
        "#e46eaf",  # 252°
        "#f170a6",  # 264° Purple
        "#f879c3",  # 276°
        "#f86c7f",  # 288° Magenta
        "#f0718c",  # 300°
        "#f87268",  # 312° Pink
        "#ee8267",  # 324°
        "#d9635a",  # 336°
        "#f76565",  # 348° Back toward Red
    ]

    group = models.ForeignKey(
        "group_maker.GroupCreationModel",
        on_delete=models.CASCADE,
        related_name="members",
    )
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, blank=True, default="")

    # Karma/points data (used by point_system app)
    positive_data = models.JSONField(default=dict)
    negative_data = models.JSONField(default=dict)
    positive_total = models.IntegerField(default=0, blank=True)
    negative_total = models.IntegerField(default=0, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} ({self.group.title})"

    def assign_color(self):
        """Assign a color based on how many members exist when this one is created."""
        if not self.color:
            existing_count = self.group.members.exclude(id=self.id).count()
            self.color = self.WHEEL_COLORS[existing_count % len(self.WHEEL_COLORS)]
