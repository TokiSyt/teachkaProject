from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    PasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)

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


class EditProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "password" in self.fields:
            self.fields["password"].widget = forms.HiddenInput()


class CustomPasswordChangeForm(PasswordChangeForm):
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput,
        help_text="",  # Removes the default message
    )
