from django.shortcuts import render
from .logic.maxGrade import calculate_grades
from .forms import gradeCalculatorForm
from django.contrib.auth.decorators import login_required

@login_required
def gradeCalculator(request):
    grades = None

    if request.method == "POST":

        grade_calculator_form = gradeCalculatorForm(request.POST)

        if grade_calculator_form.is_valid():
            max_points = grade_calculator_form.cleaned_data["max_points"]
            rounding_option = grade_calculator_form.cleaned_data["rounding_option"]
            grades = calculate_grades(max_points, rounding_option)

    else:
        grade_calculator_form = gradeCalculatorForm()

    context = {"form": grade_calculator_form, "score_range": grades}

    return render(request, "maxGradeCal/maxGrade.html", context)
