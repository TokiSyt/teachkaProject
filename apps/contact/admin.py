from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "kind", "subject", "user", "email", "handled")
    list_filter = ("kind", "handled", "created_at")
    search_fields = ("subject", "body", "email", "user__username")
    list_editable = ("handled",)
    readonly_fields = ("created_at", "user_agent", "page_url")
    date_hierarchy = "created_at"
