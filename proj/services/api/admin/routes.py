from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..web.app import Application


def setup_routes(app: "Application"):
    from .views import (
        AdminLoginView,
        AdminLogoutView,
        AdminCurrentView,
    )

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.logout", AdminLogoutView)
    app.router.add_view("/admin.current", AdminCurrentView)
