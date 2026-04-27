import math

from django.db import models

from apps.core.models import TimestampedModel, UserOwnedModel


class Quiz(UserOwnedModel):
    PUBLIC = "public"
    PRIVATE = "private"
    VISIBILITY_CHOICES = [
        (PUBLIC, "Public"),
        (PRIVATE, "Private"),
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
        (SELECT_CORRECT, "Pick the correct answer"),
        (TYPE_INPUT, "Write the answer"),
        (DRAG_ANSWER, "Drag the answer into the blank"),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="rounds")
    question = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default=SELECT_CORRECT)
    points = models.IntegerField(default=0)
    time_limit = models.IntegerField(default=0, help_text="Time limit in seconds (0 = no limit)")
    image = models.ImageField(upload_to="uploads/quizzmaker/rounds/", blank=True, null=True)
    focus_x = models.PositiveSmallIntegerField(default=50)
    focus_y = models.PositiveSmallIntegerField(default=50)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.quiz.title} - Round {self.order}"


class Answer(TimestampedModel):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Round {self.round.order}: {self.text}"
