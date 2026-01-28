from django import forms
from django.forms import ModelForm

from .models import FieldDefinition, Member


class GroupForm(ModelForm):
    class Meta:
        model = Member
        fields = ["name", "positive_data", "negative_data"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            # Positive fields
            for key, value in (self.instance.positive_data or {}).items():
                self.fields[f"pos_{key}"] = forms.IntegerField(
                    initial=value, required=False, label=key.replace("_", " ").title()
                )

            # Negative fields
            for key, value in (self.instance.negative_data or {}).items():
                self.fields[f"neg_{key}"] = forms.IntegerField(
                    initial=value, required=False, label=key.replace("_", " ").title()
                )

    def clean(self):
        cleaned_data = super().clean()
        positive_data = {}
        negative_data = {}

        for key in self.fields:
            if key not in ["name", "positive_data", "negative_data"]:
                value = cleaned_data.get(key)
                if key.startswith("pos_"):
                    positive_data[key[4:]] = value
                elif key.startswith("neg_"):
                    negative_data[key[4:]] = value

        cleaned_data["positive_data"] = positive_data
        cleaned_data["negative_data"] = negative_data
        return cleaned_data


class AddFieldForm(ModelForm):
    class Meta:
        model = FieldDefinition
        fields = ["name", "type"]


"""class AddFieldForm(forms.Form):
    field_name = forms.CharField(max_length=25)
    field_type = forms.ChoiceField(choices=[("int", "numerical"), ("str", "text")])
    field_definition = forms.ChoiceField()"""


class RemoveFieldForm(forms.Form):
    field_name = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        field_choices = kwargs.pop("field_choices", [])
        super().__init__(*args, **kwargs)
        self.fields["field_name"].choices = [(c, c) for c in field_choices]


class EditColumnForm(forms.Form):
    new_name = forms.CharField(max_length=50)
    old_name = forms.CharField(max_length=50)
    field_definition = forms.ChoiceField(choices=[("positive", "Positive"), ("negative", "Negative")])
