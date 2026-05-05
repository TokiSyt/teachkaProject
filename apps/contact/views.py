from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View

from .forms import ContactForm
from .models import ContactMessage


class ContactView(View):
    template_name = "contact/contact.html"

    def get(self, request):
        kind = request.GET.get("kind", ContactMessage.KIND_BUG)
        if kind not in dict(ContactMessage.KIND_CHOICES):
            kind = ContactMessage.KIND_BUG
        initial = {"kind": kind}
        if request.user.is_authenticated and getattr(request.user, "email", ""):
            initial["email"] = request.user.email
        form = ContactForm(initial=initial)
        return render(
            request,
            self.template_name,
            {"form": form, "selected_kind": kind, "kinds": ContactMessage.KIND_CHOICES},
        )

    def post(self, request):
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            if request.user.is_authenticated:
                msg.user = request.user
            msg.page_url = request.POST.get("page_url", "")[:512]
            msg.user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
            msg.save()
            messages.success(request, _("Message received. We'll be in touch."))
            return redirect(reverse("contact:contact") + "?sent=1")

        kind = form.data.get("kind") or ContactMessage.KIND_BUG
        return render(
            request,
            self.template_name,
            {"form": form, "selected_kind": kind, "kinds": ContactMessage.KIND_CHOICES},
        )
