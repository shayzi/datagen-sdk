import abc
from dataclasses import dataclass
from typing import Type, Optional


class ModalityFileNotFoundError(RuntimeError):
    ...


@dataclass
class Modality(abc.ABC):
    file_name: str


class ModalityDescriptor(abc.ABC):
    def __init__(self, fget=None, **kwargs):
        self._fget = fget

    def __get__(self, dp, *args):
        modality = self._fget(dp)
        modality_file_path = self._get_modality_file_path(dp, modality)
        return self._read(dp, modality, modality_file_path)

    @staticmethod
    def _get_modality_file_path(dp, modality: Modality) -> str:
        modality_file_path = None
        camera_modality_path = dp.camera_path.joinpath(modality.file_name)
        frame_modality_path = dp.frame_path.joinpath(modality.file_name)
        scene_modality_path = dp.scene_path.joinpath(modality.file_name)
        if camera_modality_path.exists():
            modality_file_path = camera_modality_path
        elif frame_modality_path.exists():
            modality_file_path = frame_modality_path
        elif scene_modality_path.exists():
            modality_file_path = scene_modality_path
        return str(modality_file_path) if modality_file_path is not None else None

    @abc.abstractmethod
    def _read(self, dp, modality: Modality, modality_file_path: str):
        ...


class ModalityPreProcess(abc.ABC):
    @abc.abstractmethod
    def __call__(self):
        ...


@dataclass
class TextualModality(Modality):
    factory_name: str
    pre_process: Optional[ModalityPreProcess] = None


class TextualModalityDescriptor(ModalityDescriptor):
    def _read(self, dp, modality: TextualModality, modality_file_path: str):
        if modality.pre_process is not None:
            modality.pre_process()
        if modality_file_path is None:
            ModalityFileNotFoundError(f"'{modality.file_name}' not found for datapoint {dp}")
        else:
            return dp.modalities_container.read_textual_modality(
                modality_file_path=modality_file_path, modality_factory_name=modality.factory_name
            )


@dataclass
class VisualModality(Modality):
    keep_alpha: bool = False
    convert_to_uint8: bool = False


class VisualModalityDescriptor(ModalityDescriptor):
    def _read(self, dp, modality: VisualModality, modality_file_path: str):
        if modality_file_path is None:
            return None
        else:
            return dp.modalities_container.read_visual_modality(
                modality_file_path=modality_file_path,
                keep_alpha=modality.keep_alpha,
                convert_to_uint8=modality.convert_to_uint8,
            )
