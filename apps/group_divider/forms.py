from django import forms
from django.utils.translation import gettext_lazy as _


class GroupMakerForm(forms.Form):
    MODE_SIZE = "size"
    MODE_TEAMS = "teams"
    MODE_CHOICES = [(MODE_SIZE, _("Team size")), (MODE_TEAMS, _("Number of teams"))]

    group_id = forms.IntegerField(required=True)
    mode = forms.ChoiceField(choices=MODE_CHOICES, required=False)
    size = forms.IntegerField(min_value=1, required=True, help_text=_("Members per team, or number of teams"))

    def clean_mode(self):
        return self.cleaned_data.get("mode") or self.MODE_SIZE
