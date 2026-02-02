from django.urls import path

from .views import GradeCalculatorView

app_name = "grade_calculator"

urlpatterns = [
    path("", GradeCalculatorView.as_view(), name="grade_calculator"),
]
