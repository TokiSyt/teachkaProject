import random


def choose_random_member(members_queryset, already_chosen_ids):
    """
    Choose a random member from those not yet chosen.

    Args:
        members_queryset: QuerySet of Member objects
        already_chosen_ids: List of already chosen member IDs

    Returns:
        Tuple of (chosen_member or None, updated already_chosen_ids list)
    """
    remaining = members_queryset.exclude(id__in=already_chosen_ids)

    if not remaining.exists():
        return None, already_chosen_ids

    chosen = random.choice(list(remaining))
    already_chosen_ids.append(chosen.id)

    return chosen, already_chosen_ids
