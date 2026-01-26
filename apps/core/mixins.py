"""
View and QuerySet mixins for Stellax applications.
"""

from django.contrib.auth.mixins import LoginRequiredMixin


class UserQuerySetMixin:
    """
    Mixin that filters queryset to only show objects owned by the current user.

    Assumes the model has a 'user' field.

    Usage:
        class MyListView(UserQuerySetMixin, ListView):
            model = MyModel
    """

    user_field = "user"

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request, "user") and self.request.user.is_authenticated:
            return queryset.filter(**{self.user_field: self.request.user})
        return queryset.none()


class UserOwnedMixin(LoginRequiredMixin, UserQuerySetMixin):
    """
    Combined mixin that requires login and filters by user.

    Usage:
        class MyListView(UserOwnedMixin, ListView):
            model = MyModel
    """

    pass


class FormUserMixin:
    """
    Mixin that automatically sets the user field on form save.

    Usage:
        class MyCreateView(FormUserMixin, CreateView):
            model = MyModel
            fields = ['name']
    """

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
