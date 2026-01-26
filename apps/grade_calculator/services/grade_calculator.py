def grade_calculator(max_points: float, rounding_option: int) -> list[float]:
    """
    Calculates grade thresholds based on max_points and rounding option.

    :param max_points: float, the maximum test score
    :param rounding_option: int (1 = round, 2 = decimal by 0.5)
    :return: list of grade cutoffs
    """
    if max_points < 4:
        return []

    static_grades: dict[int, list[float]] = {
        4: [4, 4, 3, 3, 2, 2, 1, 1, 0, 0],
        5: [5, 5, 4, 3, 2, 2, 1, 1, 0, 0],
        6: [6, 6, 5, 4, 3, 3, 2, 1, 0, 0],
        7: [7, 6, 5, 4, 3, 2, 1, 1, 0, 0],
        8: [8, 7, 6, 5, 4, 3, 2, 1, 0, 0],
        9: [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
    }

    rounded_max = round(max_points)
    if rounded_max in static_grades:
        return static_grades[rounded_max]

    grades: list[float] = [
        max_points * x for x in [1, 0.90, 0.89, 0.75, 0.74, 0.50, 0.49, 0.35, 0.34, 0]
    ]
    grades = [round(grade) for grade in grades]

    for grade_index in range(1, len(grades)):
        if grades[grade_index] >= grades[grade_index - 1]:
            grades[grade_index] -= 1 if rounding_option == 1 else 0.5

    grades[0] = int(max_points) if float(max_points).is_integer() else max_points
    grades[9] = 0
    return grades
