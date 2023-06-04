import asyncio
from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any, List

from asyncio_channel import create_channel
from asyncio_channel._channel import Channel

from datagen.api.client.exceptions import HttpStatusHandler
from datagen.api.client.schemas import ErrorResponse, parse_error
from datagen.api.client.session import ClientSession, SessionsResponse
from datagen.dev.logging import get_logger

logger = get_logger(__name__)


class Task(ABC):
    """
    Abstract base class for tasks.

    A task represents a unit of work that can be executed asynchronously.
    Tasks can take input from a channel and produce output on another channel.
    """

    def __init__(self, **kwargs):
        self.input_channel = None
        self.output_channel = None

    def setup(self) -> None:
        self.input_channel = create_channel()
        self.output_channel = create_channel()

    @abstractmethod
    async def execute(self) -> None:
        pass

    async def _get_input(self) -> Any:
        return await self.input_channel.take()


class SessionTask(Task):
    """
    This task is used when you want tasks to share the same aiohttp.ClintSession.
    It is advised to run ClientTasks or a CollectionTask that contains ClientTasks inside a SessionTask
    for improved performance.
    """

    def __init__(
        self,
        task: Task,
        session: ClientSession,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._task = task
        self._session = session

    def setup(self) -> None:
        self._task.setup()
        self.input_channel = self._task.input_channel
        self.output_channel = self._task.output_channel

    async def execute(self) -> None:
        async with self._session:
            await self._task.execute()


class ClientTask(Task):
    """
    Base class for tasks that require an ClientSession.
    Use derived class of ClientTask only inside a SessionTask, e.g. the task input of a SessionTask will be a ClientTask
    or a CollectionTask that contains SessionTask.
    """

    def __init__(
        self,
        session: ClientSession,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._session = session
        self._url = ""

    def _handle_response(self, response: SessionsResponse, **kwargs) -> Any:
        if response.status_code not in [HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.ACCEPTED]:
            error = ErrorResponse(**parse_error(response.payload))
            HttpStatusHandler.handle(
                status_code=response.status_code, message=self._error_message(error_msg=str(error), **kwargs)
            )

        logger.info(self._success_message(**kwargs))

    @abstractmethod
    def _error_message(self, error_msg: str, **kwargs) -> str:
        pass

    @abstractmethod
    def _success_message(self, **kwargs) -> str:
        pass


class TaskCollection(Task):
    def __init__(self, tasks: List[Task], **kwargs):
        super().__init__(**kwargs)
        self._tasks = tasks

    def setup(self) -> None:
        super().setup()
        for task in self._tasks:
            task.setup()


class TaskChain(TaskCollection):
    """
    A chain of tasks to be executed one sequentially.
    """

    def __init__(self, tasks: List[Task], **kwargs):
        super().__init__(tasks=tasks, **kwargs)

    def setup(self) -> None:
        super().setup()
        for idx, task in enumerate(self._tasks):
            if idx == 0:
                task.input_channel = self.input_channel
            else:
                task.input_channel = self._tasks[idx - 1].output_channel

            if idx == len(self._tasks) - 1:
                task.output_channel = self.output_channel
            else:
                task.output_channel = self._tasks[idx + 1].input_channel

    async def execute(self) -> None:
        for task in self._tasks:
            await task.execute()


class TaskGroup(TaskCollection):
    """
    A group of tasks to be executed one asynchronously without a specific order.
    """

    def __init__(self, tasks: List[Task], **kwargs):
        super().__init__(tasks=tasks, **kwargs)

    async def execute(self) -> None:
        await self._get_input()
        await asyncio.gather(*(task.execute() for task in self._tasks))
        await self.output_channel.put(await self._get_output())

    async def _get_input(self) -> Any:
        batches = await self.input_channel.take()
        for batch, task in zip(batches, self._tasks):
            await task.input_channel.put(batch)

    async def _get_output(self) -> Any:
        return await asyncio.gather(*(task.output_channel.take() for task in self._tasks))

    def _get_src_channel(self) -> Channel:
        return self.input_channel
