from django import template
from django.utils.translation import get_language

from apps.calendar.holidays_data import DESCRIPTIONS, INTERNATIONAL_HOLIDAYS, NAMES

register = template.Library()


def _build_lookup() -> dict[tuple[str, str], dict[str, dict[str, str]]]:
    out: dict[tuple[str, str], dict[str, dict[str, str]]] = {}
    for country, entries in DESCRIPTIONS.items():
        for name, meta in entries.items():
            out[(country, name)] = meta
    for _m, _d, name, subject, description in INTERNATIONAL_HOLIDAYS:
        out[("INTL", name)] = {"subject": subject, "description": description}
    return out


_LOOKUP = _build_lookup()


def _lang() -> str:
    return (get_language() or "en").split("-")[0].split("_")[0]


def _pick(d: dict[str, str], fallback: str = "") -> str:
    if not d:
        return fallback
    return d.get(_lang()) or d.get("en") or fallback


@register.filter
def holiday_name(name: str) -> str:
    return NAMES.get(name, {}).get(_lang()) or name


@register.filter
def holiday_subject(holiday) -> str:
    meta = _LOOKUP.get((holiday.country, holiday.name))
    if meta:
        return _pick(meta.get("subject", {}), holiday.subject or holiday.name)
    return holiday.subject or holiday.name


@register.filter
def holiday_description(holiday) -> str:
    meta = _LOOKUP.get((holiday.country, holiday.name))
    if meta:
        return _pick(meta.get("description", {}), holiday.description or "")
    return holiday.description or ""
