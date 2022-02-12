from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..application import ApiApplication


def setup_routes(app: "ApiApplication"):
    from .views import PlayersView

    app.router.add_view("/players", PlayersView)
