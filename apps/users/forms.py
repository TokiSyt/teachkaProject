from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    PasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField(required=False)
    password2 = forms.CharField(label=_("Password Confirmation"), widget=forms.PasswordInput, help_text="")
    accept_terms = forms.BooleanField(
        required=True,
        error_messages={"required": _("You must accept the Terms of Service and Privacy Policy to continue.")},
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("An account with this email address already exists."))
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise ValidationError(_("An account with this username already exists."))
        return username


class EditProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "country")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("password", None)
        self.fields["username"].disabled = True
        # Email is locked: users can't change it to an address they don't own
        # (no ownership verification). Changes go through info@teachka.com.
        # disabled => the submitted value is ignored, the instance value kept.
        self.fields["email"].disabled = True
        self.fields["email"].required = False


class CustomPasswordChangeForm(PasswordChangeForm):
    new_password = forms.CharField(
        label=_("Confirm new password"),
        widget=forms.PasswordInput,
        help_text="",
    )


class PasswordResetRequestForm(forms.Form):
    # email for password change
    send_to_email = forms.EmailField(required=True)
