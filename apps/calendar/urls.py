from django.urls import path

from .views import (
    CalendarView,
    DayDetailView,
    EventCreateView,
    EventDeleteView,
    EventUpdateView,
    WeekDetailView,
)

app_name = "calendar_app"

urlpatterns = [
    path("", CalendarView.as_view(), name="home"),
    path("day/<int:year>/<int:month>/<int:day>/", DayDetailView.as_view(), name="day_detail"),
    path("week/<int:year>/<int:month>/<int:day>/", WeekDetailView.as_view(), name="week_detail"),
    path("event/new/", EventCreateView.as_view(), name="event_create"),
    path("event/<int:pk>/edit/", EventUpdateView.as_view(), name="event_edit"),
    path("event/<int:pk>/delete/", EventDeleteView.as_view(), name="event_delete"),
]
