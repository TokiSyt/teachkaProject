import calendar
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from apps.core.mixins import FormUserMixin, UserOwnedMixin

from .forms import EventForm
from .models import Event
from .services.calendar_service import get_events_for_day, get_events_for_month


# defaults to monthly view
class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = "calendar/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = date.today()
        try:
            year = int(self.request.GET.get("year", today.year))
            month = int(self.request.GET.get("month", today.month))
        except (TypeError, ValueError):
            year, month = today.year, today.month

        year, month = _clamp_month(year, month)

        raw_map = get_events_for_month(self.request.user, year, month)
        events_by_day = {d.day: evs for d, evs in raw_map.items()}
        full_grid = _build_full_grid(year, month)
        # Each cell: (date_obj, is_current_month, events_list)
        weeks = [
            [
                (cell_date, is_current, events_by_day.get(cell_date.day, []) if is_current else [])
                for cell_date, is_current in week
            ]
            for week in full_grid
        ]

        prev_year, prev_month = _prev_month(year, month)
        next_year, next_month = _next_month(year, month)

        ctx.update(
            {
                "year": year,
                "month": month,
                "month_name": calendar.month_name[month],
                "weeks": weeks,
                "today": today,
                "prev_year": prev_year,
                "prev_month": prev_month,
                "next_year": next_year,
                "next_month": next_month,
                "weekday_headers": list(calendar.day_abbr),
            }
        )
        return ctx


class DayDetailView(LoginRequiredMixin, TemplateView):
    template_name = "calendar/day_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            day = date(int(kwargs["year"]), int(kwargs["month"]), int(kwargs["day"]))
        except (ValueError, KeyError) as exc:
            raise Http404("Invalid date") from exc

        prev_day = day - timedelta(days=1)
        next_day = day + timedelta(days=1)

        ctx.update(
            {
                "day": day,
                "events": get_events_for_day(self.request.user, day),
                "prev_day": prev_day,
                "next_day": next_day,
                "today": date.today(),
            }
        )
        return ctx


class WeekDetailView(LoginRequiredMixin, TemplateView):
    template_name = "calendar/week_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            anchor = date(int(kwargs["year"]), int(kwargs["month"]), int(kwargs["day"]))
        except (ValueError, KeyError) as exc:
            raise Http404("Invalid date") from exc

        week_start = anchor - timedelta(days=anchor.weekday())
        week_end = week_start + timedelta(days=6)
        prev_start = week_start - timedelta(days=7)
        next_start = week_start + timedelta(days=7)

        days = [
            {
                "date": week_start + timedelta(days=i),
                "events": get_events_for_day(self.request.user, week_start + timedelta(days=i)),
            }
            for i in range(7)
        ]

        iso_year, iso_week, _ = week_start.isocalendar()

        ctx.update(
            {
                "week_start": week_start,
                "week_end": week_end,
                "prev_start": prev_start,
                "next_start": next_start,
                "days": days,
                "today": date.today(),
                "iso_year": iso_year,
                "iso_week": iso_week,
            }
        )
        return ctx


class EventCreateView(FormUserMixin, LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "calendar/event_form.html"

    def _safe_next(self) -> str | None:
        candidate = self.request.GET.get("next") or self.request.POST.get("next")
        if candidate and url_has_allowed_host_and_scheme(
            candidate, allowed_hosts={self.request.get_host()}, require_https=self.request.is_secure()
        ):
            return candidate
        return None

    def get_initial(self):
        today = date.today()
        return {
            "start_datetime": today.strftime("%Y-%m-%dT00:00"),
            "end_datetime": today.strftime("%Y-%m-%dT23:59"),
        }

    def get_success_url(self):
        nxt = self._safe_next()
        if nxt:
            return nxt
        ev: Event = self.object
        d = ev.start_datetime.date()
        return reverse_lazy("calendar_app:home") + f"?year={d.year}&month={d.month}"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] = "Create"
        ctx["cancel_url"] = self._safe_next() or reverse_lazy("calendar_app:home")
        return ctx


class EventUpdateView(UserOwnedMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "calendar/event_form.html"

    def _safe_next(self) -> str | None:
        candidate = self.request.GET.get("next") or self.request.POST.get("next")
        if candidate and url_has_allowed_host_and_scheme(
            candidate, allowed_hosts={self.request.get_host()}, require_https=self.request.is_secure()
        ):
            return candidate
        return None

    def get_success_url(self):
        nxt = self._safe_next()
        if nxt:
            return nxt
        ev: Event = self.object
        d = ev.start_datetime.date()
        return reverse_lazy("calendar_app:home") + f"?year={d.year}&month={d.month}"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] = "Edit"
        ctx["cancel_url"] = self._safe_next() or reverse_lazy("calendar_app:home")
        return ctx


class EventDeleteView(UserOwnedMixin, DeleteView):  # type: ignore[misc]
    model = Event
    template_name = "calendar/event_confirm_delete.html"

    def get_success_url(self):
        ev: Event = self.object
        d = ev.start_datetime.date()
        return reverse_lazy("calendar_app:home") + f"?year={d.year}&month={d.month}"


def _build_full_grid(year: int, month: int) -> list[list[tuple[date, bool]]]:
    """Return (date, is_current_month) for every cell in the calendar grid."""
    first_day = date(year, month, 1)
    raw_weeks = calendar.monthcalendar(year, month)
    leading_zeros = next(i for i, d in enumerate(raw_weeks[0]) if d != 0)
    grid_start = first_day - timedelta(days=leading_zeros)

    full_grid = []
    current = grid_start
    for _week in raw_weeks:
        week_cells = [(current + timedelta(days=i), (current + timedelta(days=i)).month == month) for i in range(7)]
        full_grid.append(week_cells)
        current += timedelta(days=7)
    return full_grid


def _clamp_month(year: int, month: int) -> tuple[int, int]:
    if month < 1:
        month = 1
    elif month > 12:
        month = 12
    return year, month


def _prev_month(year: int, month: int) -> tuple[int, int]:
    month -= 1
    if month == 0:
        month = 12
        year -= 1
    return year, month


def _next_month(year: int, month: int) -> tuple[int, int]:
    month += 1
    if month == 13:
        month = 1
        year += 1
    return year, month
