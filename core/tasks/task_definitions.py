import asyncio
import os
import tarfile
from http import HTTPStatus
from pathlib import Path
from typing import Any, List, Tuple

import aiofiles
from aiohttp import ClientPayloadError

from datagen.api.client.schemas import DataResponse, DataResponseStatus, DownloadURL
from datagen.api.client.session import ClientSession, SessionsResponse
from datagen.core.tasks.task import ClientTask, Task
from datagen.dev.logging import get_logger

logger = get_logger(__name__)


class StopGenerationTask(ClientTask):
    """
    A task that stops a data generation process.

    This task sends an HTTP POST data to the Datagen services to stop the data generation
    process with the specified generation id.

    In order to use this task you need to have previously started a data generation process, so you need to pass a
    generation id as input.
    Input for this task is a generation_id.
    """

    def __init__(
        self,
        session: ClientSession,
        **kwargs,
    ):
        super().__init__(session=session, **kwargs)

        self._url = "/v1/generations/{generation_id}/stop"

    async def execute(self) -> None:
        generation_id = await self._get_input()
        session = self._session.session
        async with session.post(url=self._url.format(generation_id=generation_id)) as resp:
            self._handle_response(
                response=SessionsResponse(status_code=resp.status, payload=await resp.json()),
                generation_id=generation_id,
            )
            await self.output_channel.put(True)

    def _error_message(self, error_msg: str, **kwargs) -> str:
        return f"Failed to stop generation: {kwargs['generation_id']} with error: {error_msg}"

    def _success_message(self, **kwargs) -> str:
        return f"Successfully stopped data generation: {kwargs['generation_id']}."


class StatusTask(ClientTask):
    """
    A task that queries the current generation status.

    Generation status consists of: time estimation in ms, process percentage and the status of the process
    (e.g. STARTED, IN-PROGRESS, etc.)

    This task sends an HTTP GET data to the Datagen services to query the data generation
    status with the specified generation id.

    In order to use this task you need to have previously started a data generation process, so you need to pass a
    generation id as input.

    Input: generation_id.
    Output: GenerationStatus
    """

    def __init__(
        self,
        session: ClientSession,
        **kwargs,
    ):
        super().__init__(session=session, **kwargs)
        self._url = "/v1/generations/{generation_id}/status"

    async def execute(self) -> None:
        generation_id = await self._get_input()
        session = self._session.session
        async with session.get(url=self._url.format(generation_id=generation_id)) as resp:
            response = SessionsResponse(status_code=resp.status, payload=await resp.json())
            self._handle_response(response=response, generation_id=generation_id)
            await self.output_channel.put(DataResponseStatus(**response.payload))

    def _error_message(self, error_msg: str, **kwargs) -> str:
        return f"Failed to receive generation status of: {kwargs['generation_id']} with error: {error_msg}"

    def _success_message(self, **kwargs) -> str:
        return f"Successfully received generation status of: {kwargs['generation_id']}."


class GetDownloadURLsTask(ClientTask):
    """
    A task that gets the download URLs for the output files of a data generation process.

    The URLs will have an expiration date. In case of an expired date: please use this task again to gen new URLs.

    This task sends an HTTP GET data to Datagen services to get the download URLs for the output files of the data
    generation process with the specified generation id.

    If the generation is still in progress, an empty list will be returned.
    Input: generation_id.
    Output: list of urls to files.
    """

    def __init__(
        self,
        session: ClientSession,
        **kwargs,
    ):
        super().__init__(session=session, **kwargs)
        self._url = "/v1/generations/{generation_id}/download"

    async def execute(self) -> None:
        generation_id = await self._get_input()
        session = self._session.session
        async with session.get(url=self._url.format(generation_id=generation_id)) as resp:
            response = SessionsResponse(status_code=resp.status, payload=await resp.json())
            if response.status_code == HTTPStatus.ACCEPTED:
                logger.info(
                    f"Data generation is in progress. Download URLs for generation ID "
                    f"{generation_id} will soon be ready."
                )
            else:
                self._handle_response(response=response, generation_id=generation_id)

            response = [DownloadURL.parse_url(url=url) for url in response.payload]
            await self.output_channel.put(response)

    def _error_message(self, error_msg: str, **kwargs) -> str:
        return f"Failed to get download URLs of: {kwargs['generation_id']} with error: {error_msg}"

    def _success_message(self, **kwargs) -> str:
        return f"Successfully received download URLs of: {kwargs['generation_id']}."


class InitDataGenerationTask(ClientTask):
    """
    A task that initializes a data generation request process.
    For data with 2000 datapoints or less, use DataGenerationTask.

    This task sends an HTTP GET data to Datagen services to initialize a multi-stage data generation process.
    If request was successful, you will receive a generation id that you'll pass forward to UploadRequestTask and
    FinalizeDataGenerationTask.
    """

    def __init__(
        self,
        session: ClientSession,
        **kwargs,
    ):
        super().__init__(session=session, **kwargs)
        self._url = "/v1/generations"

    async def execute(self) -> None:
        request, name = await self._get_input()
        session = self._session.session
        async with session.post(url=self._url, json={"title": name}) as resp:
            response = SessionsResponse(status_code=resp.status, payload=await resp.json())
            self._handle_response(response=response)
            generation_id = response.payload["generation_id"]
            await self.output_channel.put([(generation_id, batch) for batch in request])

    def _error_message(self, error_msg: str, **kwargs) -> str:
        return f"Failed to initialize generation request with error: {error_msg}"

    def _success_message(self, **kwargs) -> str:
        return "Successfully initialized generation request."


class UploadRequestTask(ClientTask):
    """
    A task that uploads a data generation request.

    This task sends an HTTP POST data to Datagen services to initialize that a multi-stage data generation process.
    This tasks depend on InitDataGenerationTask's output.

    Input: generation_id, DataRequest (a batch with datapoints < 2000)
    Output: DataRequest object with dgu-hour cost, number of datapoints, number od scenes
    """

    def __init__(
        self,
        session: ClientSession,
        **kwargs,
    ):
        super().__init__(session=session, **kwargs)
        self._url = "/v1/generations/{generation_id}"

    async def execute(self) -> None:
        generation_id, request = await self._get_input()
        session = self._session.session
        async with session.put(url=self._url.format(generation_id=generation_id), json=request.dict()) as resp:
            response = SessionsResponse(status_code=resp.status, payload=await resp.json())
            self._handle_response(response=response, generation_id=generation_id)
            await self.output_channel.put(DataResponse(**response.payload))

    def _error_message(self, error_msg: str, **kwargs) -> str:
        return (
            f"Failed to upload generation request for generation id: {kwargs['generation_id']} with error: {error_msg}"
        )

    def _success_message(self, **kwargs) -> str:
        return f"Successfully uploaded generation request of generation id: {kwargs['generation_id']}."


class FinalizeDataGenerationTask(ClientTask):
    """
    This is the third and last part of the multipart request upload.
    Once you uploaded your requests with UploadRequestTask, use this task to trigger the data generation process.

    This task sends an HTTP POST data to Datagen services to start the data generation process itself.
    This tasks depend on UploadRequestTask's output.

    Input: generation_id
    Output: DataRequest object with dgu-hour cost, number of datapoints, number od scenes
    """

    def __init__(self, session: ClientSession, **kwargs):
        super().__init__(session=session, **kwargs)
        self._url = "/v1/generations/{generation_id}"

    async def execute(self) -> None:
        generation_id = await self._get_input()
        session = self._session.session
        async with session.post(url=self._url.format(generation_id=generation_id)) as resp:
            response = SessionsResponse(status_code=resp.status, payload=await resp.json())
            self._handle_response(response=response, generation_id=generation_id)
            await self.output_channel.put(DataResponse(**response.payload))

    async def _get_input(self) -> Any:
        upload_response = await self.input_channel.take()
        return upload_response[0].generation_id

    def _error_message(self, error_msg: str, **kwargs) -> str:
        return (
            f"Failed to finalize generation request for generation id: {kwargs['generation_id']} "
            f"with error: {error_msg}."
        )

    def _success_message(self, **kwargs) -> str:
        return f"Successfully finalized generation request for generation id: {kwargs['generation_id']}."


class DownloadFileTask(ClientTask):
    """
    This dask downloads a single file to a requested dictionary.
    """

    def __init__(self, session: ClientSession, **kwargs):
        super().__init__(session=session, **kwargs)
        self._lock = asyncio.Lock()

    async def execute(self) -> None:
        download_url = await self._get_input()
        session = self._session.session
        logger.info(f"Starting download from {download_url.url}. The file will be located at {download_url.filename}")
        async with session.get(url=download_url.url) as resp:
            if resp.status != HTTPStatus.OK:
                logger.error(self._error_message(error_msg="Download failed.", url=download_url.url))
                resp.raise_for_status()
            async with aiofiles.open(download_url.filename, "wb") as file:
                chunk_size = 10 * 1024 * 1024  # 10MB
                try:
                    async for chunk in resp.content.iter_chunked(chunk_size):
                        await file.write(chunk)
                except ClientPayloadError as e:
                    print(e)

            logger.info(self._success_message(url=download_url.url, filename=download_url.filename))
            await self.output_channel.put((download_url.filename, download_url.dataset_name))

    def _error_message(self, error_msg: str, **kwargs) -> str:
        return f"Failed to download {kwargs['url']} with error: {error_msg}."

    def _success_message(self, **kwargs) -> str:
        return f"Successfully downloaded {kwargs['url']} to {kwargs['filename']}."


class ExtractFilesTask(Task):
    """
    This task receives a list of files, merges them into 1 file and extracts it to the requested directory.
    """

    def __init__(self, remove_tar_files: bool = True, **kwargs):
        super().__init__(**kwargs)
        self._remove_tar_files = remove_tar_files

    async def execute(self) -> None:
        paths, compressed_file, dest_file = await self._get_input()
        if len(paths) > 1:
            ExtractFilesTask._merge_file(paths=paths, merged_tar=compressed_file)

        ExtractFilesTask._extract(src=compressed_file, dst=dest_file)

        if self._remove_tar_files:
            ExtractFilesTask._remove_files(paths=paths)

        await self.output_channel.put(dest_file)

    async def _get_input(self) -> Any:
        file_paths = await self.input_channel.take()
        dataset_names = set(name for _, name in file_paths)
        if len(dataset_names) != 1:
            raise ValueError("Got invalid download links. all links must relate to the same dataset.")
        return ExtractFilesTask._export_urls(file_paths=file_paths)

    @staticmethod
    def _export_urls(file_paths: Tuple[Any, ...]) -> Tuple[Tuple[Any, ...], str, str]:
        urls = tuple(url for url, _ in file_paths)
        if len(file_paths) == 1:
            compressed_file = str(Path(file_paths[0][0]))
            dest_file = str(Path(file_paths[0][0]).parent.joinpath(file_paths[0][1]))
            return urls, compressed_file, dest_file
        else:
            compressed_file = str(Path(file_paths[0][0]).parent.joinpath(file_paths[0][1] + ".tar.gz"))
            return urls, compressed_file, compressed_file.replace(".tar.gz", "")

    @staticmethod
    def _merge_file(paths: List[str], merged_tar: str) -> None:
        try:
            with tarfile.open(merged_tar, mode="w:gz") as merged_file:
                names = []
                for filename in paths:
                    with tarfile.open(filename, mode="r:gz") as file:
                        members = [m for m in file.getmembers() if m.name not in names]
                        names += file.getnames()
                        for member in members:
                            if member.isdir():
                                merged_file.addfile(member)
                            else:
                                merged_file.addfile(member, file.extractfile(member))

                logger.info(f"Successfully merged {len(paths)} files to {merged_tar}.")
        except Exception as e:
            logger.error(f"Failed to merge tar.gz files to {merged_file}.")
            raise e

    @staticmethod
    def _extract(src: str, dst: str) -> None:
        try:
            with tarfile.open(src, "r:gz") as tar:
                tar.extractall(path=dst)
                logger.info(f"Successfully extracted file to {dst}.")
        except Exception as e:
            logger.error(f"Failed to extract {dst}.")
            raise e

    @staticmethod
    def _remove_files(paths: List[str]) -> None:
        for path in paths:
            try:
                os.remove(path=path)
                logger.info(f"Successfully removed file: {path}.")
            except Exception as e:
                logger.error(f"Failed to removed {path} with error: {str(e)}.")
