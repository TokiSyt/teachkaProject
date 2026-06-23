"""
Member service for point_system app.

Handles member data operations.
"""

import logging
from typing import Any

from django.db import transaction
from django.db.models import Max

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
    def create_field(group, field_name: str, field_type: str, definition: str) -> FieldDefinition:
        """
        Create a FieldDefinition with auto-assigned order and sync to members.

        Order = max(order) + 1 within (group, definition) bucket.
        """
        current_max = (
            FieldDefinition.objects.filter(group=group, definition=definition).aggregate(m=Max("order"))["m"] or 0
        )
        field = FieldDefinition.objects.create(
            group=group,
            name=field_name,
            type=field_type,
            definition=definition,
            order=current_max + 1,
        )
        MemberService.add_field_to_members(group, field_name, field_type, definition)
        return field

    @staticmethod
    @transaction.atomic
    def create_fields(group, specs: list[tuple[str, str]], definition: str) -> list[FieldDefinition]:
        """
        Create several FieldDefinitions in one call and sync them to members.

        ``specs`` is a list of ``(name, type)`` tuples sharing one ``definition``.
        Names already present in the table, or repeated within the batch, are
        skipped. Returns the FieldDefinitions actually created, in input order.
        """
        existing = set(
            FieldDefinition.objects.filter(group=group, definition=definition).values_list("name", flat=True)
        )
        created: list[FieldDefinition] = []
        seen: set[str] = set()
        for name, field_type in specs:
            if not name or name in existing or name in seen:
                continue
            seen.add(name)
            created.append(MemberService.create_field(group, name, field_type, definition))
        return created

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
    def clear_field_values(group, field_name: str, definition: str) -> None:
        """
        Reset a single field's value for every member, keeping the FieldDefinition.

        Numeric fields reset to 0, text fields to "".
        """
        field = FieldDefinition.objects.filter(group=group, name=field_name, definition=definition).first()
        default_value = "" if field and field.type == "str" else 0

        members = list(Member.objects.filter(group=group))
        update_field = "positive_data" if definition == "positive" else "negative_data"

        for member in members:
            data = getattr(member, update_field)
            if data and field_name in data:
                data[field_name] = default_value
                setattr(member, update_field, MemberService._sanitize_data(data))
            member.positive_total = MemberService._calculate_total(member.positive_data)
            member.negative_total = MemberService._calculate_total(member.negative_data)

        if members:
            Member.objects.bulk_update(members, [update_field, "positive_total", "negative_total"])

        logger.info(f"Cleared field '{field_name}' for group {group.title}")

    @staticmethod
    @transaction.atomic
    def delete_all_fields(group, definition: str) -> None:
        """
        Remove every FieldDefinition in one table and clear that side's member data.

        The group, its members, and the other table are preserved.
        """
        data_field = "positive_data" if definition == "positive" else "negative_data"
        total_field = "positive_total" if definition == "positive" else "negative_total"

        members = list(Member.objects.filter(group=group))
        for member in members:
            setattr(member, data_field, {})
            setattr(member, total_field, 0)

        if members:
            Member.objects.bulk_update(members, [data_field, total_field])

        FieldDefinition.objects.filter(group=group, definition=definition).delete()
        logger.info(f"Deleted all {definition} fields for group {group.title}")

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
