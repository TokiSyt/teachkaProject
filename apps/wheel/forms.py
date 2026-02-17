from django import forms


class NameWheelForm(forms.Form):
    chosen_members_amount = forms.IntegerField(label="Members chosen", min_value=1, initial=1)
