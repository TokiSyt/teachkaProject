from datetime import date

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import connection
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from apps.calendar.name_days_cz import NAME_DAYS_CZ
from apps.contact.models import ContactMessage
from apps.group_maker.models import GroupCreationModel
from apps.point_system.models import Member
from apps.quizzmaker import live
from apps.quizzmaker.models import GameSession
from apps.users.models import UserStats


class RobotsView(View):
    def get(self, request):
        content = (
            "User-agent: *\n"
            "Disallow: /manage-portal/\n"
            "Disallow: /admin-portal/\n"
            "Disallow: /users/activate/\n"
            "Disallow: /users/reset/\n"
            "Disallow: /i18n/\n"
        )
        return HttpResponse(content, content_type="text/plain")


class PrivacyView(TemplateView):
    template_name = "legal/privacy.html"


class TermsView(TemplateView):
    template_name = "legal/terms.html"


class UseRestrictionsView(TemplateView):
    template_name = "legal/use_restrictions.html"


class SecurityView(TemplateView):
    template_name = "legal/security.html"


class CancellationView(TemplateView):
    template_name = "legal/cancellation.html"


class HealthView(View):
    def get(self, request):
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False
        status = 200 if db_ok else 503
        return JsonResponse({"status": "ok" if db_ok else "error", "db": db_ok}, status=status)


class ReadyzView(View):
    def get(self, request):
        checks: dict[str, bool] = {}
        try:
            connection.ensure_connection()
            checks["db"] = True
        except Exception:
            checks["db"] = False

        try:
            from django.db.migrations.executor import MigrationExecutor

            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            checks["migrations"] = len(plan) == 0
        except Exception:
            checks["migrations"] = False

        ready = all(checks.values())
        return JsonResponse(
            {"status": "ready" if ready else "not ready", **checks},
            status=200 if ready else 503,
        )


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict a view to admin (superuser) accounts."""

    def test_func(self):
        return self.request.user.is_superuser


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "admin_dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total_users"] = get_user_model().objects.count()

        messages_qs = ContactMessage.objects.select_related("user")
        ctx["contact_messages"] = messages_qs
        ctx["contact_counts"] = {
            "all": messages_qs.count(),
            "open": messages_qs.filter(handled=False).count(),
            ContactMessage.KIND_BUG: messages_qs.filter(kind=ContactMessage.KIND_BUG).count(),
            ContactMessage.KIND_QUESTION: messages_qs.filter(kind=ContactMessage.KIND_QUESTION).count(),
            ContactMessage.KIND_FEATURE: messages_qs.filter(kind=ContactMessage.KIND_FEATURE).count(),
        }
        ctx["kind_bug"] = ContactMessage.KIND_BUG
        ctx["kind_question"] = ContactMessage.KIND_QUESTION
        ctx["kind_feature"] = ContactMessage.KIND_FEATURE

        ctx["open_sessions"] = (
            GameSession.objects.exclude(state=GameSession.ENDED).select_related("quiz", "host").order_by("-created_at")
        )
        return ctx


class ForceQuitSessionView(AdminRequiredMixin, View):
    """Force-terminate a live quiz session: wipe Redis state, mark it ended,
    and tell every connected socket to leave."""

    def post(self, request, pk):
        session = get_object_or_404(GameSession, pk=pk)
        # Best-effort wipe of live Redis state + persist scores. This may no-op
        # if the Redis room already expired, so we don't rely on it to clear the
        # DB row below.
        try:
            live.close_room(session.code)
        except Exception:
            pass
        layer = get_channel_layer()
        if layer is not None:
            async_to_sync(layer.group_send)(f"quiz_{session.code}", {"type": "closed"})
        # Authoritatively mark the row ended so it leaves the open list even when
        # the Redis state was already gone (end_game early-returns in that case).
        if session.state != GameSession.ENDED:
            session.state = GameSession.ENDED
            session.ended_at = timezone.now()
            session.save(update_fields=["state", "ended_at"])
        messages.success(request, _("Session %(code)s was force-quit.") % {"code": session.code})
        return redirect("admin_dashboard")


class AdminMessageReplyView(AdminRequiredMixin, View):
    """Reply to a contact message by email from inside the dashboard and mark
    it handled. If no reply body is given, just toggle the handled flag."""

    def post(self, request, pk):
        msg = get_object_or_404(ContactMessage, pk=pk)
        body = (request.POST.get("reply") or "").strip()
        recipient = msg.email or (msg.user.email if msg.user else "")

        if body:
            if not recipient:
                messages.error(request, _("No email on file for this message — cannot reply."))
                return redirect("admin_dashboard")
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string

            ctx = {"reply_body": body, "subject": msg.subject, "site_url": "https://teachka.com"}
            email = EmailMultiAlternatives(
                subject=_("Re: %(subject)s") % {"subject": msg.subject},
                body=render_to_string("email/contact_reply.txt", ctx),
                from_email=None,  # uses DEFAULT_FROM_EMAIL
                to=[recipient],
            )
            email.attach_alternative(render_to_string("email/contact_reply.html", ctx), "text/html")
            email.send(fail_silently=False)
            msg.handled = True
            msg.save(update_fields=["handled"])
            messages.success(request, _("Reply sent to %(to)s.") % {"to": recipient})
        else:
            msg.handled = not msg.handled
            msg.save(update_fields=["handled"])
            messages.success(
                request,
                _("Marked as handled.") if msg.handled else _("Marked as open."),
            )
        return redirect("admin_dashboard")


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # User-specific stats (for authenticated users)
        if self.request.user.is_authenticated:
            user = self.request.user

            # Groups and members
            user_groups = GroupCreationModel.objects.filter(user=user)
            context["user_groups_count"] = user_groups.count()

            user_members = Member.objects.filter(group__user=user)
            context["user_members_count"] = user_members.count()

            # Points totals
            user_totals = user_members.aggregate(
                total_positive=Sum("positive_total"),
                total_negative=Sum("negative_total"),
            )
            context["user_positive_points"] = user_totals["total_positive"] or 0
            context["user_negative_points"] = user_totals["total_negative"] or 0

            # Usage stats
            stats, _created = UserStats.objects.get_or_create(user=user)
            context["calculator_uses"] = stats.calculator_uses
            context["wheel_spins"] = stats.wheel_spins
            context["divider_uses"] = stats.divider_uses
            total_timer_ms = stats.stopwatch_total_ms + stats.countdown_total_ms
            context["timer_total_hours"] = round(total_timer_ms / 3_600_000, 1)
            context["timer_total_minutes"] = round(total_timer_ms / 60_000)

        # Accent colour palette
        context["accent_palette"] = [
            ("#1779db", "Blue"),
            ("#7c3aed", "Violet"),
            ("#be185d", "Pink"),
            ("#047857", "Green"),
            ("#b45309", "Amber"),
            ("#b91c1c", "Red"),
            ("#0e7490", "Cyan"),
            ("#475569", "Slate"),
        ]

        # Date info
        today = date.today()
        week_number = today.isocalendar()[1]
        context["today"] = today
        context["week_number"] = week_number
        context["week_parity"] = _("Even") if week_number % 2 == 0 else _("Odd")

        # Czech name day (only for CZ users)
        if self.request.user.is_authenticated and getattr(self.request.user, "country", "") == "CZ":
            context["name_day"] = NAME_DAYS_CZ.get((today.month, today.day))

        return context
