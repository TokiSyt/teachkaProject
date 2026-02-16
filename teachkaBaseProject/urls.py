from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from apps.users import views as v

from . import views

urlpatterns: list[URLPattern | URLResolver] = [
    path("manage-portal/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(
    path("", views.HomeView.as_view(), name="home"),
    path("", include("django.contrib.auth.urls")),
    path("register/", v.RegisterView.as_view(), name="register"),
    # Main apps with clean URL paths
    path("grades/", include("apps.grade_calculator.urls")),
    path("groups/", include("apps.group_maker.urls", namespace="group_maker")),
    path("karma/", include("apps.point_system.urls")),
    path("divider/", include("apps.group_divider.urls")),
    path("wheel/", include("apps.wheel.urls")),
    path("timer/", include("apps.timer.urls")),
    # WIP apps
    path("todo/", include("apps.todo_list.urls")),
    path("math_ops/", include("apps.math_ops.urls")),
    # Users
    path("users/", include("apps.users.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
