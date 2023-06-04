from abc import ABC, abstractmethod
from enum import Enum


class ImageFormat(Enum):
    PNG = "png"
    EXR = "exr"


class ImagingLibrary(ABC):
    def read(self, image_file_path: str, keep_alpha: bool, convert_to_uint8: bool):
        file_format = self._get_file_format(image_file_path)
        if file_format == ImageFormat.PNG.value:
            return self._read_png(image_file_path, keep_alpha, convert_to_uint8)
        elif file_format == ImageFormat.EXR.value:
            return self._read_exr(image_file_path)
        else:
            raise ValueError(f"Unsupported image format: {file_format}")

    @staticmethod
    def _get_file_format(image_file_path: str) -> str:
        return image_file_path.split(".")[-1]

    @abstractmethod
    def _read_png(self, image_file_path: str, keep_alpha: bool, convert_to_uint8: bool): ...

    @abstractmethod
    def _read_exr(self, image_file_path: str): ...
