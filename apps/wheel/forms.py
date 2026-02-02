from django import forms


class NameWheelForm(forms.Form):
    members_chosen = forms.IntegerField(label="Members chosen", min_value=1, initial=1)
