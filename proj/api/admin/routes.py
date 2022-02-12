from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..application import ApiApplication


def setup_routes(app: "ApiApplication"):
    from .views import (
        AdminLoginView,
        AdminLogoutView,
        AdminCurrentView,
    )

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.logout", AdminLogoutView)
    app.router.add_view("/admin.current", AdminCurrentView)
