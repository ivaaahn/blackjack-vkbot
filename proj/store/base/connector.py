import asyncio
from asyncio import Future, Task, create_task, CancelledError
from typing import Optional

from .accessor import Accessor, ConnectAccessor
from . import BaseStore

import asyncio
import functools


def _release_waiter(waiter, *args):
    if not waiter.done():
        waiter.set_result(None)


async def cancel_and_wait(task: Task):
    """Cancel the *fut* future or task and wait until it completes."""
    loop = asyncio.get_event_loop()

    waiter = loop.create_future()
    cb = functools.partial(_release_waiter, waiter)
    task.add_done_callback(cb)

    try:
        task.cancel()
        # We cannot wait on *fut* directly to make
        # sure _cancel_and_wait itself is reliably cancellable.
        await waiter
    finally:
        task.remove_done_callback(cb)


class Connector:
    def __init__(self, store: BaseStore) -> None:
        self._store = store
        self._logger = store.app.get_logger("Connector")

        self._accessors = {}

        self.__connected_tasks: list[Task] = []
        self.__connected_async_tasks = None

    @property
    def store(self) -> BaseStore:
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
            self.__connected_async_tasks = None

            if f.cancelled():
                self._logger.warning("connect_async is cancelled")
                return

            if f.done() and f.exception():
                self._logger.exception(f.exception())

        self.__connected_async_tasks = asyncio.create_task(self.connect())
        self.__connected_async_tasks.add_done_callback(on_done)
        return self.__connected_async_tasks

    async def connect(self):
        try:
            all_success = True

            def on_all_connected(t: Task) -> None:
                nonlocal all_success

                if all_success:
                    self._logger.info("Connected to all")
                else:
                    self._logger.warning("Store connection finished with errors")

                self.__connected_tasks = []

            def on_one_connected(t: Task) -> None:
                nonlocal all_success

                accessor_name = getattr(t, "_accessor_name", "UNKNOWN_TYPE")

                if t.cancelled():
                    all_success = False
                    self._logger.error(
                        f'Connection to accessor "{accessor_name}" is cancelled'
                    )
                    return

                if exc := t.exception():
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
        except CancelledError as err:
            self._logger.debug(f"Task was cancelled: {err}")
        except Exception as err:
            self._logger.exception(f"Error while connecting: {err}")

    async def disconnect(self) -> None:
        if self.__connected_tasks:
            for task in self.__connected_tasks:
                if not task.done():
                    task.cancel()

        if self.__connected_async_tasks and not self.__connected_async_tasks.done():
            await cancel_and_wait(self.__connected_async_tasks)

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
