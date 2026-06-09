"""Live-play logic backed by Redis (live.py) + join gating.

These exercise the real Redis-backed state gateway; each test cleans its room
up via close_room so state doesn't leak across the 6h TTL.
"""

import pytest
from django.urls import reverse

from apps.quizzmaker import live
from apps.quizzmaker.models import Participant, Round
from apps.quizzmaker.tests.factories import AnswerFactory, QuizFactory, RoundFactory


def make_playable_quiz(host, n_rounds=1):
    quiz = QuizFactory(user=host, title="Live Quiz")
    for i in range(n_rounds):
        r = RoundFactory(quiz=quiz, order=i + 1, question_type=Round.SELECT_CORRECT, time_limit=0)
        AnswerFactory(round=r, text="A", is_correct=True)
        AnswerFactory(round=r, text="B", is_correct=False)
    return quiz


@pytest.fixture
def live_session(db, user):
    """A lobby-phase session hosted by `user`. Yields (code, session)."""
    quiz = make_playable_quiz(user, n_rounds=2)
    session = live.create_session(quiz, user, show_question_on_device=False)
    yield session.code, session
    live.close_room(session.code)


@pytest.mark.django_db
class TestHostCannotJoinOwnGame:
    def test_host_join_post_is_rejected(self, authenticated_client, user, live_session):
        code, session = live_session
        resp = authenticated_client.post(
            reverse("quizzmaker:join"),
            {"code": code, "nickname": "sneaky", "code_locked": "1"},
        )
        assert resp.status_code == 200  # re-rendered form, not a redirect into play
        assert resp.context.get("error")
        assert Participant.objects.filter(session=session).count() == 0

    def test_non_host_can_still_join(self, client, live_session):
        code, session = live_session
        resp = client.post(
            reverse("quizzmaker:join"),
            {"code": code, "nickname": "player1", "code_locked": "1"},
        )
        assert resp.status_code == 302
        assert Participant.objects.filter(session=session).count() == 1


@pytest.mark.django_db
class TestAllAnswered:
    def test_false_until_every_player_has_answered(self, live_session):
        code, _session = live_session
        t1 = live.add_participant(code, "p1", None)
        t2 = live.add_participant(code, "p2", None)
        live.start_game(code)  # phase question, round 0
        assert live.all_answered(code, 0) is False
        live.submit_answer(code, t1, 0, [])
        assert live.all_answered(code, 0) is False
        live.submit_answer(code, t2, 0, [])
        assert live.all_answered(code, 0) is True

    def test_false_when_no_participants(self, live_session):
        code, _session = live_session
        live.start_game(code)
        assert live.all_answered(code, 0) is False


@pytest.mark.django_db
class TestLeaderboardPhase:
    def test_reveal_advances_to_leaderboard_then_next_question(self, live_session):
        # live_session has 2 rounds.
        code, _session = live_session
        live.add_participant(code, "p1", None)
        live.start_game(code)  # question, round 0
        live.lock_and_grade(code, 0)  # reveal
        assert live.get_meta(code)["phase"] == live.REVEAL

        phase = live.advance(code)
        assert phase == live.LEADERBOARD
        meta = live.get_meta(code)
        assert meta["phase"] == live.LEADERBOARD
        assert int(meta["current_round"]) == 0  # still on the same round

        phase = live.advance(code)
        assert phase == live.QUESTION
        assert int(live.get_meta(code)["current_round"]) == 1

    def test_leaderboard_of_last_round_advances_to_ended(self, live_session):
        code, _session = live_session
        live.add_participant(code, "p1", None)
        live.start_game(code)
        # round 0
        live.lock_and_grade(code, 0)
        live.advance(code)  # leaderboard
        live.advance(code)  # question round 1
        live.lock_and_grade(code, 1)  # reveal
        assert live.advance(code) == live.LEADERBOARD
        assert live.advance(code) == live.ENDED
        assert live.get_meta(code)["phase"] == live.ENDED


@pytest.mark.django_db
class TestLeaderboardPayload:
    def _to_leaderboard(self, code):
        t1 = live.add_participant(code, "p1", None)
        live.start_game(code)
        live.lock_and_grade(code, 0)
        live.advance(code)  # leaderboard
        return t1

    def test_host_payload_has_standings(self, live_session):
        code, _session = live_session
        self._to_leaderboard(code)
        payload = live.state_payload(code, role="host")
        assert payload["phase"] == live.LEADERBOARD
        assert "leaderboard" in payload
        assert payload["leaderboard"][0]["nickname"] == "p1"

    def test_player_payload_has_self_row(self, live_session):
        code, _session = live_session
        t1 = self._to_leaderboard(code)
        payload = live.state_payload(code, role="player", token=t1)
        assert "leaderboard" in payload
        assert payload["me"]["nickname"] == "p1"
        assert payload["me"]["rank"] == 1
