import json
from pathlib import Path
from typing import List, Optional, Union

from datagen.api.assets import (
    Background,
    Camera,
    DataRequest,
    GenerationRequest,
    Glasses,
    Human,
    HumanDatapoint,
    Light,
    Mask,
    SequenceRequest,
)
from datagen.api.client.schemas import DataResponse, DataResponseStatus, DownloadRequest, DownloadURL
from datagen.api.requests.datapoint.builder import HumanDatapointBuilder
from datagen.api.requests.director import DataRequestDirector
from datagen.config import settings
from datagen.core.tasks import TaskContainer
from datagen.core.tasks.task_runner import TaskRunner
from datagen.dev.logging import get_logger

logger = get_logger(__name__)

DEFAULT_DATAPOINT_REQUESTS_JSON_NAME = "datagen_data_request.json"


class DatagenAPI:
    def __init__(self):
        self._request_director = DataRequestDirector()
        self._task_container = TaskContainer()
        self._task_runner = TaskRunner()

    def create_datapoint(
        self,
        human: Human,
        camera: Camera,
        glasses: Optional[Glasses] = None,
        mask: Optional[Mask] = None,
        background: Optional[Background] = None,
        lights: Optional[List[Light]] = None,
    ) -> HumanDatapoint:
        self._request_director.builder = HumanDatapointBuilder(
            human=human, camera=camera, glasses=glasses, mask=mask, background=background, lights=lights
        )
        return self._request_director.build_datapoint()

    def load(self, path: Union[Path, str]) -> GenerationRequest:
        path = DatagenAPI._get_request_json_path(path=path)
        request_dict = json.loads(path.read_text())
        return DataRequest(**request_dict) if "datapoints" in request_dict else SequenceRequest(**request_dict)

    def generate(
        self,
        request: GenerationRequest,
        generation_name: str,
    ) -> DataResponse:
        batches = DatagenAPI.batch_request(request)
        return self._task_runner.run(
            task=self._task_container.pipeline_factory.data_generation(number_of_batches=len(batches)),
            data=(batches, generation_name),
        )

    def stop(self, generation_id) -> None:
        self._task_runner.run(
            task=self._task_container.client_task(task_name="stop_generation"),
            data=generation_id,
        )

    def get_status(self, generation_id: str) -> DataResponseStatus:
        return self._task_runner.run(
            task=self._task_container.client_task(task_name="status"),
            data=generation_id,
        )

    def get_download_urls(self, generation_id: str) -> List[DownloadURL]:
        return self._task_runner.run(
            task=self._task_container.client_task(task_name="get_download_links"),
            data=generation_id,
        )

    def download(
        self, urls: List[DownloadURL], dest_folder: str, dataset_name: str, remove_tar_files: bool = True
    ) -> None:
        self._task_runner.run(
            task=self._task_container.pipeline_factory.download(
                number_of_files=len(urls), remove_tar_files=remove_tar_files
            ),
            data=DownloadRequest(urls=urls, path=dest_folder, dataset_name=dataset_name).batch(),
        )

    def dump(self, request: GenerationRequest, path: Union[Path, str] = None) -> None:
        path = DatagenAPI._get_request_json_path(path=path, create_if_not_exists=True)
        path.write_text(json.dumps(request.dict(), indent=3, sort_keys=True))
        logger.info(
            f"Request was successfully dumped to path '{path.absolute()}'.",
        )

    @staticmethod
    def _get_request_json_path(path: Path, create_if_not_exists: Optional[bool] = False) -> Path:
        if isinstance(path, str):
            path = Path(path)

        if not path and not create_if_not_exists:
            raise FileNotFoundError(f"Path '{path}' does not exist or is not a file.")

        if path and path.parent.exists():
            return path

        logger.error(f"Path '{path}' does not exist or is not a file.")

        default_path = Path.cwd().joinpath(DEFAULT_DATAPOINT_REQUESTS_JSON_NAME)
        logger.info(f"A file was created in a default location: {default_path.absolute()}")
        default_path.touch()
        return default_path

    @staticmethod
    def batch_request(request: GenerationRequest) -> List[GenerationRequest]:
        batches = []
        if isinstance(request, DataRequest):
            batch_size = settings["batch_size"]
            datapoints_num = len(request.datapoints)
            batches.extend(
                DataRequest(datapoints=request.datapoints[dp_idx : dp_idx + batch_size])
                for dp_idx in range(0, datapoints_num, batch_size)
            )
        elif isinstance(request, SequenceRequest):
            batches = [request]
        return batches
