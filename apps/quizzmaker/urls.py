from django.urls import path

from .views import (
    AnswerCreateView,
    AnswerDeleteView,
    AnswerUpdateView,
    HomeView,
    HostSessionCreateView,
    JoinView,
    LeaveSessionView,
    QuizCreateView,
    QuizDeleteView,
    QuizFinalizeView,
    QuizUpdateView,
    RoundCopyTimeView,
    RoundCreateView,
    RoundDeleteView,
    RoundEditorView,
    RoundReorderView,
    RoundUpdateView,
    SessionHostView,
    SessionPlayView,
)

app_name = "quizzmaker"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    # Live play
    path("join/", JoinView.as_view(), name="join"),
    path("join/<str:code>/", JoinView.as_view(), name="join_code"),
    path("<int:pk>/host/", HostSessionCreateView.as_view(), name="host_create"),
    path("session/<str:code>/host/", SessionHostView.as_view(), name="session_host"),
    path("session/<str:code>/play/", SessionPlayView.as_view(), name="session_play"),
    path("session/<str:code>/leave/", LeaveSessionView.as_view(), name="session_leave"),
    path("create/", QuizCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", QuizUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", QuizDeleteView.as_view(), name="delete"),
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
        "<int:pk>/rounds/<int:round_pk>/copy-time/",
        RoundCopyTimeView.as_view(),
        name="round_copy_time",
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
        "<int:pk>/rounds/<int:round_pk>/answers/new/",
        AnswerCreateView.as_view(),
        name="answer_create",
    ),
    path(
        "<int:pk>/answers/<int:answer_pk>/delete/",
        AnswerDeleteView.as_view(),
        name="answer_delete",
    ),
    path(
        "<int:pk>/finalize/",
        QuizFinalizeView.as_view(),
        name="quiz_finalize",
    ),
]
