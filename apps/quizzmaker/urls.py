from django.urls import path

from .views import (
    AnswerUpdateView,
    HomeView,
    QuizCreateView,
    QuizFinalizeView,
    QuizUpdateView,
    RoundCreateView,
    RoundDeleteView,
    RoundEditorView,
    RoundReorderView,
    RoundUpdateView,
)

app_name = "quizzmaker"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("create/", QuizCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", QuizUpdateView.as_view(), name="edit"),
    path("<int:pk>/rounds/", RoundEditorView.as_view(), name="rounds"),
    path("<int:pk>/rounds/new/", RoundCreateView.as_view(), name="round_create"),
    path(
        "<int:pk>/rounds/<int:round_pk>/edit/",
        RoundUpdateView.as_view(),
        name="round_edit",
    ),
    path(
        "<int:pk>/rounds/<int:round_pk>/delete/",
        RoundDeleteView.as_view(),
        name="round_delete",
    ),
    path(
        "<int:pk>/rounds/reorder/",
        RoundReorderView.as_view(),
        name="round_reorder",
    ),
    path(
        "<int:pk>/answers/<int:answer_pk>/",
        AnswerUpdateView.as_view(),
        name="answer_update",
    ),
    path(
        "<int:pk>/finalize/",
        QuizFinalizeView.as_view(),
        name="quiz_finalize",
    ),
]
