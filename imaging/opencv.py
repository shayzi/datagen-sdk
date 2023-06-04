import os
import numpy as np

from datagen.imaging.base import ImagingLibrary

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

import cv2


class OpenCVImagingLibrary(ImagingLibrary):
    def _read_png(self, image_file_path: str, keep_alpha: bool, convert_to_uint8: bool) -> np.ndarray:
        img = cv2.imread(image_file_path, cv2.IMREAD_UNCHANGED)
        if keep_alpha:
            img[..., :3] = cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2RGB)
        else:
            img = cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2RGB)
        if convert_to_uint8:
            img = self._convert_to_uint8(img)
        return img

    @staticmethod
    def _convert_to_uint8(img: np.ndarray) -> np.ndarray:
        if img.dtype == np.uint16:
            img = ((img / (2 ** 16 - 1)) * 255).astype(np.uint8)
        elif img.dtype == np.uint8:
            return img
        else:
            raise ValueError("Cannot convert image to uint8 format")
        return img

    def _read_exr(self, image_file_path: str) -> np.ndarray:
        img = cv2.imread(image_file_path, cv2.IMREAD_UNCHANGED)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
