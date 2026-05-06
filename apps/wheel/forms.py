from django import forms
from django.utils.translation import gettext_lazy as _


class NameWheelForm(forms.Form):
    chosen_members_amount = forms.IntegerField(label=_("Members chosen"), min_value=1, initial=1)
