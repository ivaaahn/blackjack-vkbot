# import json
# import weakref
# from asyncio import Task
# from typing import Mapping, Optional, Type, Generic
#
# from aio_pika import IncomingMessage
#
# from proj.store.base import S
# from proj.config import ConfigType
# from proj.store.vk.dataclasses import Update, UpdateMessage, UpdateObject
#
#
# class AbstractWorker(Generic[S, ConfigType]):
#     class Meta:
#         name = None
#
#     def __init__(
#         self,
#         store: S,
#         *,
#         name: Optional[str] = None,
#         config: Optional[Mapping] = None,
#         config_type: Type[ConfigType] = None,
#     ) -> None:
#         self._store = weakref.ref(store)
#         self._name = name or self.Meta.name or self.__class__.__name__
#         self._name_is_custom = name is not None
#         self._raw_config = config or store.config.get(self._name) or {}
#         self._parse_config(config_type)
#         self._logger = store.app
#         self._is_running = False
#         self._poll_task: Optional[Task] = None
#
#     @property
#     def store(self) -> S:
#         return self._store
#
#     @property
#     def game_accessor(self):
#         return
#
#     def _parse_config(self, config_type: Type[ConfigType]):
#         try:
#             self._config = config_type(**self._raw_config) if config_type else None
#         except Exception as err:
#             raise ValueError(
#                 f"Error parsing config of {self._name} accessor: {str(err)}"
#             ) from err
#
#     async def start(self) -> None:
#         self._logger.info(f"Worker {self._name} starting...")
#         await self.store.rabbit.register_consumer(self.handle_rabbit_msg)
#         self._logger.info("Worker started")
#
#     async def stop(self) -> None:
#         self._logger.info(f"Worker {self._name} stopped")
#
#     async def handle_rabbit_msg(self, msg: IncomingMessage) -> None:
#         async with msg.process():
#             if updates_json := json.loads(msg.body.decode(encoding="utf-8"))["updates"]:
#                 self._logger.debug(f"Updates: {updates_json}")
#                 await self.handle_updates(self._pack_updates(updates_json))
#
#     async def handle_updates(self, updates: list[Update]) -> None:
#         pass
#
#     @staticmethod
#     def _pack_updates(raw_updates: dict) -> list[Update]:
#         return [
#             Update(
#                 type=u["type"],
#                 object=UpdateObject(
#                     message=UpdateMessage(
#                         from_id=u["object"]["message"]["from_id"],
#                         text=u["object"]["message"]["text"],
#                         id=u["object"]["message"]["id"],
#                         peer_id=u["object"]["message"]["peer_id"],
#                         payload=u["object"]["message"].get("payload"),
#                     )
#                 ),
#             )
#             for u in raw_updates
#             if u["type"] == "message_new"
#         ]
