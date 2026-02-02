from django.urls import path

from .views import GroupDividerHome

app_name = "group_divider"

urlpatterns = [
    path("", GroupDividerHome.as_view(), name="home"),
]
