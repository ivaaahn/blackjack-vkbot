from proj.core.context import FSMGameCtx
from proj.core.middlewares import ErrorHandlerMiddleware

from proj.services.worker.base import AbstractWorker

from proj.store import Store
from proj.store.vk.dataclasses import Update


class Worker(AbstractWorker[Store, None]):
    async def handle_updates(self, updates: list[Update]) -> None:
        for update in updates:
            await self._handle_update(update)

    async def _handle_update(self, update: Update) -> None:
        async with FSMGameCtx(
            accessor=self.store.game_ctx,
            chat=update.object.message.peer_id,
            msg=update.object.message,
        ).proxy() as ctx:
            await ErrorHandlerMiddleware.exec(ctx.state, self.store, ctx)
