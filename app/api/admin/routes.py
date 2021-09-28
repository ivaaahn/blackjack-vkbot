from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.app import Application


def setup_routes(app: 'Application'):
    from .views import AdminLoginView
    from .views import AdminLogoutView
    from .views import AdminCurrentView

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.logout", AdminLogoutView)
    app.router.add_view("/admin.current", AdminCurrentView)
