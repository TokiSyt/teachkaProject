from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy
from django.views.generic import TemplateView

from apps.users.models import UserStats

from .forms import GradeCalculatorForm
from .services.grade_calculator import grade_calculator

SESSION_RESULT_KEY = "grade_calculator_result"


class GradeCalculatorView(LoginRequiredMixin, TemplateView):
    template_name = "grade_calculator/grade_calculator.html"
    form_class = GradeCalculatorForm

    def get(self, request, *args, **kwargs):
        if request.GET.get("reset"):
            request.session.pop(SESSION_RESULT_KEY, None)
            return redirect(reverse("grade_calculator:grade_calculator"))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = self.request.session.get(SESSION_RESULT_KEY, None)
        initial = {}
        if result and result.get("score_range"):
            context["score_range"] = result["score_range"]
            initial = {
                "max_points": result.get("max_points"),
                "rounding_option": result.get("rounding_option"),
            }
        context["form"] = self.form_class(initial=initial)
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        max_points = form.cleaned_data["max_points"]
        rounding_option = form.cleaned_data["rounding_option"]

        if max_points < 4:
            form.add_error("max_points", gettext_lazy("Maximum points must be at least 4."))
            return render(request, self.template_name, {"form": form})

        stats, _ = UserStats.objects.get_or_create(user=request.user)
        stats.calculator_uses += 1
        stats.save(update_fields=["calculator_uses"])

        score_range = grade_calculator(max_points, rounding_option)

        request.session[SESSION_RESULT_KEY] = {
            "score_range": score_range,
            "max_points": max_points,
            "rounding_option": rounding_option,
        }
        return redirect(reverse("grade_calculator:grade_calculator"))
