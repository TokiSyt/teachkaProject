from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    THEME_CHOICES = [
        ("light", _("Light")),
        ("dark", _("Dark")),
        ("pastel", _("Pastel")),
        ("lemonade", _("Editorial")),
        ("fantasy", _("Palette")),
    ]
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("pt", "Português"),
        ("cs", "Čeština"),
    ]
    COUNTRY_CHOICES = [
        ("CZ", _("Czech Republic")),
        ("PT", _("Portugal")),
        ("EN", _("England")),
    ]
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="en")
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, blank=True, default="")
    icon_hover_color = models.CharField(max_length=20, default="#1779db")
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    terms_version = models.CharField(max_length=10, blank=True, default="")


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
        verbose_name_plural = _("User stats")

    def __str__(self):
        return f"Stats for {self.user.username}"
