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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "name", "definition"], name="unique_field_per_group_and_table")
        ]

    def __str__(self):
        return f"{self.name}_({self.definition})_({self.type})"
