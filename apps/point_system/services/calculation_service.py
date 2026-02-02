"""
Calculation service for point_system app.

Handles score calculations and aggregations.
"""

import logging
from typing import Any

from ..models import Member

logger = logging.getLogger(__name__)


class CalculationService:
    """Service class for calculations and aggregations."""

    @staticmethod
    def calculate_group_totals(group) -> dict[str, Any]:
        """
        Calculate aggregate totals for a group.

        Args:
            group: GroupCreationModel instance

        Returns:
            Dict with total_positive, total_negative, net_total, member_count
        """
        members = Member.objects.filter(group=group)

        total_positive = 0
        total_negative = 0

        for member in members:
            total_positive += member.positive_total or 0
            total_negative += member.negative_total or 0

        return {
            "total_positive": total_positive,
            "total_negative": total_negative,
            "net_total": total_positive - total_negative,
            "member_count": members.count(),
        }

    @staticmethod
    def get_member_ranking(group, order_by: str = "net") -> list[dict[str, Any]]:
        """
        Get members ranked by score.

        Args:
            group: GroupCreationModel instance
            order_by: 'net', 'positive', or 'negative'

        Returns:
            List of dicts with member info and rank
        """
        members = Member.objects.filter(group=group)

        member_scores: list[dict[str, Any]] = []
        for member in members:
            net = (member.positive_total or 0) - (member.negative_total or 0)
            member_scores.append(
                {
                    "id": member.id,
                    "name": member.name,
                    "positive_total": member.positive_total or 0,
                    "negative_total": member.negative_total or 0,
                    "net_total": net,
                }
            )

        # Sort based on order_by
        if order_by == "positive":
            member_scores.sort(key=lambda x: int(x["positive_total"]), reverse=True)
        elif order_by == "negative":
            member_scores.sort(key=lambda x: int(x["negative_total"]), reverse=True)
        else:  # net
            member_scores.sort(key=lambda x: int(x["net_total"]), reverse=True)

        # Add rank
        for i, score_dict in enumerate(member_scores, 1):
            score_dict["rank"] = i

        return member_scores

    @staticmethod
    def recalculate_all_totals(group) -> int:
        """
        Recalculate totals for all members in a group.

        Useful for data integrity checks.

        Args:
            group: GroupCreationModel instance

        Returns:
            Number of members updated
        """
        from .member_service import MemberService

        members = Member.objects.filter(group=group)
        count = 0

        for member in members:
            MemberService.update_member_data(member)  # Recalculates totals
            count += 1

        logger.info(f"Recalculated totals for {count} members in group {group.title}")
        return count
