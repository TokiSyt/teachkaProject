"""
Signals for group_maker app.

Handles automatic syncing of karma members when groups are saved.
"""

import logging

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="group_maker.GroupCreationModel")
def sync_karma_members_on_save(sender, instance, created, **kwargs):
    """
    Sync karma members when a group is created or updated.

    Uses apps.get_model() to avoid circular imports with point_system.
    """
    try:
        Member = apps.get_model("point_system", "Member")
        FieldDefinition = apps.get_model("point_system", "FieldDefinition")
    except LookupError:
        # point_system app not installed
        logger.debug("point_system app not available, skipping member sync")
        return

    current_names = instance.get_members_list()
    current_names_ordered = list(dict.fromkeys(current_names))

    existing_members = instance.karma_members.all()

    # Remove members that are no longer in the list
    for member in existing_members:
        if member.name not in current_names:
            member.delete()
            logger.debug(f"Deleted member {member.name} from group {instance.title}")

    # Add or update members
    for name in current_names_ordered:
        member, member_created = Member.objects.get_or_create(group=instance, name=name)

        if member_created:
            positive_fields = FieldDefinition.objects.filter(group=instance, definition="positive")
            negative_fields = FieldDefinition.objects.filter(group=instance, definition="negative")

            member.positive_data = {}
            for field in positive_fields:
                member.positive_data[field.name] = 0 if field.type == "int" else ""

            member.negative_data = {}
            for field in negative_fields:
                member.negative_data[field.name] = 0 if field.type == "int" else ""

            member.save()
            logger.debug(f"Created member {name} in group {instance.title}")
