from django.apps import apps
from django.conf import settings
from django.db import models


class GroupCreationModel(models.Model):
    """Model for creating and managing groups of members."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    members_string = models.TextField(
        help_text='Comma-separated names. (f.e.: "Toki, Tina, Alice") | We recommend not using the same exact name for different members',
        default="",
    )
    size = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

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

    def sync_members(self):
        """
        Sync Member records with the current members_string input.

        Handles duplicate names correctly - if a user enters "John, Alice, John",
        two separate Member records are created for John (with different IDs).

        Note: This is also called automatically via post_save signal.
        Use apps.get_model() to avoid circular imports.
        """
        from collections import Counter

        try:
            Member = apps.get_model("core", "Member")
            FieldDefinition = apps.get_model("point_system", "FieldDefinition")
        except LookupError:
            # core or point_system app not installed
            return

        current_names = self.get_members_list()
        current_name_counts = Counter(current_names)

        existing_members = list(self.members.all())
        existing_name_counts = Counter(m.name for m in existing_members)

        # Delete members that are no longer needed (or have too many)
        for member in existing_members:
            if existing_name_counts[member.name] > current_name_counts.get(member.name, 0):
                member.delete()
                existing_name_counts[member.name] -= 1

        # Fetch field definitions once for creating new members
        positive_fields = list(FieldDefinition.objects.filter(group=self, definition="positive"))
        negative_fields = list(FieldDefinition.objects.filter(group=self, definition="negative"))

        # Create new members where needed (including duplicates)
        existing_name_counts = Counter(m.name for m in self.members.all())
        for name in current_names:
            needed = current_name_counts[name]
            have = existing_name_counts.get(name, 0)

            if have < needed:
                member = Member.objects.create(group=self, name=name)

                member.positive_data = {}
                for field in positive_fields:
                    member.positive_data[field.name] = 0 if field.type == "int" else ""

                member.negative_data = {}
                for field in negative_fields:
                    member.negative_data[field.name] = 0 if field.type == "int" else ""

                member.assign_color()
                member.save()
                existing_name_counts[name] = have + 1
