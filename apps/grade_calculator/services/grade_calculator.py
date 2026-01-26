def grade_calculator(max_points: int, rounding_option: int) -> list[float]:
    """
    Calculates grade thresholds based on max_points and rounding option.

    :param max_points: float, the maximum test score
    :param rounding_option: int (1 = round, 2 = decimal by 0.5)
    :return: list of grade cutoffs
    """

    grades: list[float] = [
        max_points * x for x in [1, 0.90, 0.89, 0.75, 0.74, 0.50, 0.49, 0.35, 0.34, 0]
    ]
    grades = [round(grade) for grade in grades]

    for grade_index in range(len(grades) - 1):
        if grades[grade_index] == grades[grade_index + 1]:
            grades[grade_index] += 1 if rounding_option == 1 else 0.5

    return grades
