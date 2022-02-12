import typing

if typing.TYPE_CHECKING:
    from ..application import ApiApplication


def setup_routes(app: "ApiApplication"):
    from .views import ChatsView

    app.router.add_view("/chats", ChatsView)
