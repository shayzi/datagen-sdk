from typing import Any, Optional

import aiohttp
from pydantic import BaseModel

DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1MB
DEFAULT_SESSION_TIMOUT_SEC = 300  # 5 min


class SessionsResponse(BaseModel):
    status_code: int
    payload: Any


class ClientSession:
    def __init__(
        self,
        base_url: Optional[str] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = DEFAULT_SESSION_TIMOUT_SEC,
    ):
        self.base_url = base_url
        self.headers = headers
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(base_url=self.base_url, headers=self.headers, timeout=self.timeout)
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        self.session = None
