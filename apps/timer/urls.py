from django.urls import path

from .views import HomeView, StopwatchView, TimerView

app_name = "timer"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("stopwatch/", StopwatchView.as_view(), name="stopwatch"),
    path("countdown/", TimerView.as_view(), name="countdown"),
]
