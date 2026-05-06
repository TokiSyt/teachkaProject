from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["kind", "subject", "body", "email"]
        widgets = {
            "kind": forms.HiddenInput(),
            "subject": forms.TextInput(attrs={"maxlength": 140, "autocomplete": "off"}),
            "body": forms.Textarea(attrs={"rows": 8, "maxlength": 5000}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_subject(self):
        s = (self.cleaned_data.get("subject") or "").strip()
        if len(s) < 3:
            raise forms.ValidationError(_("Subject too short."))
        return s

    def clean_body(self):
        b = (self.cleaned_data.get("body") or "").strip()
        if len(b) < 10:
            raise forms.ValidationError(_("Please add a bit more detail (at least 10 characters)."))
        return b
