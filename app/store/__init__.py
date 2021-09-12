from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.vk_api.accessor import VkApiAccessor
        from app.store.admin.accessor import AdminAccessor
        from app.store.game.redis_accessor import RedisGameAccessor

        self.admins = AdminAccessor(app)
        self.vk_api = VkApiAccessor(app)
        self.game = RedisGameAccessor(app)


def setup_store(app: "Application"):
    app.store = Store(app)
