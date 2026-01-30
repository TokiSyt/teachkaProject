from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class CustomUser(AbstractUser):
    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
        ("pastel", "Pastel"),
    ]
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")
    icon_hover_color = models.CharField(max_length=20, default="#1779db")

    # Usage tracking
    calculator_uses = models.PositiveIntegerField(default=0)
    wheel_spins = models.PositiveIntegerField(default=0)
    divider_uses = models.PositiveIntegerField(default=0)
