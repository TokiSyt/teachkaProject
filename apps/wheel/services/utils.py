import random


def choose_a_random_name(name_list, already_chosen_names):
    remaining_names = [name for name in name_list if name not in already_chosen_names]

    if not remaining_names:
        already_chosen_names = []
        remaining_names = name_list

    new_choice = random.choice(remaining_names)
    already_chosen_names.append(new_choice)

    return new_choice, already_chosen_names
