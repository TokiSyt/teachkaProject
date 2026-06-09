"""Consumer-level checks driven via asyncio.run (no pytest-asyncio dep).

Verifies live behaviour through the WebSocket: a kicked player is told to leave
immediately (no refresh), and the round ends as soon as everyone has answered.
"""

import asyncio

import pytest
from channels.testing import WebsocketCommunicator

from apps.quizzmaker import live
from apps.quizzmaker.consumers import GameConsumer
from apps.quizzmaker.models import Round
from apps.quizzmaker.tests.factories import AnswerFactory, QuizFactory, RoundFactory


def _make_quiz(host):
    quiz = QuizFactory(user=host, title="WS Quiz")
    r = RoundFactory(quiz=quiz, order=1, question_type=Round.SELECT_CORRECT, time_limit=0)
    AnswerFactory(round=r, text="A", is_correct=True)
    AnswerFactory(round=r, text="B", is_correct=False)
    return quiz


def _host_comm(code, host):
    comm = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/quiz/{code}/")
    comm.scope["url_route"] = {"kwargs": {"code": code}}
    comm.scope["user"] = host
    comm.scope["cookies"] = {}
    return comm


def _player_comm(code, token):
    comm = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/quiz/{code}/")
    comm.scope["url_route"] = {"kwargs": {"code": code}}
    comm.scope["cookies"] = {f"quiz_token_{code}": token}
    return comm


async def _drain_until(comm, want_type, tries=8):
    for _ in range(tries):
        msg = await comm.receive_json_from(timeout=3)
        if msg.get("type") == want_type:
            return msg
    raise AssertionError(f"never received {want_type!r}")


@pytest.mark.django_db(transaction=True)
def test_kicked_player_is_told_to_leave_live(django_user_model):
    host = django_user_model.objects.create_user(username="wshost", email="wshost@x.com", password="p")
    quiz = _make_quiz(host)
    session = live.create_session(quiz, host, show_question_on_device=False)
    code = session.code
    token = live.add_participant(code, "kickme", None)

    async def scenario():
        hc = _host_comm(code, host)
        pc = _player_comm(code, token)
        assert (await hc.connect())[0]
        assert (await pc.connect())[0]
        # Both get an initial state snapshot.
        await _drain_until(hc, "state")
        await _drain_until(pc, "state")
        # Host kicks the player by nickname.
        await hc.send_json_to({"action": "kick", "nickname": "kickme"})
        # Player must receive a "closed" directive without any manual refresh.
        await _drain_until(pc, "closed")
        await hc.disconnect()
        await pc.disconnect()

    try:
        asyncio.run(scenario())
    finally:
        live.close_room(code)


@pytest.mark.django_db(transaction=True)
def test_round_reveals_when_all_players_answered(django_user_model):
    host = django_user_model.objects.create_user(username="wshost2", email="wshost2@x.com", password="p")
    quiz = _make_quiz(host)
    session = live.create_session(quiz, host, show_question_on_device=False)
    code = session.code
    token = live.add_participant(code, "solo", None)
    live.start_game(code)  # single participant, question phase, round 0

    async def scenario():
        pc = _player_comm(code, token)
        assert (await pc.connect())[0]
        first = await _drain_until(pc, "state")
        assert first["phase"] == "question"
        # The only player answers -> round should auto-advance to reveal with no
        # host action and no timer (time_limit=0).
        await pc.send_json_to({"action": "answer", "round_idx": 0, "value": []})
        reveal = await _drain_until(pc, "state")
        assert reveal["phase"] == "reveal"
        await pc.disconnect()

    try:
        asyncio.run(scenario())
    finally:
        live.close_room(code)
