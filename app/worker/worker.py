import asyncio
import json
import traceback

from aio_pika import IncomingMessage

from app.config import setup_config, Config
from app.databases import setup_databases, Databases, Rabbit
from app.game.dataclasses import GAccessors
from app.game.game import GameCtx
from app.game.logic import do_force_cancel
from app.game.states import States
from app.store import setup_store, Store
from app.store.vk_api.dataclasses import Update, UpdateObject, UpdateMessage

from app.store.players.accessor import PlayersAccessor
from app.store.vk_api.accessor import VkApiAccessor
from app.base.base_game_accessor import BaseGameAccessor
from app.store.game_settings.accessor import GameSettingsAccessor

from app.app_logger import get_logger

logger = get_logger(__file__)


class Worker:
    def __init__(self, store: Store, databases: Databases, config: Config):
        self.store = store
        self.databases = databases
        self.config = config

    @property
    def vk_api(self) -> VkApiAccessor:
        return self.store.vk_api

    @property
    def rabbit(self) -> Rabbit:
        return self.databases.rabbit

    @property
    def g_accessor(self) -> BaseGameAccessor:
        return self.store.game

    @property
    def p_accessor(self) -> PlayersAccessor:
        return self.store.players

    @property
    def gs_accessor(self) -> GameSettingsAccessor:
        return self.store.game_settings

    async def start(self) -> None:
        logger.info('Worker starting ...')

        await self.databases.connect_for_worker()
        await self.store.connect_for_worker()

        await self.rabbit.register_consumer(self.handle_rabbit_msg)
        logger.info('Poller started')

    async def stop(self) -> None:
        logger.info('Poller stopping ...')
        await self.store.disconnect_for_worker()
        await self.databases.disconnect_for_worker()
        logger.info('Poller stopped')

    async def handle_rabbit_msg(self, msg: IncomingMessage) -> None:
        async with msg.process():
            updates_json = json.loads(msg.body.decode(encoding='utf-8'))['updates']
            if updates_json:
                await self.handle_updates(self._pack_updates(updates_json))

    async def handle_updates(self, updates: list[Update]) -> None:
        import app.game.handlers  # DO NOT DELETE
        for update in updates:
            msg = update.object.message
            async with GameCtx(self.g_accessor, msg.peer_id, msg).proxy() as ctx:
                if ctx.state is None:
                    ctx.state = States.WAITING_FOR_TRIGGER

                accessors = GAccessors(self.vk_api, self.p_accessor, self.gs_accessor)

                try:
                    await ctx.state.handler(ctx, accessors)
                except Exception as e:
                    logger.exception(f'Exception during processing bot logic: "{e}"')
                    await do_force_cancel(ctx, accessors)

    @staticmethod
    def _pack_updates(raw_updates: dict) -> list[Update]:
        return [
            Update(
                type=u['type'],
                object=UpdateObject(
                    message=UpdateMessage(
                        from_id=u['object']['message']['from_id'],
                        text=u['object']['message']['text'],
                        id=u['object']['message']['id'],
                        peer_id=u['object']['message']['peer_id'],
                        payload=u['object']['message'].get('payload')
                    ))) for u in raw_updates if u['type'] == 'message_new']


def setup_worker(config_path: str) -> Worker:
    config = setup_config(config_path)
    databases = setup_databases(config)
    store = setup_store(databases, config)
    return Worker(store, databases, config)


def run_worker(worker: Worker) -> None:
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(worker.start())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt')
    finally:
        loop.run_until_complete(worker.stop())
        logger.info('Closing loop ...')
        loop.close()
        logger.info('Loop closed')
