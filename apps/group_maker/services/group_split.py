import random


def group_split(members_list, group_size):
    random.shuffle(members_list)
    list = [members_list[i : i + group_size] for i in range(0, len(members_list), group_size)]
    return list
