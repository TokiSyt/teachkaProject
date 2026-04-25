from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "start_datetime", "recurrence"]
    list_filter = ["recurrence"]
    search_fields = ["title", "subject"]
