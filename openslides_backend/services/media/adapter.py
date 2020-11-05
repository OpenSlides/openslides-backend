from typing import Dict, Optional

import requests

from ...shared.exceptions import ServiceException
from ...shared.interfaces.logging import LoggingModule
from .interface import MediaService


class MediaServiceAdapter(MediaService):
    """
    Adapter to connect to media service.
    """

    def __init__(self, media_url: str, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.media_url = media_url

    def upload(self, file: str, id: int, mimetype: str) -> Optional[Dict[str, str]]:
        payload = {"file": file, "id": id, "mimetype": mimetype}
        self.logger.debug(f"Starting upload of file '{file}'")
        try:
            response = requests.post(self.media_url, json=payload)
        except requests.exceptions.ConnectionError:
            raise ServiceException("Connect to mediaservice failed.")
        if response.status_code != 200:
            raise ServiceException(f"Mediaservice Error: {str(response.json())}")
        self.logger.debug(f"File '{file}' successfully uploaded to the media service")
        return response.json()
