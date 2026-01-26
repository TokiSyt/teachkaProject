from django.conf import settings
from django.db import models

# Create your models here.


class GroupCreationModel(models.Model):
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    members_string = models.TextField(
        help_text='Comma-separated list of names. (f.e.: "Toki, Tina, Alice")',
        default="",
    )
    size = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        members = self.get_members_list()
        if not members:
            raise ValueError("You must provide at least one member.")
        self.size = len(members)
        super().save(*args, **kwargs)

    def get_members_list(self):
        return [
            member.strip()
            for member in self.members_string.replace("\n", ",").split(",")
            if member.strip()
        ]
