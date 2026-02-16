from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def strip_lang_prefix(path):
    """Strip the language prefix from a URL path.

    e.g. /pt/karma/ -> /karma/, /cs/groups/ -> /groups/, /karma/ -> /karma/
    """
    for code, _name in settings.LANGUAGES:
        prefix = f"/{code}/"
        if path.startswith(prefix):
            return "/" + path[len(prefix) :]
    return path
