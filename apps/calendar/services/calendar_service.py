import calendar
from datetime import date, timedelta

from apps.calendar.models import Event, Holiday
from apps.calendar.name_days_cz import NAME_DAYS_CZ


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


def _holiday_country_codes(user) -> list[str]:
    """Country codes whose holidays should appear for this user: their country + INTL."""
    codes = ["INTL"]
    country = getattr(user, "country", "") or ""
    if country:
        codes.append(country)
    return codes


def _drop_intl_when_national(holidays: list[Holiday]) -> list[Holiday]:
    """If a national holiday shares a date with INTL, hide the INTL one."""
    if len(holidays) > 1 and any(h.country != Holiday.COUNTRY_INTERNATIONAL for h in holidays):
        return [h for h in holidays if h.country != Holiday.COUNTRY_INTERNATIONAL]
    return holidays


def get_holidays_for_month(user, year: int, month: int) -> dict[date, list[Holiday]]:
    _, days_in_month = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)

    qs = Holiday.objects.filter(
        country__in=_holiday_country_codes(user),
        date__gte=month_start,
        date__lte=month_end,
    )
    holidays_map: dict[date, list[Holiday]] = {}
    for h in qs:
        holidays_map.setdefault(h.date, []).append(h)
    for d, hs in holidays_map.items():
        holidays_map[d] = _drop_intl_when_national(hs)
    return holidays_map


def get_holidays_for_day(user, day: date) -> list[Holiday]:
    holidays = list(
        Holiday.objects.filter(
            country__in=_holiday_country_codes(user),
            date=day,
        )
    )
    return _drop_intl_when_national(holidays)


def _is_czech_user(user) -> bool:
    return getattr(user, "country", "") == "CZ"


def get_name_day_for_day(user, day: date) -> str | None:
    """Return the Czech name day for the given date, or None if user is not CZ."""
    if not _is_czech_user(user):
        return None
    return NAME_DAYS_CZ.get((day.month, day.day))


def get_name_days_for_month(user, year: int, month: int) -> dict[date, str]:
    """Return {date: name} for every day in month with a name. Empty dict if user not CZ."""
    if not _is_czech_user(user):
        return {}
    _, days_in_month = calendar.monthrange(year, month)
    result: dict[date, str] = {}
    for day_num in range(1, days_in_month + 1):
        name = NAME_DAYS_CZ.get((month, day_num))
        if name:
            result[date(year, month, day_num)] = name
    return result
