from django.db import models
from django.utils import timezone

# Create your models here.


class TimerSession(models.Model):
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.pk} - {self.start_time}"

    def duration(self):
        return (self.end_time or timezone.now()) - self.start_time


class Flag(models.Model):
    session = models.ForeignKey(TimerSession, on_delete=models.CASCADE, related_name="flags")
    label = models.CharField(max_length=50)
    time_offset = models.DurationField()

    def __str__(self):
        return f"{self.label} @ {self.time_offset}"
