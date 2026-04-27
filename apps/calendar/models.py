from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import UserOwnedModel


class Event(UserOwnedModel):
    RECURRENCE_NONE = "none"
    RECURRENCE_DAILY = "daily"
    RECURRENCE_WEEKLY = "weekly"
    RECURRENCE_MONTHLY = "monthly"
    RECURRENCE_YEARLY = "yearly"
    RECURRENCE_CHOICES = [
        (RECURRENCE_NONE, _("One-time event")),
        (RECURRENCE_DAILY, _("Daily")),
        (RECURRENCE_WEEKLY, _("Weekly")),
        (RECURRENCE_MONTHLY, _("Monthly")),
        (RECURRENCE_YEARLY, _("Yearly")),
    ]

    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    recurrence = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default=RECURRENCE_NONE)
    recurrence_end = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self) -> str:
        return f"{self.title} ({self.start_datetime:%Y-%m-%d})"
