"""
Signals for group_maker app.

Handles automatic syncing of members when groups are saved.
"""

import logging

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="group_maker.GroupCreationModel")
def sync_members_on_save(sender, instance, created, **kwargs):
    """
    Sync Member records when a group is created or updated.

    Handles duplicate names correctly - if a user enters "John, Alice, John",
    two separate Member records are created for John (with different IDs).

    Uses apps.get_model() to avoid circular imports.
    """
    from collections import Counter

    try:
        Member = apps.get_model("core", "Member")
        FieldDefinition = apps.get_model("point_system", "FieldDefinition")
    except LookupError:
        # core or point_system app not installed
        logger.debug("core/point_system app not available, skipping member sync")
        return

    current_names = instance.get_members_list()
    current_name_counts = Counter(current_names)

    existing_members = list(instance.members.all())
    existing_name_counts = Counter(m.name for m in existing_members)

    from collections import defaultdict

    name_to_members = defaultdict(list)
    for member in instance.members.all():
        name_to_members[member.name].append(member)

    # Delete members that are no longer needed (or have too many)
    for member in existing_members:
        if existing_name_counts[member.name] > current_name_counts.get(member.name, 0):
            member.delete()
            existing_name_counts[member.name] -= 1
            logger.debug(f"Deleted member {member.name} from group {instance.title}")

    # Fetch field definitions once for creating new members
    positive_fields = list(FieldDefinition.objects.filter(group=instance, definition="positive"))
    negative_fields = list(FieldDefinition.objects.filter(group=instance, definition="negative"))

    for index, name in enumerate(current_names):
        if name_to_members[name]:
            member = name_to_members[name].pop(0)

            if member.order != index:
                member.order = index
                member.save(update_fields=["order"])

        else:
            member = Member.objects.create(group=instance, name=name, order=index)
            member.positive_data = {field.name: (0 if field.type == "int" else "") for field in positive_fields}
            member.negative_data = {field.name: (0 if field.type == "int" else "") for field in negative_fields}
            member.assign_color()
            member.save()
