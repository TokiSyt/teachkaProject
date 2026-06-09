"""End-to-end: 1 host + 29 players play a full game over real WebSockets.

Drives the actual consumer + Redis channel layer: everyone joins, the host
starts, all 29 answer each round (auto-reveal on the last answer), the host
steps reveal -> leaderboard -> next, through to the final leaderboard.
"""

import asyncio

import pytest
from channels.testing import WebsocketCommunicator

from apps.quizzmaker import live
from apps.quizzmaker.consumers import GameConsumer
from apps.quizzmaker.models import Round
from apps.quizzmaker.tests.factories import AnswerFactory, QuizFactory, RoundFactory

NUM_PLAYERS = 29
NUM_ROUNDS = 2


def _make_quiz(host):
    quiz = QuizFactory(user=host, title="Big Game")
    for i in range(NUM_ROUNDS):
        r = RoundFactory(quiz=quiz, order=i + 1, question_type=Round.SELECT_CORRECT, time_limit=0)
        AnswerFactory(round=r, text="A", is_correct=True)
        AnswerFactory(round=r, text="B", is_correct=False)
    return quiz


def _comm(code, *, user=None, token=None):
    comm = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/quiz/{code}/")
    comm.scope["url_route"] = {"kwargs": {"code": code}}
    comm.scope["user"] = user
    comm.scope["cookies"] = {f"quiz_token_{code}": token} if token else {}
    return comm


async def _state(comm, *, phase=None, current_round=None, tries=200):
    """Read messages until a ``state`` matches the wanted phase/round."""
    for _ in range(tries):
        msg = await comm.receive_json_from(timeout=5)
        if msg.get("type") != "state":
            continue
        if phase is not None and msg.get("phase") != phase:
            continue
        if current_round is not None and msg.get("current_round") != current_round:
            continue
        return msg
    raise AssertionError(f"never saw state phase={phase} round={current_round}")


@pytest.mark.django_db(transaction=True)
def test_full_game_one_host_29_players(django_user_model):
    host = django_user_model.objects.create_user(username="bighost", email="bh@x.com", password="p")
    quiz = _make_quiz(host)
    session = live.create_session(quiz, host, show_question_on_device=False)
    code = session.code
    tokens = [live.add_participant(code, f"p{i:02d}", None) for i in range(NUM_PLAYERS)]

    async def scenario():
        hc = _comm(code, user=host)
        assert (await hc.connect())[0]
        await _state(hc, phase="lobby")

        players = [_comm(code, token=t) for t in tokens]
        for p in players:
            assert (await p.connect())[0]
            await _state(p, phase="lobby")

        # Host starts the game.
        await hc.send_json_to({"action": "start"})
        await _state(hc, phase="question", current_round=0)

        for rnd in range(NUM_ROUNDS):
            # Every player answers the current question (picks option A's id).
            for p in players:
                st = await _state(p, phase="question", current_round=rnd)
                opt_id = st["round"]["answers"][0]["id"]
                await p.send_json_to({"action": "answer", "round_idx": rnd, "value": [opt_id]})
            # All answered -> auto reveal; host steps reveal -> leaderboard -> next.
            await _state(hc, phase="reveal", current_round=rnd)
            await hc.send_json_to({"action": "next"})
            await _state(hc, phase="leaderboard")
            await hc.send_json_to({"action": "next"})

        final = await _state(hc, phase="ended")
        assert len(final["leaderboard"]) == NUM_PLAYERS
        # Everyone answered correctly every round -> all share the top score.
        assert final["leaderboard"][0]["score"] > 0

        await hc.disconnect()
        for p in players:
            await p.disconnect()

    try:
        asyncio.run(scenario())
    finally:
        live.close_room(code)
