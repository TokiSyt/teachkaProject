from django import forms


class GroupMakerForm(forms.Form):
    group_id = forms.IntegerField(required=True)
    size = forms.IntegerField(min_value=1, required=True, help_text="How many members per group?")
