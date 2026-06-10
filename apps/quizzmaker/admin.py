from django.contrib import admin

from .models import Answer, GameSession, Participant, Quiz, Round


class RoundInline(admin.TabularInline):
    model = Round
    extra = 0
    fields = ("order", "question", "question_type", "points", "time_limit")
    ordering = ("order", "id")


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ("order", "text", "is_correct")
    ordering = ("order", "id")


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0
    fields = ("nickname", "user", "final_score", "max_streak")
    ordering = ("-final_score", "id")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "visibility", "total_points", "expected_duration", "saved_count", "created_at")
    list_filter = ("visibility", "created_at")
    search_fields = ("title", "user__email", "user__username")
    inlines = [RoundInline]


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ("quiz", "order", "question_type", "points", "time_limit")
    list_filter = ("question_type",)
    search_fields = ("question", "quiz__title")
    ordering = ("quiz", "order")
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("round", "order", "text", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("text", "round__quiz__title")


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "code", "host", "state", "started_at", "ended_at", "created_at")
    list_filter = ("state", "created_at")
    search_fields = ("code", "quiz__title", "host__email")
    inlines = [ParticipantInline]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("nickname", "session", "user", "final_score", "max_streak")
    search_fields = ("nickname", "session__code", "user__email")
