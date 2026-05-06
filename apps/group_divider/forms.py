from django import forms
from django.utils.translation import gettext_lazy as _


class GroupMakerForm(forms.Form):
    group_id = forms.IntegerField(required=True)
    size = forms.IntegerField(min_value=1, required=True, help_text=_("How many members per group?"))
