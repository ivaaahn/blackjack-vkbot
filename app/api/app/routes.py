from aiohttp.web_app import Application


def setup_routes(app: Application):
    from app.api.admin.routes import setup_routes as admin_setup_routes
    from app.api.players.routes import setup_routes as players_setup_routes
    from app.api.chats.routes import setup_routes as chats_setup_routes
    from app.api.game_settings.routes import setup_routes as game_settings_setup_routes

    admin_setup_routes(app)
    players_setup_routes(app)
    chats_setup_routes(app)
    game_settings_setup_routes(app)
