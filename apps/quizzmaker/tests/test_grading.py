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


class TestTrueFalseGrading:
    def _round(self, correct_id, points=10):
        return {
            "question_type": Round.TRUE_FALSE,
            "points": points,
            "correct_ids": [correct_id],
            "single_select": True,
        }

    def test_correct_pick_is_full(self):
        rd = self._round(correct_id=1)
        assert live._grade_one(rd, [1]) == (10, True, True)

    def test_wrong_pick_scores_zero(self):
        rd = self._round(correct_id=1)
        assert live._grade_one(rd, [2]) == (0, False, False)

    def test_no_pick_scores_zero(self):
        rd = self._round(correct_id=1)
        assert live._grade_one(rd, None) == (0, False, False)


class TestAcceptAllGrading:
    def _round(self, points=10):
        return {"question_type": Round.TYPE_INPUT, "points": points, "accept_all": True, "correct_texts": []}

    def test_any_nonblank_answer_is_full(self):
        rd = self._round()
        assert live._grade_one(rd, "literally anything") == (10, True, True)

    def test_blank_or_missing_answer_scores_zero(self):
        rd = self._round()
        assert live._grade_one(rd, "   ") == (0, False, False)
        assert live._grade_one(rd, None) == (0, False, False)
