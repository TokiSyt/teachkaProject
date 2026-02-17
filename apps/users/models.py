from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
        ("pastel", "Pastel"),
    ]
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("pt", "Português"),
        ("cs", "Čeština"),
    ]
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="en")
    icon_hover_color = models.CharField(max_length=20, default="#1779db")


class UserStats(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="stats")
    calculator_uses = models.PositiveIntegerField(default=0)
    wheel_spins = models.PositiveIntegerField(default=0)
    divider_uses = models.PositiveIntegerField(default=0)
    stopwatch_starts = models.PositiveIntegerField(default=0)
    stopwatch_flags = models.PositiveIntegerField(default=0)
    stopwatch_total_ms = models.PositiveBigIntegerField(default=0)
    countdown_starts = models.PositiveIntegerField(default=0)
    countdown_total_ms = models.PositiveBigIntegerField(default=0)

    class Meta:
        verbose_name_plural = "User stats"

    def __str__(self):
        return f"Stats for {self.user.username}"
