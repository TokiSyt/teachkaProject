from django.contrib import admin

from .models import Event, Holiday


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "start_datetime", "recurrence"]
    list_filter = ["recurrence"]
    search_fields = ["title", "subject"]


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "date", "subject"]
    list_filter = ["country", "date"]
    search_fields = ["name", "subject", "description"]
    ordering = ["date", "name"]
