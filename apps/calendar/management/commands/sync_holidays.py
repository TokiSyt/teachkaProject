"""
Sync the Holiday table for one or more countries and a given year.

Pulls dates+English names from the `holidays` library, joins them with curated
descriptions in `apps/calendar/holidays_data.py`, and upserts `Holiday` rows
keyed on (country, date, name).

Usage:
    python manage.py sync_holidays --year 2026
    python manage.py sync_holidays --year 2026 --country CZ
    python manage.py sync_holidays --year 2026 --country CZ PT EN INTL
"""

from datetime import date as date_cls

import holidays
from django.core.management.base import BaseCommand, CommandError

from apps.calendar.holidays_data import DESCRIPTIONS, INTERNATIONAL_HOLIDAYS
from apps.calendar.models import Holiday

# Mapping: our model country code -> `holidays` lib country code
LIB_COUNTRY = {
    "CZ": "CZ",
    "PT": "PT",
    "EN": "GB",
}
SUPPORTED = list(LIB_COUNTRY.keys()) + ["INTL"]


class Command(BaseCommand):
    help = "Sync Holiday rows for the given year and countries."

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, required=True, help="Calendar year to sync.")
        parser.add_argument(
            "--country",
            nargs="+",
            choices=SUPPORTED,
            default=SUPPORTED,
            help=f"Country codes to sync. Default: all ({', '.join(SUPPORTED)}).",
        )

    def handle(self, *args, **options):
        year: int = options["year"]
        countries: list[str] = options["country"]

        if year < 1900 or year > 2100:
            raise CommandError(f"Year {year} outside supported range 1900-2100.")

        total_created = 0
        total_updated = 0

        for code in countries:
            self.stdout.write(f"Syncing {code} for {year}...", ending=" ")
            self.stdout.flush()
            if code == "INTL":
                created, updated = self._sync_international(year)
            else:
                created, updated = self._sync_country(code, year)
            total_created += created
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f"{created} created, {updated} updated"))

        self.stdout.write(self.style.SUCCESS(f"Done. Total: {total_created} created, {total_updated} updated."))

    def _sync_country(self, country_code: str, year: int) -> tuple[int, int]:
        lib_code = LIB_COUNTRY[country_code]
        try:
            country_holidays = holidays.country_holidays(lib_code, years=year, language="en_US")
        except Exception as exc:
            raise CommandError(f"holidays lib failed for {lib_code} {year}: {exc}") from exc

        descriptions = DESCRIPTIONS.get(country_code, {})
        created = updated = 0

        for d, name in sorted(country_holidays.items()):
            # Some countries return composite names like "Holiday A; Holiday B" on one date.
            for single_name in [n.strip() for n in name.split(";") if n.strip()]:
                meta = descriptions.get(single_name, {})
                subject = meta.get("subject", {}).get("en", single_name) if meta else single_name
                description = meta.get("description", {}).get("en", "") if meta else ""
                _, was_created = Holiday.objects.update_or_create(
                    country=country_code,
                    date=d,
                    name=single_name,
                    defaults={
                        "subject": subject,
                        "description": description,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
        return created, updated

    def _sync_international(self, year: int) -> tuple[int, int]:
        created = updated = 0
        for month, day, name, subject, description in INTERNATIONAL_HOLIDAYS:
            d = date_cls(year, month, day)
            _, was_created = Holiday.objects.update_or_create(
                country="INTL",
                date=d,
                name=name,
                defaults={
                    "subject": subject.get("en", name),
                    "description": description.get("en", ""),
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
        return created, updated
