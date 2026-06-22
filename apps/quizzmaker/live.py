"""Live quiz state + scoring.

Authoritative game state for a live (Kahoot-style) session lives in Redis, not
Postgres. This module is the single gateway to that state. It is fully
synchronous; the async WebSocket consumer calls it via ``sync_to_async``, and
plain HTTP views (host/join) call it directly.

Persistence split:
- Redis  -> live, ephemeral: phase, current round, per-player answers/scores,
            answer distribution (powers live leaderboard + post-game review).
- Postgres -> summary only: GameSession lifecycle + Participant final scores.

Anti-cheat: correct answers live only in Redis (server side). The payloads
built for *players* never include correctness until the reveal phase.
"""

from __future__ import annotations

import json
import secrets
import time
from typing import Any

import redis
from django.conf import settings
from django.utils import timezone

from .models import GameSession, Participant, Round

# --- tuning -----------------------------------------------------------------

CODE_ALPHABET = "0123456789"  # digits only
CODE_LENGTH = 6
MAX_PLAYERS = 30
SESSION_TTL = 6 * 60 * 60  # 6h auto-cleanup
STREAK_BONUS_RATE = 0.10  # per consecutive full-correct beyond the first
STREAK_BONUS_CAP = 0.50  # max bonus as a fraction of round points

# Phases
LOBBY = "lobby"
QUESTION = "question"
REVEAL = "reveal"
LEADERBOARD = "leaderboard"
ENDED = "ended"

# Supported question types in play (drag_answer deferred — no builder UI).
PLAYABLE_TYPES = {Round.SELECT_CORRECT, Round.TYPE_INPUT}


class LiveError(Exception):
    """User-facing problem (bad code, name taken, game started, full...)."""


_client: redis.Redis | None = None


def client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            health_check_interval=30,
        )
    return _client


# --- key helpers ------------------------------------------------------------


def _k(code: str, suffix: str) -> str:
    return f"quizlive:{code}:{suffix}"


def _touch_ttl(r: redis.Redis, code: str) -> None:
    for suffix in ("meta", "rounds", "participants"):
        r.expire(_k(code, suffix), SESSION_TTL)


def normalize_text(s: str) -> str:
    return (s or "").strip().lower()


# --- snapshot building ------------------------------------------------------


def _build_rounds_snapshot(quiz) -> list[dict[str, Any]]:
    """Freeze the quiz's playable rounds (+answers) into Redis-storable dicts.

    Correct answers are kept here (server side) and stripped before reaching
    player clients.
    """
    snapshot: list[dict[str, Any]] = []
    rounds = quiz.rounds.prefetch_related("answers").all()
    idx = 0
    for rnd in rounds:
        if rnd.question_type not in PLAYABLE_TYPES:
            continue  # drag_answer / anything unplayable is skipped
        answers = list(rnd.answers.all())
        entry: dict[str, Any] = {
            "idx": idx,
            "id": rnd.id,
            "question": rnd.question,
            "question_type": rnd.question_type,
            "points": rnd.points,
            "time_limit": rnd.time_limit,
            "image_url": rnd.image.url if rnd.image else "",
            "focus_x": rnd.focus_x,
            "focus_y": rnd.focus_y,
        }
        if rnd.question_type == Round.SELECT_CORRECT:
            entry["answers"] = [{"id": a.id, "text": a.text} for a in answers[:4]]
            entry["correct_ids"] = [a.id for a in answers[:4] if a.is_correct]
            # Single-select when exactly one correct option (radio vs checkbox).
            entry["single_select"] = len(entry["correct_ids"]) == 1
        else:  # TYPE_INPUT — any of several accepted answers
            entry["answers"] = []
            entry["accept_all"] = rnd.accept_all
            entry["correct_texts"] = [normalize_text(a.text) for a in answers if a.text.strip()]
        snapshot.append(entry)
        idx += 1
    return snapshot


# --- session lifecycle ------------------------------------------------------


def _gen_code(r: redis.Redis) -> str:
    """Allocate a code unique among *live* rooms. The atomic SET NX claim is the
    whole story: a code only needs to be unambiguous while a room is hosted, so
    once a room closes (claim freed) the code is free to reuse."""
    for _ in range(50):
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        if r.set(_k(code, "claim"), "1", nx=True, ex=SESSION_TTL):
            return code
    raise LiveError("Could not allocate a game code, try again.")


def create_session(quiz, host, show_question_on_device: bool) -> GameSession:
    """Create the PG summary row + initialise Redis live state. Returns session."""
    rounds = _build_rounds_snapshot(quiz)
    if not rounds:
        raise LiveError("This quiz has no playable rounds yet.")

    r = client()
    code = _gen_code(r)
    session = GameSession.objects.create(
        quiz=quiz,
        host=host,
        code=code,
        state=GameSession.LOBBY,
        show_question_on_device=show_question_on_device,
    )

    meta = {
        "session_id": str(session.id),
        "quiz_id": str(quiz.id),
        "quiz_title": quiz.title,
        "host_id": str(host.id),
        "phase": LOBBY,
        "current_round": "-1",
        "num_rounds": str(len(rounds)),
        "show_question": "1" if show_question_on_device else "0",
        "round_started_at": "",
    }
    pipe = r.pipeline()
    pipe.delete(_k(code, "meta"), _k(code, "rounds"), _k(code, "participants"))
    pipe.hset(_k(code, "meta"), mapping=meta)
    pipe.set(_k(code, "rounds"), json.dumps(rounds))
    pipe.execute()
    _touch_ttl(r, code)
    return session


def session_exists(code: str) -> bool:
    return bool(client().exists(_k(code, "meta")))


def set_host_channel(code: str, channel_name: str) -> None:
    """Record which WS channel is the live host (for grace-close on leave)."""
    r = client()
    if r.exists(_k(code, "meta")):
        r.hset(_k(code, "meta"), "host_channel", channel_name)
        _touch_ttl(r, code)


def host_channel(code: str) -> str | None:
    return client().hget(_k(code, "meta"), "host_channel")


def get_meta(code: str) -> dict[str, Any]:
    meta = client().hgetall(_k(code, "meta"))
    if not meta:
        raise LiveError("Game not found or has ended.")
    return meta


def _rounds(r: redis.Redis, code: str) -> list[dict[str, Any]]:
    raw = r.get(_k(code, "rounds"))
    return json.loads(raw) if raw else []


def rounds_meta(code: str) -> list[dict[str, Any]]:
    """Lightweight round list (idx/time_limit/points) for the consumer timer."""
    return [
        {"idx": rd["idx"], "time_limit": rd["time_limit"], "points": rd["points"]} for rd in _rounds(client(), code)
    ]


# --- participants -----------------------------------------------------------


def add_participant(code: str, nickname: str, user_id: int | None) -> str:
    """Validate + register a player while in the lobby. Returns participant token."""
    r = client()
    meta = get_meta(code)
    if meta.get("phase") != LOBBY:
        raise LiveError("This game has already started.")

    nickname = nickname.strip()
    if not nickname:
        raise LiveError("Please enter a nickname.")
    if len(nickname) > 30:
        nickname = nickname[:30]

    pkey = _k(code, "participants")
    existing = r.hgetall(pkey)
    if len(existing) >= MAX_PLAYERS:
        raise LiveError("This game is full.")
    for raw in existing.values():
        if normalize_text(json.loads(raw)["nickname"]) == normalize_text(nickname):
            raise LiveError("That nickname is taken, pick another.")

    # DB row gives a stable id for the final summary (session resolved by pk).
    participant = Participant.objects.create(session_id=int(meta["session_id"]), nickname=nickname, user_id=user_id)

    token = secrets.token_urlsafe(16)
    record = {
        "pk": participant.id,
        "nickname": nickname,
        "user_id": user_id,
        "score": 0,
        "streak": 0,
        "max_streak": 0,
    }
    r.hset(pkey, token, json.dumps(record))
    _touch_ttl(r, code)
    return token


def get_participant(code: str, token: str) -> dict[str, Any] | None:
    raw = client().hget(_k(code, "participants"), token)
    return json.loads(raw) if raw else None


def find_token_by_nickname(code: str, nickname: str) -> str | None:
    r = client()
    target = normalize_text(nickname)
    for tok, raw in r.hgetall(_k(code, "participants")).items():
        if normalize_text(json.loads(raw)["nickname"]) == target:
            return tok
    return None


def host_kick(code: str, nickname: str) -> str | None:
    """Host removes a player by nickname. Returns the kicked token (or None)."""
    token = find_token_by_nickname(code, nickname)
    if token:
        remove_participant(code, token)
    return token


def host_rename(code: str, nickname: str, new_name: str) -> None:
    """Host renames a player. Validates non-empty + unique within the session."""
    r = client()
    new_name = (new_name or "").strip()[:30]
    if not new_name:
        raise LiveError("Name cannot be empty.")
    token = find_token_by_nickname(code, nickname)
    if not token:
        raise LiveError("Player not found.")
    for tok, raw in r.hgetall(_k(code, "participants")).items():
        if tok != token and normalize_text(json.loads(raw)["nickname"]) == normalize_text(new_name):
            raise LiveError("That nickname is taken.")
    raw = r.hget(_k(code, "participants"), token)
    p = json.loads(raw)
    p["nickname"] = new_name
    r.hset(_k(code, "participants"), token, json.dumps(p))
    if p.get("pk"):
        Participant.objects.filter(pk=p["pk"]).update(nickname=new_name)
    _touch_ttl(r, code)


def remove_participant(code: str, token: str) -> None:
    """Player leaves: drop from Redis + DB summary, freeing the nickname."""
    r = client()
    raw = r.hget(_k(code, "participants"), token)
    if not raw:
        return
    pk = json.loads(raw).get("pk")
    r.hdel(_k(code, "participants"), token)
    if pk:
        Participant.objects.filter(pk=pk).delete()
    _touch_ttl(r, code)


def _all_participants(r: redis.Redis, code: str) -> dict[str, dict[str, Any]]:
    return {tok: json.loads(raw) for tok, raw in r.hgetall(_k(code, "participants")).items()}


def leaderboard(code: str) -> list[dict[str, Any]]:
    r = client()
    players = _all_participants(r, code).values()
    ranked = sorted(players, key=lambda p: (-p["score"], p["nickname"].lower()))
    return [
        {"rank": i + 1, "nickname": p["nickname"], "score": p["score"], "streak": p["streak"]}
        for i, p in enumerate(ranked)
    ]


def player_rank(code: str, token: str) -> int | None:
    me = get_participant(code, token)
    if not me:
        return None
    for row in leaderboard(code):
        if row["nickname"] == me["nickname"]:
            return row["rank"]
    return None


# --- play flow --------------------------------------------------------------


def start_game(code: str) -> None:
    r = client()
    meta = get_meta(code)
    if meta.get("phase") != LOBBY:
        return
    r.hset(
        _k(code, "meta"),
        mapping={"phase": QUESTION, "current_round": "0", "round_started_at": str(time.time())},
    )
    GameSession.objects.filter(pk=meta["session_id"]).update(state=GameSession.ACTIVE, started_at=timezone.now())
    _touch_ttl(r, code)


def set_show_question(code: str, show: bool) -> None:
    """Host toggle (lobby only): show question text on player devices."""
    r = client()
    meta = get_meta(code)
    if meta.get("phase") != LOBBY:
        return
    r.hset(_k(code, "meta"), "show_question", "1" if show else "0")
    GameSession.objects.filter(pk=meta["session_id"]).update(show_question_on_device=show)
    _touch_ttl(r, code)


def submit_answer(code: str, token: str, round_idx: int, value: Any) -> None:
    """Store/replace a player's answer. Allowed only during the active question."""
    r = client()
    meta = get_meta(code)
    if meta.get("phase") != QUESTION:
        raise LiveError("Answers are closed.")
    if int(meta.get("current_round", -1)) != round_idx:
        raise LiveError("That round is no longer active.")
    if not r.hexists(_k(code, "participants"), token):
        raise LiveError("You are not in this game.")
    r.hset(_k(code, f"answers:{round_idx}"), token, json.dumps({"value": value}))
    r.expire(_k(code, f"answers:{round_idx}"), SESSION_TTL)


def all_answered(code: str, round_idx: int) -> bool:
    """True when every participant has submitted for ``round_idx`` (≥1 player)."""
    r = client()
    total = r.hlen(_k(code, "participants"))
    if not total:
        return False
    return r.hlen(_k(code, f"answers:{round_idx}")) >= total


def _grade_one(round_def: dict[str, Any], value: Any) -> tuple[int, bool, bool]:
    """Return (base_points, is_full_correct, earned_any).

    base_points ignores the streak bonus (added later, full-correct only).
    """
    points = round_def["points"]
    qtype = round_def["question_type"]

    if qtype == Round.SELECT_CORRECT:
        correct = set(round_def.get("correct_ids", []))
        picked = set(value or []) if isinstance(value, list) else set()
        if not correct:
            return 0, False, False
        right = len(picked & correct)
        base = int(round(points * right / len(correct)))
        is_full = picked == correct
        return base, is_full, base > 0

    if qtype == Round.TYPE_INPUT:
        if round_def.get("accept_all"):
            # Open question: any non-empty submission is full-correct.
            answered = isinstance(value, str) and value.strip() != ""
            return (points, True, True) if answered else (0, False, False)
        ok = isinstance(value, str) and normalize_text(value) in round_def.get("correct_texts", [])
        return (points, True, True) if ok else (0, False, False)

    return 0, False, False


def lock_and_grade(code: str, round_idx: int) -> None:
    """Grade everyone for ``round_idx``, update scores/streaks, enter REVEAL.

    Idempotent: a second call (timer + manual reveal race) is a no-op.
    """
    r = client()
    meta = get_meta(code)
    if meta.get("phase") == REVEAL and int(meta.get("current_round", -1)) == round_idx:
        return  # already revealed
    rounds = _rounds(r, code)
    if round_idx >= len(rounds):
        return
    round_def = rounds[round_idx]

    answers = {tok: json.loads(raw).get("value") for tok, raw in r.hgetall(_k(code, f"answers:{round_idx}")).items()}
    participants = _all_participants(r, code)
    graded: dict[str, dict[str, Any]] = {}
    pipe = r.pipeline()

    for token, p in participants.items():
        value = answers.get(token)
        base, is_full, earned = _grade_one(round_def, value)

        if is_full:
            p["streak"] = p["streak"] + 1
            bonus_frac = min(STREAK_BONUS_RATE * (p["streak"] - 1), STREAK_BONUS_CAP)
            bonus = int(round(round_def["points"] * bonus_frac))
        elif earned:
            bonus = 0  # partial: streak held, no bonus
        else:
            p["streak"] = 0
            bonus = 0

        awarded = base + bonus
        p["score"] += awarded
        p["max_streak"] = max(p["max_streak"], p["streak"])
        pipe.hset(_k(code, "participants"), token, json.dumps(p))
        graded[token] = {
            "points": awarded,
            "base": base,
            "bonus": bonus,
            "full": is_full,
            "earned": earned,
        }

    pipe.set(_k(code, f"graded:{round_idx}"), json.dumps(graded))
    pipe.expire(_k(code, f"graded:{round_idx}"), SESSION_TTL)
    pipe.hset(_k(code, "meta"), "phase", REVEAL)
    pipe.execute()
    _touch_ttl(r, code)


def _distribution(r: redis.Redis, code: str, round_def: dict[str, Any], round_idx: int) -> dict[str, Any]:
    """Answer breakdown for the reveal screen (host/projector)."""
    answers = [json.loads(raw).get("value") for raw in r.hgetall(_k(code, f"answers:{round_idx}")).values()]
    if round_def["question_type"] == Round.SELECT_CORRECT:
        counts = {a["id"]: 0 for a in round_def["answers"]}
        for value in answers:
            for aid in value or []:
                if aid in counts:
                    counts[aid] += 1
        return {"type": Round.SELECT_CORRECT, "counts": counts, "answered": len(answers)}
    # type_input: how many got it right vs wrong (accept_all => every entry is right)
    if round_def.get("accept_all"):
        answered = sum(1 for v in answers if isinstance(v, str) and v.strip())
        return {"type": Round.TYPE_INPUT, "right": answered, "wrong": 0, "answered": len(answers)}
    right = sum(1 for v in answers if isinstance(v, str) and normalize_text(v) in round_def.get("correct_texts", []))
    return {
        "type": Round.TYPE_INPUT,
        "right": right,
        "wrong": len(answers) - right,
        "answered": len(answers),
    }


def _answers_list(r: redis.Redis, code: str, round_idx: int) -> list[dict[str, Any]]:
    """Every player's submitted text for ``round_idx`` (accept_all reveal)."""
    raw_answers = r.hgetall(_k(code, f"answers:{round_idx}"))
    participants = _all_participants(r, code)
    out: list[dict[str, Any]] = []
    for token, p in participants.items():
        raw = raw_answers.get(token)
        value = json.loads(raw).get("value") if raw else None
        text = value if isinstance(value, str) else ""
        out.append({"nickname": p["nickname"], "text": text})
    out.sort(key=lambda x: x["nickname"].lower())
    return out


def advance(code: str) -> str:
    """Host "Next" step. Returns the new phase.

    REVEAL -> LEADERBOARD (standings for the round just played, same round).
    LEADERBOARD -> next QUESTION, or ENDED after the last round.
    """
    r = client()
    meta = get_meta(code)
    phase = meta.get("phase")

    if phase == REVEAL:
        r.hset(_k(code, "meta"), "phase", LEADERBOARD)
        _touch_ttl(r, code)
        return LEADERBOARD

    rounds = _rounds(r, code)
    current = int(meta.get("current_round", -1))
    nxt = current + 1
    if nxt >= len(rounds):
        end_game(code)
        return ENDED
    r.hset(
        _k(code, "meta"),
        mapping={"phase": QUESTION, "current_round": str(nxt), "round_started_at": str(time.time())},
    )
    _touch_ttl(r, code)
    return QUESTION


def close_room(code: str) -> None:
    """Terminate the session entirely: persist the summary, then wipe all live
    state from Redis so the room no longer exists."""
    r = client()
    rounds = _rounds(r, code)
    end_game(code)  # persist final scores + mark ended (idempotent)
    # Drop the claim too so the code becomes available for reuse right away.
    keys = [_k(code, "meta"), _k(code, "rounds"), _k(code, "participants"), _k(code, "claim")]
    for i in range(len(rounds)):
        keys += [_k(code, f"answers:{i}"), _k(code, f"graded:{i}")]
    r.delete(*keys)


def end_game(code: str) -> None:
    """Enter ENDED and flush the summary (final scores) to Postgres."""
    r = client()
    meta = client().hgetall(_k(code, "meta"))
    if not meta or meta.get("phase") == ENDED:
        return
    r.hset(_k(code, "meta"), "phase", ENDED)

    participants = _all_participants(r, code)
    to_update = []
    for p in participants.values():
        try:
            obj = Participant.objects.get(pk=p["pk"])
        except Participant.DoesNotExist:
            continue
        obj.final_score = p["score"]
        obj.max_streak = p["max_streak"]
        to_update.append(obj)
    if to_update:
        Participant.objects.bulk_update(to_update, ["final_score", "max_streak"])
    if meta.get("session_id"):
        GameSession.objects.filter(pk=meta["session_id"]).update(state=GameSession.ENDED, ended_at=timezone.now())
    _touch_ttl(r, code)


# --- payload builders (what gets pushed over the wire) ----------------------


def _public_round(round_def: dict[str, Any], show_question: bool) -> dict[str, Any]:
    """Round info safe to send to a player mid-question (no correctness)."""
    data = {
        "idx": round_def["idx"],
        "question_type": round_def["question_type"],
        "points": round_def["points"],
        "time_limit": round_def["time_limit"],
        "single_select": round_def.get("single_select", False),
        "answers": [{"id": a["id"], "text": a["text"]} for a in round_def.get("answers", [])],
    }
    if show_question:
        data["question"] = round_def["question"]
        data["image_url"] = round_def.get("image_url", "")
        data["focus_x"] = round_def.get("focus_x", 50)
        data["focus_y"] = round_def.get("focus_y", 50)
    return data


def state_payload(code: str, *, role: str, token: str | None = None) -> dict[str, Any]:
    """Full current-state snapshot for a freshly (re)connected client."""
    r = client()
    meta = get_meta(code)
    phase = meta.get("phase", LOBBY)
    show_q = meta.get("show_question") == "1"
    is_host = role == "host"
    current = int(meta.get("current_round", -1))
    rounds = _rounds(r, code)

    payload: dict[str, Any] = {
        "type": "state",
        "phase": phase,
        "code": code,
        "quiz_title": meta.get("quiz_title", ""),
        "num_rounds": int(meta.get("num_rounds", 0)),
        "current_round": current,
        "show_question": show_q,
        "players": [p["nickname"] for p in _all_participants(r, code).values()],
    }

    if phase in (QUESTION, REVEAL) and 0 <= current < len(rounds):
        rdef = rounds[current]
        if is_host or show_q:
            payload["round"] = {
                "idx": rdef["idx"],
                "question": rdef["question"],
                "question_type": rdef["question_type"],
                "points": rdef["points"],
                "time_limit": rdef["time_limit"],
                "image_url": rdef.get("image_url", ""),
                "focus_x": rdef.get("focus_x", 50),
                "focus_y": rdef.get("focus_y", 50),
                "single_select": rdef.get("single_select", False),
                "answers": [{"id": a["id"], "text": a["text"]} for a in rdef.get("answers", [])],
            }
        else:
            payload["round"] = _public_round(rdef, show_q)
        payload["round_started_at"] = float(meta["round_started_at"]) if meta.get("round_started_at") else None

    if phase == QUESTION and token:
        existing = r.hget(_k(code, f"answers:{current}"), token)
        payload["my_answer"] = json.loads(existing).get("value") if existing else None

    if phase == REVEAL and 0 <= current < len(rounds):
        payload["reveal"] = reveal_payload(code, current, role=role, token=token)

    if phase in (REVEAL, LEADERBOARD, ENDED):
        payload["leaderboard"] = leaderboard(code)

    if phase in (LEADERBOARD, ENDED) and token:
        me = get_participant(code, token)
        if me:
            payload["me"] = {
                "nickname": me["nickname"],
                "score": me["score"],
                "rank": player_rank(code, token),
            }

    if phase == ENDED:
        payload["final"] = True

    return payload


def reveal_payload(code: str, round_idx: int, *, role: str, token: str | None = None) -> dict[str, Any]:
    r = client()
    rounds = _rounds(r, code)
    rdef = rounds[round_idx]
    out: dict[str, Any] = {
        "round_idx": round_idx,
        "question_type": rdef["question_type"],
    }
    if rdef["question_type"] == Round.SELECT_CORRECT:
        out["correct_ids"] = rdef.get("correct_ids", [])
    else:
        out["correct_texts"] = rdef.get("correct_texts", [])
        out["accept_all"] = rdef.get("accept_all", False)
    # host/projector gets the distribution (+ every participant's submission for
    # type_input: open questions show them outright, graded ones on host demand)
    if role == "host":
        out["distribution"] = _distribution(r, code, rdef, round_idx)
        if rdef["question_type"] == Round.TYPE_INPUT:
            out["answers_list"] = _answers_list(r, code, round_idx)
    # player gets their own result
    if token:
        graded_raw = r.get(_k(code, f"graded:{round_idx}"))
        graded = json.loads(graded_raw) if graded_raw else {}
        mine = graded.get(token, {"points": 0, "full": False, "earned": False})
        me = get_participant(code, token)
        out["me"] = {
            "points": mine["points"],
            "full": mine["full"],
            "earned": mine["earned"],
            "score": me["score"] if me else 0,
            "streak": me["streak"] if me else 0,
            "rank": player_rank(code, token),
        }
        if rdef.get("accept_all"):
            ans_raw = r.hget(_k(code, f"answers:{round_idx}"), token)
            value = json.loads(ans_raw).get("value") if ans_raw else None
            out["me"]["your_answer"] = value if isinstance(value, str) else ""
    return out


def round_review(code: str, round_idx: int) -> dict[str, Any]:
    """Per-question post-game review for the host (ephemeral, Redis-backed)."""
    r = client()
    rounds = _rounds(r, code)
    if not (0 <= round_idx < len(rounds)):
        raise LiveError("No such round.")
    rdef = rounds[round_idx]
    data = {
        "round_idx": round_idx,
        "question": rdef["question"],
        "question_type": rdef["question_type"],
        "answers": rdef.get("answers", []),
        "correct_ids": rdef.get("correct_ids", []),
        "correct_texts": rdef.get("correct_texts", []),
        "accept_all": rdef.get("accept_all", False),
        "distribution": _distribution(r, code, rdef, round_idx),
    }
    if rdef.get("accept_all"):
        data["answers_list"] = _answers_list(r, code, round_idx)
    return data
