from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    PasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField(required=False)
    password2 = forms.CharField(label="Password Confirmation", widget=forms.PasswordInput, help_text="")

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
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise ValidationError("An account with this username already exists.")
        return username


class EditProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("password", None)
        self.fields["username"].disabled = True


class CustomPasswordChangeForm(PasswordChangeForm):
    new_password = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput,
        help_text="",
    )


class PasswordResetRequestForm(forms.Form):
    # email for password change
    send_to_email = forms.EmailField(required=True)
