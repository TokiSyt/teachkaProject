"""Grading of type_input rounds with multiple accepted answers."""

from apps.quizzmaker import live
from apps.quizzmaker.models import Round


def _round(correct_texts, points=10):
    return {"question_type": Round.TYPE_INPUT, "points": points, "correct_texts": correct_texts}


class TestTypeInputGrading:
    def test_matches_any_accepted_answer(self):
        rd = _round(["paris", "paris, france"])
        assert live._grade_one(rd, "Paris, France")[0] == 10  # base points
        assert live._grade_one(rd, "  PARIS ")[0] == 10

    def test_no_match_scores_zero(self):
        rd = _round(["paris"])
        base, is_full, earned = live._grade_one(rd, "London")
        assert (base, is_full, earned) == (0, False, False)

    def test_match_is_full_correct(self):
        rd = _round(["yes", "y"])
        base, is_full, earned = live._grade_one(rd, "Y")
        assert is_full is True and earned is True
