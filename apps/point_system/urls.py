from django.urls import path
from .views import HomeView, DashboardView, AddColumn, EditColumn, DeleteColumn

app_name = "karma"

urlpatterns = [
    path("", HomeView.as_view(), name="karma-home"),
    path("new_column/<int:pk>", AddColumn.as_view(), name="new-column"),
    path("delete_column/<int:pk>", DeleteColumn.as_view(), name="delete-column"),
    path("edit_column/<int:pk>", EditColumn.as_view(), name="edit-column"),
    path("karma_dashboard/<int:pk>", DashboardView.as_view(), name="karma-dashboard"),
]
