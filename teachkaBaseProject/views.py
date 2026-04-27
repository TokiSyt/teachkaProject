from datetime import date

from django.db import connection
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from apps.group_maker.models import GroupCreationModel
from apps.point_system.models import Member
from apps.users.models import UserStats


class RobotsView(View):
    def get(self, request):
        content = (
            "User-agent: *\n"
            "Disallow: /manage-portal/\n"
            "Disallow: /users/activate/\n"
            "Disallow: /users/reset/\n"
            "Disallow: /i18n/\n"
        )
        return HttpResponse(content, content_type="text/plain")


class PrivacyView(TemplateView):
    template_name = "legal/privacy.html"


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

        return context
