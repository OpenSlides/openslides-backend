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
        self.logger.debug("Starting upload of file")
        try:
            response = requests.post(url, json=payload)
        except requests.exceptions.ConnectionError:
            msg = "Connect to mediaservice failed."
            self.logger.debug("Upload of file: " + msg)
            raise MediaServiceException(msg)

        if response.status_code != 200:
            msg = f"Mediaservice Error: {str(response.content)}"
            self.logger.debug("Upload of file: " + msg)
            raise MediaServiceException(msg)
        self.logger.debug("File successfully uploaded to the media service")

    def upload_mediafile(self, file: str, id: int, mimetype: str) -> None:
        subpath = "upload_mediafile"
        self._upload(file, id, mimetype, subpath)

    def upload_resource(self, file: str, id: int, mimetype: str) -> None:
        subpath = "upload_resource"
        self._upload(file, id, mimetype, subpath)

    def download_mediafile(self, id: int) -> bytes:
        # TODO The media service path differ between /internal/media/
        # and /system/media/, this is a hotfix. We need two config paths here.
        url = self.media_url.replace("internal", "system") + "get" + "/" + str(id)
        try:
            response = requests.get(url)
        except requests.exceptions.ConnectionError:
            msg = "Connect to mediaservice failed."
            self.logger.debug("Download of file: " + msg)
            raise MediaServiceException(msg)

        if response.status_code != 200:
            msg = f"Mediaservice Error: {str(response.content)}"
            self.logger.debug("Download of file: " + msg)
            raise MediaServiceException(msg)
        self.logger.debug("File successfully downloaded of the media service")
        return response.content
