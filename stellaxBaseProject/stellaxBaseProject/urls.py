from django.contrib import admin
from django.urls import path, include
from . import views
from apps.users import views as v

app_name = "home"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.HomeView.as_view(), name="home"),
    path("", include("django.contrib.auth.urls")),
    path("register/", v.RegisterView.as_view(), name="register"),
    path("todo_list/", include("apps.todo_list.urls")),
    path("timer/", include("apps.timer.urls")),
    path("quiz/", include("apps.quiz.urls")),
    path("excel/", include("apps.excel.urls")),
    path("currency_calculator/", include("apps.currency_calculator.urls")),
    path("wheel/", include("apps.wheel.urls")),
    path("math_ops/", include("apps.math_ops.urls")),
    path("grade-calculator/", include("apps.grade_calculator.urls")),
    path("users/", include("apps.users.urls")),
]
