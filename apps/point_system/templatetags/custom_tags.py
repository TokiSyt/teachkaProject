from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)


@register.filter
def negativity_class(value):
    """Return a CSS class name based on the total_negative value."""
    try:
        val = int(value)
    except (ValueError, TypeError):
        return "level-unknown"

    if 0 <= val <= 4:
        return "level-black"
    elif 5 <= val <= 9:
        return "level-orange"
    elif 10 <= val <= 19:
        return "level-red"
    elif val >= 20:
        return "level-red-dark"
    return "level-unknown"


@register.filter
def positivity_class(value):
    """Return a CSS class name based on the total_positive value."""
    try:
        value = int(value)
    except (ValueError, TypeError):
        return "level-unknown"

    if value >= 5:
        return "level-green"

    return value
