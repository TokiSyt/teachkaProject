from django import forms
from .models import GroupCreationModel


class GroupCreationForm(forms.ModelForm):
    class Meta:
        model = GroupCreationModel
        fields = ["title", "members_string"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "members_string": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }


class GroupMakerForm(forms.Form):
    size = forms.IntegerField(min_value=1, required=True, help_text="How many members per group?")
