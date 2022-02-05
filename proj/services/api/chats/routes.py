import typing

if typing.TYPE_CHECKING:
    from ..web.app import Application


def setup_routes(app: "Application"):
    from .views import ChatsView

    app.router.add_view("/chats", ChatsView)
