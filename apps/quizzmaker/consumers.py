"""WebSocket consumer for live quiz sessions.

State changes broadcast a lightweight ``refresh`` to the session group; every
connected socket then rebuilds *its own* role/token-specific snapshot via
``live.state_payload``. This keeps correct answers off player wires until the
reveal phase and lets each player see their own per-round result.
"""

from __future__ import annotations

import asyncio
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from . import live

HOST = "host"
PLAYER = "player"

# Seconds to wait after the host's socket drops before tearing the room down.
# A refresh reconnects (and reclaims host_channel) well within this window;
# a real leave does not, so the room is closed and Redis state freed.
HOST_GRACE = 12

# Keep references to detached grace-close tasks so they aren't GC'd mid-sleep.
_grace_tasks: set = set()


class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.code = self.scope["url_route"]["kwargs"]["code"]
        self.group = f"quiz_{self.code}"
        self.token: str | None = None
        self.role: str | None = None
        self._lock_task: asyncio.Task | None = None

        meta = await self._safe(live.get_meta, self.code)
        if meta is None:
            await self.close(code=4004)
            return

        user = self.scope.get("user")
        if user and user.is_authenticated and str(user.id) == meta.get("host_id"):
            self.role = HOST
        else:
            token = self.scope.get("cookies", {}).get(f"quiz_token_{self.code}")
            if token and await self._safe(live.get_participant, self.code, token):
                self.role = PLAYER
                self.token = token

        if self.role is None:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_state()

        # Host owns the round timer; (re)arm it on connect if a timed question
        # is already running (survives host refresh). Also claim host_channel so
        # a stale grace-close from a previous host socket won't fire.
        if self.role == HOST:
            await self._safe(live.set_host_channel, self.code, self.channel_name)
            await self._maybe_arm_timer()
            # Host (re)connected: resync everyone (clears any "host left" notice).
            await self.broadcast_refresh()
        else:
            # A player (re)connected — tell everyone so the host's roster + count
            # update live without a refresh.
            await self.broadcast_refresh()

    async def disconnect(self, code):
        if self._lock_task:
            self._lock_task.cancel()
        if getattr(self, "group", None):
            await self.channel_layer.group_discard(self.group, self.channel_name)
        # Host left: tell players immediately, then close the room after a grace
        # window unless the host reconnects.
        if self.role == HOST:
            await self.channel_layer.group_send(self.group, {"type": "host_left"})
            task = asyncio.create_task(self._grace_close())
            _grace_tasks.add(task)
            task.add_done_callback(_grace_tasks.discard)

    async def _grace_close(self):
        await asyncio.sleep(HOST_GRACE)
        # If another host socket reclaimed host_channel, a reconnect happened.
        if await self._safe(live.host_channel, self.code) != self.channel_name:
            return
        if not await self._safe(live.session_exists, self.code):
            return
        await self._safe(live.close_room, self.code)
        await self.channel_layer.group_send(self.group, {"type": "closed"})

    # --- inbound ----------------------------------------------------------

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if self.role == HOST:
            await self._host_action(action, content)
        elif self.role == PLAYER:
            await self._player_action(action, content)

    async def _host_action(self, action, content):
        if action == "start":
            await self._safe(live.start_game, self.code)
            await self.broadcast_refresh()
            await self._maybe_arm_timer()
        elif action == "reveal":
            await self._reveal_current()
        elif action == "next":
            phase = await self._safe(live.advance, self.code)
            await self.broadcast_refresh()
            if phase == live.QUESTION:
                await self._maybe_arm_timer()
        elif action == "end":
            await self._safe(live.end_game, self.code)
            await self.broadcast_refresh()
        elif action == "set_show_question":
            await self._safe(live.set_show_question, self.code, bool(content.get("value")))
            await self.broadcast_refresh()
        elif action == "close":
            await self._safe(live.close_room, self.code)
            await self.channel_layer.group_send(self.group, {"type": "closed"})
        elif action == "kick":
            token = await self._safe(live.host_kick, self.code, content.get("nickname"))
            if token:
                await self.channel_layer.group_send(self.group, {"type": "player_kicked", "token": token})
                await self.broadcast_refresh()
        elif action == "rename":
            try:
                await database_sync_to_async(live.host_rename)(
                    self.code, content.get("nickname"), content.get("new_name", "")
                )
            except live.LiveError as exc:
                await self.send_json({"type": "error", "message": str(exc)})
                return
            await self.broadcast_refresh()
        elif action == "review":
            try:
                idx = int(content.get("round_idx"))
            except (TypeError, ValueError):
                return
            data = await self._safe(live.round_review, self.code, idx)
            if data is not None:
                await self.send_json({"type": "review", **data})

    async def _player_action(self, action, content):
        if action != "answer":
            return
        try:
            round_idx = int(content.get("round_idx"))
        except (TypeError, ValueError):
            return
        value = content.get("value")
        try:
            await database_sync_to_async(live.submit_answer)(self.code, self.token, round_idx, value)
        except live.LiveError as exc:
            await self.send_json({"type": "error", "message": str(exc)})
            return
        await self.send_json({"type": "answer_ack", "round_idx": round_idx, "value": value})
        # Everyone answered -> end the round now instead of waiting for the timer
        # or a manual reveal. lock_and_grade is idempotent, so a timer/manual
        # race is harmless.
        if await self._safe(live.all_answered, self.code, round_idx):
            await self._reveal_current()

    # --- round timer ------------------------------------------------------

    async def _maybe_arm_timer(self):
        meta = await self._safe(live.get_meta, self.code)
        if not meta or meta.get("phase") != live.QUESTION:
            return
        rounds = await self._safe(live.rounds_meta, self.code)
        current = int(meta.get("current_round", -1))
        if rounds is None or not (0 <= current < len(rounds)):
            return
        time_limit = rounds[current]["time_limit"]
        if not time_limit:  # 0 = untimed; host reveals manually
            return
        started = float(meta["round_started_at"]) if meta.get("round_started_at") else time.time()
        remaining = max(0.0, started + time_limit - time.time())
        if self._lock_task:
            self._lock_task.cancel()
        self._lock_task = asyncio.create_task(self._auto_lock(current, remaining))

    async def _auto_lock(self, round_idx, delay):
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        meta = await self._safe(live.get_meta, self.code)
        if meta and meta.get("phase") == live.QUESTION and int(meta.get("current_round", -1)) == round_idx:
            await self._reveal_current()

    async def _reveal_current(self):
        meta = await self._safe(live.get_meta, self.code)
        if not meta or meta.get("phase") != live.QUESTION:
            return
        current = int(meta.get("current_round", -1))
        await database_sync_to_async(live.lock_and_grade)(self.code, current)
        # Cancel the pending timer, but never the task we're running inside
        # (that would abort the broadcast below).
        task, self._lock_task = self._lock_task, None
        if task and task is not asyncio.current_task():
            task.cancel()
        await self.broadcast_refresh()

    # --- broadcast / state ------------------------------------------------

    async def broadcast_refresh(self):
        await self.channel_layer.group_send(self.group, {"type": "refresh"})

    async def refresh(self, event):
        await self.send_state()

    async def closed(self, event):
        await self.send_json({"type": "closed"})

    async def player_kicked(self, event):
        # The kicked player is told to leave; everyone else ignores it.
        if self.role == PLAYER and self.token == event.get("token"):
            await self.send_json({"type": "closed"})

    async def host_left(self, event):
        if self.role == PLAYER:
            await self.send_json({"type": "host_left"})

    async def send_state(self):
        payload = await database_sync_to_async(live.state_payload)(self.code, role=self.role, token=self.token)
        await self.send_json(payload)

    # --- helpers ----------------------------------------------------------

    async def _safe(self, fn, *args):
        try:
            return await database_sync_to_async(fn)(*args)
        except live.LiveError:
            return None
