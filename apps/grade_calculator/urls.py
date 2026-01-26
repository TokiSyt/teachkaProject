from django.urls import path

from .views import GradeCalculatorView

urlpatterns = [
    path("", GradeCalculatorView.as_view(), name="grade_calculator"),
]
