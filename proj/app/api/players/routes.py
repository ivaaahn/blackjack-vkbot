from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.app import Application


def setup_routes(app: "Application"):
    from .views import PlayersView

    app.router.add_view("/players", PlayersView)
