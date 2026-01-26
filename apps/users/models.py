from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    theme = models.CharField(max_length=10, choices=[("light", "Light"), ("dark", "Dark")], default="light")
    icon_hover_color = models.CharField(max_length=20, default="#1779db")