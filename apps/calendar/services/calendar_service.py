import calendar
from datetime import date, timedelta

from apps.calendar.models import Event


def expand_recurring(event: Event, year: int, month: int) -> list[date]:
    """Return all dates in (year, month) where the recurring event falls."""
    _, days_in_month = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)

    recurrence_end = event.recurrence_end or date(year + 10, 1, 1)
    event_start = event.start_datetime.date()

    result: list[date] = []

    if event.recurrence == Event.RECURRENCE_DAILY:
        cur = max(month_start, event_start)
        while cur <= month_end and cur <= recurrence_end:
            result.append(cur)
            cur += timedelta(days=1)

    elif event.recurrence == Event.RECURRENCE_WEEKLY:
        target_weekday = event_start.weekday()
        cur = month_start
        while cur <= month_end:
            if cur.weekday() == target_weekday and cur >= event_start and cur <= recurrence_end:
                result.append(cur)
            cur += timedelta(days=1)

    elif event.recurrence == Event.RECURRENCE_MONTHLY:
        target_day = event_start.day
        _, max_day = calendar.monthrange(year, month)
        if target_day <= max_day:
            d = date(year, month, target_day)
            if d >= event_start and d <= recurrence_end:
                result.append(d)

    elif event.recurrence == Event.RECURRENCE_YEARLY:
        if month == event_start.month:
            target_day = event_start.day
            _, max_day = calendar.monthrange(year, month)
            if target_day <= max_day:
                d = date(year, month, target_day)
                if d >= event_start and d <= recurrence_end:
                    result.append(d)

    return result


def get_events_for_day(user, day: date) -> list[Event]:
    """Return all events (including recurring) occurring on the given day."""
    events: list[Event] = []

    non_recurring = Event.objects.filter(
        user=user,
        recurrence=Event.RECURRENCE_NONE,
        start_datetime__date=day,
    )
    events.extend(non_recurring)

    recurring = Event.objects.filter(
        user=user,
        start_datetime__date__lte=day,
    ).exclude(recurrence=Event.RECURRENCE_NONE)

    for ev in recurring:
        if day in expand_recurring(ev, day.year, day.month):
            events.append(ev)

    events.sort(key=lambda e: (not e.all_day, e.start_datetime))
    return events


def get_events_for_month(user, year: int, month: int) -> dict[date, list[Event]]:
    """Return a mapping of date → events for the given month."""
    _, days_in_month = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)

    events_map: dict[date, list[Event]] = {}

    non_recurring = Event.objects.filter(
        user=user,
        recurrence=Event.RECURRENCE_NONE,
        start_datetime__date__gte=month_start,
        start_datetime__date__lte=month_end,
    )
    for ev in non_recurring:
        d = ev.start_datetime.date()
        events_map.setdefault(d, []).append(ev)

    recurring = Event.objects.filter(
        user=user,
        start_datetime__date__lte=month_end,
    ).exclude(recurrence=Event.RECURRENCE_NONE)

    for ev in recurring:
        for d in expand_recurring(ev, year, month):
            events_map.setdefault(d, []).append(ev)

    return events_map
