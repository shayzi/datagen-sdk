import enum
import sys
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, validator


class DataResponse(BaseModel):
    generation_name: str = Field(
        description="Generation name provided by Datagen platform. In a format " "of 'Field - <date>."
    )
    generation_id: str = Field(
        description="Unique UUID provided by Datagen platform. With the generation id you'll "
        "be able to query generation_status, stop generation and get download urls"
    )
    dgu_hour: float = Field(description="The DGU Hour cost of the requested generation.")
    renders: int = Field(description="The number of datapoints received in this request.")
    scenes: int = Field(description="The number of scenes received in this request.")


class EGenerationStatus(enum.Enum):
    START = "START"
    IN_PROGRESS = "IN-PROGRESS"
    PENDING = "IN-PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DownloadURL(BaseModel):
    url: str
    filename: str
    dataset_name: Optional[str] = None

    @classmethod
    def parse_url(cls, url: str, dataset_name: Optional[str] = None) -> "DownloadURL":
        path = urlsplit(url).path.split("/")
        filename = path[-1]
        return cls(url=url, filename=filename, dataset_name=dataset_name)


class DownloadRequest(BaseModel):
    urls: List[DownloadURL]
    path: str
    dataset_name: str

    @validator("path")
    def validate_url_host(cls, path: str) -> str:
        if not Path(path).exists():
            Path(path).mkdir(parents=True)
        return path

    def batch(self) -> list:
        batches = []
        for url in self.urls:
            url.filename = str(Path(self.path, url.filename))
            url.dataset_name = self.dataset_name
            batches.append(url)

        return batches


class DataResponseStatus(BaseModel):
    status: EGenerationStatus = Field(description="Current status of the generation process.")
    percentage: Optional[int] = Field(description="The percentage of data generation completion.", ge=0, le=100)
    estimation_time_ms: Optional[Union[int, str]] = Field(
        description="Estimated time in ms to data generation completion.", ge=0
    )

    @validator("estimation_time_ms")
    def validate_name(cls, val: Union[int, str]):
        if not val:
            return sys.maxsize
        return val


class ErrorDetail(BaseModel):
    loc: list
    msg: str
    type: str


class ValidationError(BaseModel):
    error_name: str
    description: str
    text: str
    details: List[ErrorDetail]


class ErrorResponse(BaseModel):
    error: Union[str, ValidationError]

    def __str__(self):
        if isinstance(self.error, str):
            return f"Error: {self.error}"
        else:
            return (
                f"Error: {self.error.error_name}\n"
                f"Description: {self.error.description}\n"
                f"Text: {self.error.text}\n"
                f"Details: {self.error.details} "
            )


def parse_error(error: Union[str, dict]) -> dict:
    if isinstance(error, dict) and "error" in error.keys():
        return error
    elif isinstance(error, str):
        return {"error": error}

    raise ValueError("Couldn't parse an error due to an invalid type")
