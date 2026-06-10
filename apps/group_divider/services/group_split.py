import random


def group_split(members_list, group_size):
    random.shuffle(members_list)
    list = [members_list[i : i + group_size] for i in range(0, len(members_list), group_size)]
    return list


def group_split_by_teams(members_list, num_teams):
    """Split members into a fixed number of teams, distributed as evenly as possible."""
    random.shuffle(members_list)
    num_teams = min(num_teams, len(members_list)) or 1
    teams = [[] for _ in range(num_teams)]
    for i, member in enumerate(members_list):
        teams[i % num_teams].append(member)
    return teams


def get_split_group_color(member_groups):
    for group in member_groups:
        random_member = random.choice(group)
        group.append(random_member.color)
    return member_groups
