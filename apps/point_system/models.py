from django.db import models

from apps.core.models import Member  # noqa: F401 - re-exported for backward compatibility
from apps.group_maker.models import GroupCreationModel


class FieldDefinition(models.Model):
    group = models.ForeignKey(GroupCreationModel, on_delete=models.CASCADE, related_name="fields")
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=10,
        choices=[("int", "Numerical"), ("str", "Text")],
        default="int",
    )
    definition = models.CharField(
        max_length=10,
        choices=[("positive", "Positive"), ("negative", "Negative")],
        default="positive",
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "name", "definition"], name="unique_field_per_group_and_table")
        ]

    def __str__(self):
        return f"{self.name}_({self.definition})_({self.type})"


class PointSystemGroupSettings(models.Model):
    """Per-group display preferences for the point system tables."""

    group = models.OneToOneField(GroupCreationModel, on_delete=models.CASCADE, related_name="point_settings")
    show_positive = models.BooleanField(default=True)
    show_negative = models.BooleanField(default=True)

    def __str__(self):
        return f"Settings(group={self.group_id}, +{self.show_positive}, -{self.show_negative})"

    @classmethod
    def for_group(cls, group) -> "PointSystemGroupSettings":
        """Return the settings row for a group, creating defaults if absent."""
        settings, _ = cls.objects.get_or_create(group=group)
        return settings

    @classmethod
    def set_table_visibility(cls, group, definition: str, visible: bool) -> "PointSystemGroupSettings":
        """Persist whether the positive or negative table is shown."""
        settings = cls.for_group(group)
        if definition == "positive":
            settings.show_positive = visible
        elif definition == "negative":
            settings.show_negative = visible
        settings.save()
        return settings
