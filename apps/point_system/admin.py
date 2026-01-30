from django.contrib import admin

from .models import FieldDefinition, Member

# Register your models here.

admin.site.register(Member)
admin.site.register(FieldDefinition)
