from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

import cv2

from datagen.components.datapoint import DataPoint
from datagen.modalities.textual.base.environments import Environment


@dataclass
class Sequence:
    scene_path: Path
    camera_name: str
    datapoints: Tuple[DataPoint] = field(repr=False)
    environment: Environment = field(init=False)

    def __post_init__(self):
        self.environment = self._get_sequence_env()

    def _get_sequence_env(self) -> Environment:
        try:
            sequence_envs = set(map(lambda dp: dp.environment, self.datapoints))
            [environment] = list(sequence_envs)
            return environment
        except ValueError:
            # Too many values to unpack
            raise ValueError(f"More than one environment selected for sequence: {sequence_envs}")

    def __iter__(self):
        for datapoint in self.datapoints:
            yield datapoint

    def to_video(
            self, video_name: str = None, fps: int = 30, codec: str = "MJPG", height: int = None, width: int = None
    ) -> cv2.VideoWriter:
        """
        :param video_name Name of the video. Must also include format. If not specified,
        use the sequence's behaviour name, and .mov format
        :param fps:
        :param codec:
        :param height Height of the video. If not specified, use same as the datapoints'
        :param width Width of the video. If not specified, use same as the datapoints'
        """
        video = self._create_video(video_name, fps, codec, height, width)
        self._write_images(video)
        video.release()
        return video

    def _create_video(self, video_name: str, fps: int, codec: str, height: int, width: int) -> cv2.VideoWriter:
        if height is None or width is None:
            height, width = self._get_datapoints_shape()
        if video_name is None:
            video_name = f"{self.environment.behaviour}.mov"
        vid = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*codec), fps, (width, height))
        vid.release()
        return vid

    def _get_datapoints_shape(self) -> Tuple[int, int]:
        height, width, _ = self.datapoints[0].visible_spectrum.shape
        return height, width

    def _write_images(self, video: cv2.VideoWriter) -> None:
        for dp in self.datapoints:
            video.write(dp.visible_spectrum)
