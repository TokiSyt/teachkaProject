from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ContactMessage(models.Model):
    KIND_BUG = "bug"
    KIND_QUESTION = "question"
    KIND_FEATURE = "feature"
    KIND_CHOICES = [
        (KIND_BUG, _("Bug report")),
        (KIND_QUESTION, _("Question")),
        (KIND_FEATURE, _("Feature request")),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_messages",
    )
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=KIND_BUG)
    subject = models.CharField(max_length=140)
    body = models.TextField(max_length=5000)
    email = models.EmailField(blank=True)
    page_url = models.CharField(max_length=512, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.kind}] {self.subject}"
