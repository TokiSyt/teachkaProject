from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, UserStats


class CustomUserAdmin(UserAdmin):
    fieldsets = tuple(UserAdmin.fieldsets or ()) + (
        ("Preferences", {"fields": ("theme", "language", "country", "icon_hover_color")}),
    )
    add_fieldsets = tuple(UserAdmin.add_fieldsets or ()) + (
        ("Preferences", {"fields": ("theme", "language", "country", "icon_hover_color")}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserStats)
