import random


def group_split(members_list, group_size):
    random.shuffle(members_list)
    list = [members_list[i : i + group_size] for i in range(0, len(members_list), group_size)]
    return list


def get_split_group_color(member_groups):
    for group in member_groups:
        random_member = random.choice(group)
        group.append(random_member.color)
    return member_groups
