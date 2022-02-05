import asyncio
import logging
from asyncio import Future, Task, create_task, CancelledError
from logging import getLogger
from typing import Optional

from .accessor import S, Accessor, ConnectAccessor
from ...services.app_logger import get_logger


class Connector:
    def __init__(self, store: S) -> None:
        self._store = store
        self._logger = get_logger("store_connector")

        self._accessors = {}

        self.__connected_tasks: list[Task] = []
        self.__connect_async_task = None

    @property
    def store(self) -> S:
        return self._store

    def add(self, accessor: Accessor) -> "Connector":
        if accessor.name in self._accessors:
            raise ValueError(f"Accessor {accessor.name} is already registered")

        self._logger.debug(f"[+] {accessor.name} was registered")
        self._accessors[accessor.name] = accessor
        return self

    def connect_async(self) -> Optional[Task]:
        self._logger.debug("Connector (async) started...")

        def on_done(f: Future):
            self.__connect_async_task = None

            if f.cancelled():
                self._logger.warning("connect_async is cancelled")
                return

            if f.done() and f.exception():
                self._logger.exception(f.exception())

        self.__connect_async_task = asyncio.create_task(self.connect())
        self.__connect_async_task.add_done_callback(on_done)
        return self.__connect_async_task

    async def connect(self):
        try:
            all_success = True

            def on_all_connected(f: Future) -> None:
                nonlocal all_success

                if all_success:
                    self._logger.info("Connected to all")
                else:
                    self._logger.warning("Store connection finished with errors")

                self.__connected_tasks = []

            def on_one_connected(f: Future) -> None:
                nonlocal all_success

                accessor_name = getattr(f, "_accessor_name", "UNKNOWN_TYPE")

                if f.cancelled():
                    all_success = False
                    self._logger.error(
                        f'Connection to accessor "{accessor_name}" is cancelled'
                    )
                    return

                if exc := f.exception():
                    all_success = False
                    self._logger.error(
                        f'Exception while connecting to accessor "{accessor_name}" : {exc}',
                        exc_info=exc,
                    )

                self._logger.debug(f"Accessor {accessor_name} successfully connected")

            tasks = []

            if self._accessors:
                for accessor_type, accessor in self._accessors.items():
                    if not isinstance(accessor, ConnectAccessor):
                        continue

                    task = create_task(accessor.connect(), name=accessor_type)
                    task.add_done_callback(on_one_connected)
                    task._accessor_name = accessor_type
                    tasks.append(task)

            if not tasks:
                self._logger.info("No accessors to connect")
                return

            self.__connected_tasks = tasks

            waiting_for_tasks = create_task(
                asyncio.wait(self.__connected_tasks, return_when=asyncio.ALL_COMPLETED)
            )
            waiting_for_tasks.add_done_callback(on_all_connected)

            await waiting_for_tasks
        except CancelledError:
            pass
        except Exception as err:
            self._logger.exception(f"Error while connecting: {err}")

    async def disconnect(self) -> None:
        if self.__connected_tasks:
            for task in self.__connected_tasks:
                if not task.done():
                    task.cancel()
        # if self.__connected_async_tasks and not self.__connected_async_tasks.done():
        #     await cancel_and_wait(self.__connected_async_tasks)

        try:
            if self._accessors:
                for accessor in self._accessors.values():
                    if not isinstance(accessor, ConnectAccessor):
                        continue

                    await accessor.disconnect()
                self._logger.info("Disconnected from all accessors")

        except Exception as err:
            self._logger.exception(f"Error while disconnecting: {err}")

    async def wait_connected(self) -> None:
        coros = []

        for accessor_type, accessor in self._accessors.items():
            if not isinstance(accessor, ConnectAccessor):
                continue

            coros.append(create_task(accessor.wait_connected()))

        if coros:
            await asyncio.wait(coros)
