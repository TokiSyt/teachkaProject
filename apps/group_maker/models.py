import logging

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class GroupCreationModel(models.Model):
    """Model for creating and managing groups of members."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    members_string = models.TextField(
        help_text=_(
            'Comma-separated names. (f.e.: "Toki, Tina, Alice") | We recommend not using the same exact name for different members'
        ),
        default="",
    )
    size = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title}_{self.user}"

    def save(self, *args, **kwargs):
        members = self.get_members_list()
        if not members:
            raise ValueError("You must provide at least one member.")
        self.size = len(members)
        super().save(*args, **kwargs)
        # Note: sync_members is handled by post_save signal in signals.py

    def get_members_list(self):
        """Return list of member names from members_string (for backward compatibility)."""
        return [member.strip() for member in self.members_string.replace("\n", ",").split(",") if member.strip()]

    def get_members(self):
        """Return Member queryset for this group."""
        return self.members.all()

    def get_size(self):
        return self.size

    @property
    def karma_members(self):
        """Alias for backward compatibility with code using old related_name."""
        return self.members

    # Member records are kept in sync automatically via the post_save signal
    # "sync_members_on_save" in signals.py (no explicit sync_members() method).
