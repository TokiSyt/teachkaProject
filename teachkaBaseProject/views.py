from django.db.models import Sum
from django.views.generic import TemplateView

from apps.group_maker.models import GroupCreationModel
from apps.point_system.models import Member


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
            context["calculator_uses"] = user.calculator_uses
            context["wheel_spins"] = user.wheel_spins
            context["divider_uses"] = user.divider_uses

        return context
