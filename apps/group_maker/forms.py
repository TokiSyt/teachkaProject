from django import forms
from django.utils.translation import gettext_lazy as _

from .models import GroupCreationModel


class GroupCreationForm(forms.ModelForm):
    class Meta:
        model = GroupCreationModel
        fields = ["title", "members_string"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "members_string": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }
        error_messages = {
            "title": {
                "unique": _("A group with this name already exists. Please choose a different name."),
            },
        }
