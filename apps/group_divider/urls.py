from django.urls import path

from .views import GroupDividerHome

urlpatterns = [
    path("", GroupDividerHome.as_view(), name="group-divider-home"),
]
