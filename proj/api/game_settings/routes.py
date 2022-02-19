from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..application import ApiApplication


def setup_routes(app: "ApiApplication"):
    from .views import GameSettingsView

    app.router.add_view("/game_settings", GameSettingsView)
