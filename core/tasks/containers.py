from dependency_injector import containers, providers

from datagen.api.client.containers import SessionContainer
from datagen.core.tasks.task import SessionTask, Task, TaskChain, TaskGroup
from datagen.core.tasks.task_definitions import (
    DownloadFileTask,
    ExtractFilesTask,
    FinalizeDataGenerationTask,
    GetDownloadURLsTask,
    InitDataGenerationTask,
    StatusTask,
    StopGenerationTask,
    UploadRequestTask,
)
from datagen.dev.logging import get_logger

logger = get_logger(__name__)


def create_data_generation_pipeline(task_container: containers.DeclarativeContainer, number_of_batches: int) -> Task:
    session = SessionContainer.client_session()
    init_task = task_container.task_factory.initialize(session=session)
    upload_tasks = task_container.collection_factory.task_group(
        tasks=[task_container.task_factory.upload(session=session) for _ in range(number_of_batches)],
    )
    finalize_task = task_container.task_factory.finalize(session=session)
    multipart_task = task_container.collection_factory.task_chain(tasks=[init_task, upload_tasks, finalize_task])
    session_task = SessionTask(
        task=multipart_task,
        session=session,
    )
    return session_task


def create_download_pipeline(
    task_container: containers.DeclarativeContainer, number_of_files: int, remove_tar_files: bool
) -> Task:
    session = SessionContainer.client_session(
        base_url=None, headers={"Connection": "keep-alive"}, timeout=SessionContainer.long_timeout()
    )
    download_task = task_container.collection_factory.task_group(
        tasks=[task_container.task_factory.download_file(session=session) for _ in range(number_of_files)],
    )
    extract_task = task_container.task_factory.extract_files(remove_tar_files=remove_tar_files)
    download_pipeline = task_container.collection_factory.task_chain(tasks=[download_task, extract_task])
    session_task = SessionTask(task=download_pipeline, session=session)
    return session_task


def create_client_task(task_container: containers.DeclarativeContainer, task_name: str, **kwargs) -> Task:
    session = SessionContainer.client_session()
    task = task_container.task_factory.providers[task_name](session=session, **kwargs)
    return SessionTask(task=task, session=session)


class TaskContainer(containers.DeclarativeContainer):

    __self__ = providers.Self()

    task_factory = providers.FactoryAggregate(
        stop_generation=providers.Factory(StopGenerationTask),
        get_download_links=providers.Factory(GetDownloadURLsTask),
        status=providers.Factory(StatusTask),
        initialize=providers.Factory(InitDataGenerationTask),
        upload=providers.Factory(UploadRequestTask),
        finalize=providers.Factory(FinalizeDataGenerationTask),
        extract_files=providers.Factory(ExtractFilesTask),
        download_file=providers.Factory(DownloadFileTask),
    )

    client_task = providers.Callable(create_client_task, task_container=__self__)

    collection_factory = providers.FactoryAggregate(
        task_chain=providers.Factory(TaskChain),
        task_group=providers.Factory(TaskGroup),
    )

    pipeline_factory = providers.FactoryAggregate(
        data_generation=providers.Callable(create_data_generation_pipeline, task_container=__self__),
        download=providers.Callable(create_download_pipeline, task_container=__self__),
    )
