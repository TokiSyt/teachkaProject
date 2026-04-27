from django import forms

from .models import Quiz, Round
from .utils import validate_upload


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["title", "logo", "visibility", "focus_x", "focus_y"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "input input-bordered border-2 border-base-300 bg-base-200 focus:bg-base-100 focus:border-primary rounded-xl w-full",
                    "placeholder": "e.g. Capitals of Europe",
                }
            ),
            "logo": forms.ClearableFileInput(attrs={"class": "file-input file-input-bordered rounded-xl w-full"}),
            "visibility": forms.Select(attrs={"class": "select select-bordered rounded-xl w-full"}),
            "focus_x": forms.HiddenInput(),
            "focus_y": forms.HiddenInput(),
        }

    def clean_logo(self):
        f = self.cleaned_data.get("logo")
        if f and f is not getattr(self.instance, "logo", None):
            validate_upload(f)
        return f


class RoundForm(forms.ModelForm):
    class Meta:
        model = Round
        fields = ["question", "image", "question_type", "time_limit", "points", "focus_x", "focus_y"]
        widgets = {
            "question": forms.TextInput(
                attrs={
                    "class": "input input-bordered border-2 border-base-300 bg-base-200 focus:bg-base-100 focus:border-primary rounded-xl w-full",
                    "placeholder": "e.g. What is the capital of France?",
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={"class": "file-input file-input-bordered rounded-xl w-full", "accept": "image/*"}
            ),
            "question_type": forms.Select(
                attrs={
                    "class": "select select-bordered border-2 border-base-300 bg-base-200 focus:bg-base-100 focus:border-primary rounded-xl w-full"
                }
            ),
            "time_limit": forms.NumberInput(
                attrs={
                    "class": "input input-bordered border-2 border-base-300 bg-base-200 focus:bg-base-100 focus:border-primary rounded-xl w-full",
                    "min": 0,
                }
            ),
            "points": forms.NumberInput(
                attrs={
                    "class": "input input-bordered border-2 border-base-300 bg-base-200 focus:bg-base-100 focus:border-primary rounded-xl w-full",
                    "min": 0,
                }
            ),
            "focus_x": forms.HiddenInput(),
            "focus_y": forms.HiddenInput(),
        }

    def clean_image(self):
        f = self.cleaned_data.get("image")
        if f and f is not getattr(self.instance, "image", None):
            validate_upload(f)
        return f
