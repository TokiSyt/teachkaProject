"""
Selectors for point_system app.

Contains optimized queries with prefetch_related to avoid N+1 issues.
"""

import logging

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.group_maker.models import GroupCreationModel

from .models import FieldDefinition, Member
from .services.member_service import MemberService

logger = logging.getLogger(__name__)


def get_user_groups(user) -> QuerySet[GroupCreationModel]:
    """
    Get all groups owned by a user.

    Args:
        user: User instance

    Returns:
        QuerySet of GroupCreationModel
    """
    return GroupCreationModel.objects.filter(user=user).order_by("-created")


def get_group_with_members(group_id: int, user) -> tuple[GroupCreationModel, QuerySet[Member]]:
    """
    Get a group with its members, optimized to avoid N+1 queries.

    Args:
        group_id: Group ID
        user: User instance (for permission check)

    Returns:
        Tuple of (group, members_queryset)
    """
    group = get_object_or_404(GroupCreationModel, id=group_id, user=user)

    # Prefetch related data to avoid N+1
    members = Member.objects.filter(group=group).order_by("id")

    return group, members


def get_group_with_fields(group_id: int, user) -> tuple[GroupCreationModel, dict]:
    """
    Get a group with its field definitions organized by type.

    Args:
        group_id: Group ID
        user: User instance (for permission check)

    Returns:
        Tuple of (group, fields_dict) where fields_dict has 'positive' and 'negative' keys
    """
    group = get_object_or_404(GroupCreationModel, id=group_id, user=user)

    positive_fields = list(
        FieldDefinition.objects.filter(group=group, definition="positive").order_by("order", "created_at")
    )
    negative_fields = list(
        FieldDefinition.objects.filter(group=group, definition="negative").order_by("order", "created_at")
    )

    fields = {
        "positive": positive_fields,
        "negative": negative_fields,
        "positive_names": [f.name for f in positive_fields],
        "negative_names": [f.name for f in negative_fields],
        "positive_types": {f.name: "number" if f.type == "int" else "text" for f in positive_fields},
        "negative_types": {f.name: "number" if f.type == "int" else "text" for f in negative_fields},
    }

    return group, fields


def get_group_full_data(group_id: int, user) -> dict:
    """
    Get complete group data including members and fields.

    This is the main selector for the dashboard view.

    Args:
        group_id: Group ID
        user: User instance (for permission check)

    Returns:
        Dict with group, members, and field information
    """
    group, members = get_group_with_members(group_id, user)

    # Reuse the group object instead of fetching it again
    positive_fields = list(
        FieldDefinition.objects.filter(group=group, definition="positive").order_by("order", "created_at")
    )
    negative_fields = list(
        FieldDefinition.objects.filter(group=group, definition="negative").order_by("order", "created_at")
    )
    fields = {
        "positive_names": [f.name for f in positive_fields],
        "negative_names": [f.name for f in negative_fields],
        "positive_types": {f.name: "number" if f.type == "int" else "text" for f in positive_fields},
        "negative_types": {f.name: "number" if f.type == "int" else "text" for f in negative_fields},
    }

    # Calculate totals for each member
    for member in members:
        member.positive_total = MemberService._calculate_total(member.positive_data)
        member.negative_total = MemberService._calculate_total(member.negative_data)

    return {
        "group": group,
        "members": members,
        "positive_column_names": fields["positive_names"],
        "negative_column_names": fields["negative_names"],
        "column_type_positive": fields["positive_types"],
        "column_type_negative": fields["negative_types"],
        "positive_fields": positive_fields,
        "negative_fields": negative_fields,
    }


# Single-hue stacked-bar palettes (light -> dark); index by column order.
_GREEN_SHADES = ["#bbf7d0", "#86efac", "#4ade80", "#22c55e", "#16a34a", "#15803d", "#166534", "#14532d"]
_RED_SHADES = ["#fecaca", "#fca5a5", "#f87171", "#ef4444", "#dc2626", "#b91c1c", "#991b1b", "#7f1d1d"]


def _bar_segments(fields, data, total, shades):
    """Build stacked-bar segments for a table's numeric columns.

    One segment per int column: name, value, pct of the table total, and a
    single-hue colour shaded light->dark by the column's position.
    """
    segments = []
    numeric = [f for f in fields if f.type == "int"]
    for i, field in enumerate(numeric):
        try:
            value = int((data or {}).get(field.name, 0) or 0)
        except (ValueError, TypeError):
            value = 0
        pct = round(value / total * 100) if total else 0
        segments.append(
            {
                "name": field.name,
                "value": value,
                "pct": pct,
                "color": shades[i % len(shades)],
            }
        )
    return segments


def get_member_dashboard_data(member_id: int, user) -> dict:
    """Per-member dashboard data (karma dashboard, PRD #39).

    Owner-only: a member belonging to another user raises Http404.
    Totals are computed from the stored JSON data (not the cached columns).

    Args:
        member_id: Member ID
        user: User instance (for permission check)

    Returns:
        Dict with member, group, fields, totals, net and bar segments.
    """
    member = get_object_or_404(Member, id=member_id, group__user=user)
    group = member.group

    positive_fields = list(
        FieldDefinition.objects.filter(group=group, definition="positive").order_by("order", "created_at")
    )
    negative_fields = list(
        FieldDefinition.objects.filter(group=group, definition="negative").order_by("order", "created_at")
    )
    # Free-form (text) columns from both tables live together in the Notes tab.
    text_fields = [f for f in positive_fields + negative_fields if f.type == "str"]

    positive_total = MemberService._calculate_total(member.positive_data)
    negative_total = MemberService._calculate_total(member.negative_data)

    return {
        "member": member,
        "group": group,
        "positive_fields": positive_fields,
        "negative_fields": negative_fields,
        "text_fields": text_fields,
        "positive_column_types": {f.name: "number" if f.type == "int" else "text" for f in positive_fields},
        "negative_column_types": {f.name: "number" if f.type == "int" else "text" for f in negative_fields},
        "positive_segments": _bar_segments(positive_fields, member.positive_data, positive_total, _GREEN_SHADES),
        "negative_segments": _bar_segments(negative_fields, member.negative_data, negative_total, _RED_SHADES),
        "positive_total": positive_total,
        "negative_total": negative_total,
        "net": positive_total - negative_total,
    }
