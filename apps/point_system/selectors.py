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

    positive_fields = FieldDefinition.objects.filter(
        group=group, definition="positive"
    ).order_by("created_at")

    negative_fields = FieldDefinition.objects.filter(
        group=group, definition="negative"
    ).order_by("created_at")

    fields = {
        "positive": list(positive_fields),
        "negative": list(negative_fields),
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
    _, fields = get_group_with_fields(group_id, user)

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
    }


