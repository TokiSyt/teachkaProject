from django.conf import settings


def site_flags(request):
    return {"enable_wip_apps": settings.ENABLE_WIP_APPS}
