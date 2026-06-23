from django.urls import path

from .views import (
    AddColumn,
    ClearColumn,
    ColumnReorderView,
    DashboardView,
    DeleteAllColumns,
    DeleteColumn,
    EditColumn,
    HomeView,
    ToggleTable,
)

app_name = "karma"

urlpatterns = [
    path("", HomeView.as_view(), name="karma-home"),
    path("", HomeView.as_view(), name="home"),  # alias for consistent origin_app routing
    path("new_column/<int:pk>", AddColumn.as_view(), name="new-column"),
    path("delete_column/<int:pk>", DeleteColumn.as_view(), name="delete-column"),
    path("clear_column/<int:pk>", ClearColumn.as_view(), name="clear-column"),
    path("delete_all_columns/<int:pk>", DeleteAllColumns.as_view(), name="delete-all-columns"),
    path("toggle_table/<int:pk>", ToggleTable.as_view(), name="toggle-table"),
    path("edit_column/<int:pk>", EditColumn.as_view(), name="edit-column"),
    path("columns/reorder/<int:group_pk>", ColumnReorderView.as_view(), name="column-reorder"),
    path("karma_dashboard/<int:pk>", DashboardView.as_view(), name="karma-dashboard"),
]
