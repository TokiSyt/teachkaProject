"""
Member service for point_system app.

Handles member data operations.
"""

import logging
from typing import Any

from django.db import transaction

from ..models import FieldDefinition, Member

logger = logging.getLogger(__name__)


class MemberService:
    """Service class for member-related operations."""

    @staticmethod
    def _sanitize_data(data: dict[str, Any]) -> dict[str, Any]:
        """Ensure numeric values are not negative."""
        sanitized = {}
        for key, value in data.items():
            try:
                num_value = int(value)
                sanitized[key] = max(0, num_value)
            except (ValueError, TypeError):
                sanitized[key] = value
        return sanitized

    @staticmethod
    def update_member_data(
        member: Member,
        positive_data: dict[str, Any] | None = None,
        negative_data: dict[str, Any] | None = None,
    ) -> Member:
        """
        Update member's positive and/or negative data.

        Args:
            member: The Member instance to update
            positive_data: New positive data dict (optional)
            negative_data: New negative data dict (optional)

        Returns:
            Updated Member instance
        """
        if positive_data is not None:
            member.positive_data = MemberService._sanitize_data(positive_data)
        if negative_data is not None:
            member.negative_data = MemberService._sanitize_data(negative_data)

        # Recalculate totals
        member.positive_total = MemberService._calculate_total(member.positive_data)
        member.negative_total = MemberService._calculate_total(member.negative_data)

        member.save()
        logger.debug(f"Updated member {member.name}: +{member.positive_total}/-{member.negative_total}")
        return member

    @staticmethod
    def _calculate_total(data: dict[str, Any] | None) -> int:
        """Calculate total from a data dict, handling non-numeric values."""
        if not data:
            return 0

        total = 0
        for value in data.values():
            try:
                total += int(value)
            except (ValueError, TypeError):
                pass
        return total

    @staticmethod
    @transaction.atomic
    def add_field_to_members(group, field_name: str, field_type: str, definition: str) -> None:
        """
        Add a new field to all members in a group.

        Args:
            group: GroupCreationModel instance
            field_name: Name of the new field
            field_type: 'int' or 'str'
            definition: 'positive' or 'negative'
        """
        default_value = 0 if field_type == "int" else ""
        members = list(Member.objects.filter(group=group))
        update_field = "positive_data" if definition == "positive" else "negative_data"

        for member in members:
            data = getattr(member, update_field)
            if data is None:
                data = {}
                setattr(member, update_field, data)
            data[field_name] = default_value

        if members:
            Member.objects.bulk_update(members, [update_field])

        logger.info(f"Added field '{field_name}' to {len(members)} members in group {group.title}")

    @staticmethod
    @transaction.atomic
    def remove_field_from_members(group, field_name: str, definition: str) -> None:
        """
        Remove a field from all members in a group.

        Args:
            group: GroupCreationModel instance
            field_name: Name of the field to remove
            definition: 'positive' or 'negative'
        """
        members = list(Member.objects.filter(group=group))
        update_field = "positive_data" if definition == "positive" else "negative_data"

        for member in members:
            data = getattr(member, update_field)
            if data:
                data.pop(field_name, None)

        if members:
            Member.objects.bulk_update(members, [update_field])

        # Also delete the field definition
        FieldDefinition.objects.filter(group=group, name=field_name, definition=definition).delete()

        logger.info(f"Removed field '{field_name}' from group {group.title}")

    @staticmethod
    @transaction.atomic
    def rename_field_for_members(group, old_name: str, new_name: str, definition: str) -> None:
        """
        Rename a field for all members in a group.

        Args:
            group: GroupCreationModel instance
            old_name: Current field name
            new_name: New field name
            definition: 'positive' or 'negative'
        """
        members = list(Member.objects.filter(group=group))
        update_field = "positive_data" if definition == "positive" else "negative_data"

        for member in members:
            data = getattr(member, update_field)
            if data and old_name in data:
                data[new_name] = data.pop(old_name)

        if members:
            Member.objects.bulk_update(members, [update_field])

        # Update the field definition
        FieldDefinition.objects.filter(group=group, name=old_name, definition=definition).update(name=new_name)

        logger.info(f"Renamed field '{old_name}' to '{new_name}' in group {group.title}")
