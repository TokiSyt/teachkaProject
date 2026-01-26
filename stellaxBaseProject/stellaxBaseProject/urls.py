from django.contrib import admin
from django.urls import path, include
from . import views
from users import views as v

app_name = "home"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.homePage, name="home"),
    path("", include("django.contrib.auth.urls")),
    path("register/", v.register, name="register"),
    path("wishList/", include("wishList.urls")),
    path("timer/", include("timer.urls")),
    path("quiz/", include("quiz.urls")),
    path("excel/", include("excel.urls")),
    path("currencyCalculator/", include("currencyCalculator.urls")),
    path("wheel/", include("wheel.urls")),
    path("mathOps", include("mathOps.urls")),
    path("maxGradeCal", include("maxGradeCal.urls")),
    path("users/", include("users.urls")),
]
