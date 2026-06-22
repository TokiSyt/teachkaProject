import math

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel, UserOwnedModel


class Quiz(UserOwnedModel):
    PUBLIC = "public"
    PRIVATE = "private"
    VISIBILITY_CHOICES = [
        (PUBLIC, _("Public")),
        (PRIVATE, _("Private")),
    ]

    title = models.CharField(max_length=100)
    total_points = models.IntegerField(default=0)
    logo = models.ImageField(upload_to="uploads/quizzmaker/logos/", blank=True, null=True)
    focus_x = models.PositiveSmallIntegerField(default=50)
    focus_y = models.PositiveSmallIntegerField(default=50)
    visibility = models.CharField(max_length=7, choices=VISIBILITY_CHOICES, default=PUBLIC)
    saved_count = models.IntegerField(default=0)
    expected_duration = models.IntegerField(default=1, help_text="Expected duration in minutes")

    class Meta:
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title

    def recalculate_totals(self, save=True):
        rounds = list(self.rounds.all())
        self.total_points = sum(r.points for r in rounds)
        total_seconds = sum(r.time_limit for r in rounds)
        self.expected_duration = max(1, math.ceil(total_seconds / 60)) if total_seconds else 1
        if save:
            self.save(update_fields=["total_points", "expected_duration"])


class Round(TimestampedModel):
    SELECT_CORRECT = "select_correct"
    TYPE_INPUT = "type_input"
    DRAG_ANSWER = "drag_answer"
    QUESTION_TYPE_CHOICES = [
        (SELECT_CORRECT, _("Pick the correct answer")),
        (TYPE_INPUT, _("Write the answer")),
        (DRAG_ANSWER, _("Drag the answer into the blank")),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="rounds")
    question = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default=SELECT_CORRECT)
    points = models.IntegerField(default=0)
    time_limit = models.IntegerField(default=0, help_text="Time limit in seconds (0 = no limit)")
    accept_all = models.BooleanField(
        default=False,
        help_text="type_input only: accept every submitted answer as correct (open question).",
    )
    image = models.ImageField(upload_to="uploads/quizzmaker/rounds/", blank=True, null=True)
    focus_x = models.PositiveSmallIntegerField(default=50)
    focus_y = models.PositiveSmallIntegerField(default=50)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.quiz.title} - Round {self.order}"

    @property
    def has_correct_answer(self) -> bool:
        """Whether this round's correct answer is defined (so it can be played)."""
        if self.question_type == self.SELECT_CORRECT:
            return any(a.is_correct for a in self.answers.all())
        if self.question_type == self.TYPE_INPUT:
            # accept_all makes the round playable without any defined answer.
            return self.accept_all or any(a.text.strip() for a in self.answers.all())
        return False


class Answer(TimestampedModel):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Round {self.round.order}: {self.text}"


class GameSession(TimestampedModel):
    """A live, teacher-hosted play-through of a quiz.

    Authoritative live state lives in Redis (see ``live.LiveStore``); this row
    is the persisted *summary*: who hosted, the join code, and lifecycle
    timestamps. Per-round answer detail is intentionally not persisted.
    """

    LOBBY = "lobby"
    ACTIVE = "active"
    ENDED = "ended"
    STATE_CHOICES = [
        (LOBBY, "Lobby"),
        (ACTIVE, "Active"),
        (ENDED, "Ended"),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="sessions")
    host = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE, related_name="hosted_sessions")
    code = models.CharField(max_length=8, db_index=True)
    state = models.CharField(max_length=8, choices=STATE_CHOICES, default=LOBBY)
    show_question_on_device = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.quiz.title} [{self.code}]"


class Participant(TimestampedModel):
    """A player in a GameSession. ``user`` is optional (guests play by nickname)."""

    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="participants")
    nickname = models.CharField(max_length=30)
    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quiz_participations",
    )
    final_score = models.IntegerField(default=0)
    max_streak = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-final_score", "id"]
        constraints = [
            models.UniqueConstraint(fields=["session", "nickname"], name="unique_nickname_per_session"),
        ]

    def __str__(self):
        return f"{self.nickname} @ {self.session.code}"
