from django.db import models

from apps.group_maker.models import GroupCreationModel

# Create your models here.


class Member(models.Model):
    group = models.ForeignKey(GroupCreationModel, on_delete=models.CASCADE, related_name="karma_members")
    name = models.CharField(max_length=50)

    positive_data = models.JSONField(default=dict)
    negative_data = models.JSONField(default=dict)

    positive_total = models.IntegerField(default=0, blank=True)
    negative_total = models.IntegerField(default=0, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} ({self.group.title})"


class FieldDefinition(models.Model):
    group = models.ForeignKey(GroupCreationModel, on_delete=models.CASCADE, related_name="fields")
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=10,
        choices=[("int", "Numerical"), ("str", "Text")],
        default="positive",
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
        return f"{self.name} ({self.definition})"
