import os

from dependency_injector import containers, providers

from datagen.api.client.session import ClientSession
from datagen.config import settings
from datagen.dev.logging import get_logger

logger = get_logger(__name__)

LONG_TIMEOUT_TIME = 36000  # 10 hours


def token_setup_instructions() -> str:
    if os.name == "nt":  # Windows
        return "set DG_AUTH_TOKEN=<your-auth-token>"
    else:  # Linux and MacOS
        return "export DG_AUTH_TOKEN=<your-auth-token>"


def get_token() -> str:
    token = os.environ.get("DG_AUTH_TOKEN")
    if not token:
        logger.warning(
            f"Authentication token is uninitialized. You can create a new token at "
            f"https://app.datagen.tech/token. \nAfter creating the token insert the following in your terminal:"
            f" {token_setup_instructions()}"
        )

    return token


class SessionContainer(containers.DeclarativeContainer):

    client_session = providers.Factory(
        ClientSession, base_url=settings["url"]["base"], headers={"authorization_token": get_token()}
    )

    long_timeout = providers.Object(LONG_TIMEOUT_TIME)
