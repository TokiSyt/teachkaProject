"""Dynamic per-quiz streak bonus (live.lock_and_grade).

The streak bonus adds ``streak_bonus_rate`` % of a round's points per
consecutive full-correct answer beyond the first, capped at
``streak_bonus_cap`` %. These exercise the real Redis-backed grader; each
test cleans its room up via close_room.

Cumulative score after each round (points P, rate R%, cap C%) for an
unbroken streak: round k (1-based) adds ``P + round(P * min(R*(k-1), C) / 100)``.
"""

import pytest

from apps.quizzmaker import live
from apps.quizzmaker.models import Round
from apps.quizzmaker.tests.factories import AnswerFactory, QuizFactory, RoundFactory


def _build(host, n_rounds, *, points=100, rate=10, cap=50):
    quiz = QuizFactory(user=host, streak_bonus_rate=rate, streak_bonus_cap=cap)
    ids = []  # (correct_id, wrong_id) per round
    for i in range(n_rounds):
        r = RoundFactory(quiz=quiz, order=i + 1, question_type=Round.SELECT_CORRECT, time_limit=0, points=points)
        correct = AnswerFactory(round=r, text="A", is_correct=True)
        wrong = AnswerFactory(round=r, text="B", is_correct=False)
        ids.append((correct.pk, wrong.pk))
    return quiz, ids


def _play(quiz, ids, correctness, *, scrub_meta=False):
    """Run a full game for one player; return cumulative score after each round.

    correctness: list of bool — whether the player picks the correct option.
    scrub_meta: delete the per-session streak keys to test the default fallback.
    """
    session = live.create_session(quiz, quiz.user, show_question_on_device=False)
    code = session.code
    try:
        if scrub_meta:
            live.client().hdel(live._k(code, "meta"), "streak_rate", "streak_cap")
        token = live.add_participant(code, "p1", None)
        live.start_game(code)  # phase question, round 0
        scores = []
        for idx, ok in enumerate(correctness):
            correct_id, wrong_id = ids[idx]
            live.submit_answer(code, token, idx, [correct_id] if ok else [wrong_id])
            live.lock_and_grade(code, idx)
            scores.append(live.get_participant(code, token)["score"])
            if idx < len(correctness) - 1:
                live.advance(code)  # reveal -> leaderboard
                live.advance(code)  # leaderboard -> next question
        return scores
    finally:
        live.close_room(code)


@pytest.mark.django_db
class TestStreakProgression:
    def test_default_rate10_cap50(self, user):
        # 10% per streak, capped at 50%, 100-point rounds.
        quiz, ids = _build(user, 7, points=100, rate=10, cap=50)
        scores = _play(quiz, ids, [True] * 7)
        # +100, +110, +120, +130, +140, +150(cap), +150(cap)
        assert scores == [100, 210, 330, 460, 600, 750, 900]

    def test_cap40_rate20_holds_beyond_third_streak(self, user):
        # The user's example: per-streak 20%, max 40%. Streak >3 must stay 40%.
        quiz, ids = _build(user, 5, points=100, rate=20, cap=40)
        scores = _play(quiz, ids, [True] * 5)
        # +100, +120, +140(40%), +140(cap), +140(cap)
        assert scores == [100, 220, 360, 500, 640]
        # Every round past the cap adds the same fixed amount.
        assert scores[3] - scores[2] == 140
        assert scores[4] - scores[3] == 140

    def test_rate_above_cap_caps_at_first_bonus(self, user):
        # 100% per streak but cap 50% -> second correct already pinned to 50%.
        quiz, ids = _build(user, 3, points=100, rate=100, cap=50)
        scores = _play(quiz, ids, [True] * 3)
        assert scores == [100, 250, 400]


class TestStreakDisabled:
    @pytest.mark.django_db
    def test_zero_rate_means_no_bonus(self, user):
        quiz, ids = _build(user, 4, points=100, rate=0, cap=50)
        scores = _play(quiz, ids, [True] * 4)
        assert scores == [100, 200, 300, 400]

    @pytest.mark.django_db
    def test_zero_cap_means_no_bonus(self, user):
        quiz, ids = _build(user, 3, points=100, rate=20, cap=0)
        scores = _play(quiz, ids, [True] * 3)
        assert scores == [100, 200, 300]


@pytest.mark.django_db
class TestStreakReset:
    def test_wrong_answer_resets_streak(self, user):
        # T, T, F, T, T with 20% per streak, no effective cap.
        quiz, ids = _build(user, 5, points=100, rate=20, cap=100)
        scores = _play(quiz, ids, [True, True, False, True, True])
        # +100, +120, +0(reset), +100(streak restarts), +120
        assert scores == [100, 220, 220, 320, 440]


@pytest.mark.django_db
class TestStreakRounding:
    def test_fractional_bonus_is_rounded(self, user):
        # 15-point rounds, 10% per streak: streak2 -> 1.5 -> 2, streak3 -> 3.0.
        quiz, ids = _build(user, 3, points=15, rate=10, cap=100)
        scores = _play(quiz, ids, [True] * 3)
        assert scores == [15, 32, 50]


@pytest.mark.django_db
class TestMetaFallback:
    def test_missing_session_keys_fall_back_to_defaults(self, user):
        # Quiz configured 20/20, but the session's streak keys are scrubbed
        # (e.g. a session created before the feature). Grading must use the
        # module defaults (10% / 50%), not the quiz values.
        quiz, ids = _build(user, 3, points=100, rate=20, cap=20)
        scores = _play(quiz, ids, [True] * 3, scrub_meta=True)
        # Defaults: +100, +110, +120  (not the quiz's 20/20: +100,+120,+120)
        assert scores == [100, 210, 330]
