"""
Context processors for Teachka.

Provides dynamic data to all templates.
"""


def navigation(request):
    """
    Provides navigation items for the sidebar.

    Returns a list of navigation items with:
    - name: Display name
    - url: URL name (for {% url %} tag)
    - icon: Lucide icon name
    - active: Whether this item is currently active
    """
    nav_items = [
        {
            "name": "Home",
            "url": "home",
            "icon": "home",
            "path": "/",
        },
        {
            "name": "Grade Calculator",
            "url": "grade_calculator:home",
            "icon": "calculator",
            "path": "/grades/",
        },
        {
            "name": "Group Maker",
            "url": "group_maker:group_list",
            "icon": "users",
            "path": "/groups/",
        },
        {
            "name": "Karma Points",
            "url": "point_system:dashboard",
            "icon": "star",
            "path": "/karma/",
        },
        {
            "name": "Group Divider",
            "url": "group_divider:home",
            "icon": "split",
            "path": "/divider/",
        },
        {
            "name": "Wheel",
            "url": "wheel:wheel",
            "icon": "circle-dot",
            "path": "/wheel/",
        },
        {
            "name": "Timer",
            "url": "timer:timer",
            "icon": "timer",
            "path": "/timer/",
        },
    ]

    # Mark active item based on current path
    current_path = request.path
    for item in nav_items:
        # Check if current path starts with the nav item's path
        # Special case for home to avoid matching everything
        if item["path"] == "/":
            item["active"] = current_path == "/"
        else:
            item["active"] = current_path.startswith(item["path"])

    return {"nav_items": nav_items}
