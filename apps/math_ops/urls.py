from django.urls import path

from .views import HomeView

app_name = "math_ops"

urlpatterns = [path("", HomeView.as_view(), name="home")]
