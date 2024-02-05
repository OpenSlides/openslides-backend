from typing import Any

import requests

from ...shared.exceptions import MediaServiceException
from ...shared.interfaces.logging import LoggingModule
from .interface import MediaService


class MediaServiceAdapter(MediaService):
    """
    Adapter to connect to media service.
    """

    def __init__(self, media_url: str, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.media_url = media_url + "/"

    def _upload(self, file: str, id: int, mimetype: str, subpath: str) -> None:
        url = self.media_url + subpath + "/"
        payload = {"file": file, "id": id, "mimetype": mimetype}
        self.logger.debug(f"Starting upload of mediafile/{id} (mimetype: {mimetype})")
        self._handle_upload(url, payload, description="Upload of file: ")
        self.logger.debug("File successfully uploaded to the media service")

    def upload_mediafile(self, file: str, id: int, mimetype: str) -> None:
        subpath = "upload_mediafile"
        self._upload(file, id, mimetype, subpath)

    def upload_resource(self, file: str, id: int, mimetype: str) -> None:
        subpath = "upload_resource"
        self._upload(file, id, mimetype, subpath)

    def duplicate_mediafile(self, source_id: int, target_id: int) -> None:
        url = self.media_url + "duplicate_mediafile/"
        payload = {"source_id": source_id, "target_id": target_id}
        self._handle_upload(url, payload, description="Duplicate of mediafile: ")
        self.logger.debug("File successfully duplicated on the media service")

    def _handle_upload(
        self, url: str, payload: dict[str, Any], description: str
    ) -> None:
        try:
            response = requests.post(url, json=payload)
        except requests.exceptions.ConnectionError as e:
            msg = f"Connect to mediaservice failed. {e}"
            self.logger.debug(description + msg)
            raise MediaServiceException(msg)

        if response.status_code != 200:
            msg = f"Mediaservice Error: {str(response.content)}"
            self.logger.debug(description + msg)
            raise MediaServiceException(msg)
