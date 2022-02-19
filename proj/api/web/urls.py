import typing

if typing.TYPE_CHECKING:
    from ..application import ApiApplication


def setup_routes(app: "ApiApplication"):
    from ..admin.routes import setup_routes as admin_setup_routes
    from ..players.routes import setup_routes as players_setup_routes
    from ..chats.routes import setup_routes as chats_setup_routes
    from ..game_settings.routes import setup_routes as game_settings_setup_routes

    admin_setup_routes(app)
    players_setup_routes(app)
    chats_setup_routes(app)
    game_settings_setup_routes(app)
