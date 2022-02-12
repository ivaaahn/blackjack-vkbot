import json
from typing import Optional, Mapping, Type

from aio_pika import IncomingMessage

from proj.core.context import FSMGameCtx
from proj.core.middlewares import ErrorHandlerMiddleware
from proj.store import CoreStore
from proj.store.rabbitmq import ConfigType
from proj.store.rabbitmq.worker.config import RabbitMQWorkerConfig

from proj.store.rabbitmq.worker.worker import RabbitMQWorker

from proj.store.vk.dataclasses import Update


class GameRequestReceiver(RabbitMQWorker):
    @staticmethod
    def _extract_updates(
        msg: IncomingMessage,
    ) -> Optional[dict]:  # TODO None или же тут {}
        return json.loads(msg.body.decode(encoding="utf-8"))[
            "updates"
        ]  # TODO мб тут класть в rmq сразу апдейты?

    async def handler(self, msg: IncomingMessage):
        updates = self._extract_updates(msg)

        if updates:
            self._logger.debug(f"Updates: {updates}")
            await self._handle_updates(self._pack_updates(updates))

    async def _handle_updates(self, updates: list[Update]) -> None:
        for update in updates:
            self.logger.debug(update)
            await self._handle_update(update)

    async def _handle_update(self, update: Update) -> None:
        async with FSMGameCtx(
            accessor=self.store.game_ctx,
            chat=update.object.message.peer_id,
            msg=update.object.message,
        ).proxy() as ctx:
            await ErrorHandlerMiddleware.exec(ctx.state, self.store, ctx)

    @staticmethod
    def _pack_updates(updates: dict) -> list[Update]:
        return [
            Update.from_dict(u)
            for u in updates
            if u["type"] == "message_new"  # TODO костыль
        ]
