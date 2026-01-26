from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView

from .forms import GradeCalculatorForm
from .services.grade_calculator import grade_calculator


class GradeCalculatorView(LoginRequiredMixin, FormView):
    template_name = "grade_calculator/grade_calculator.html"
    form_class = GradeCalculatorForm
    success_url = "."

    def form_valid(self, form):
        max_points = form.cleaned_data["max_points"]
        rounding_option = form.cleaned_data["rounding_option"]
        grades = grade_calculator(max_points, rounding_option)

        context = self.get_context_data(
            form=form,
            score_range=grades,
            min_points_error=not grades,
        )
        return self.render_to_response(context)

    def form_invalid(self, form):
        return super().form_invalid(form)
