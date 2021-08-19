from typing_extensions import Protocol


class MediaService(Protocol):
    """
    Mediaservice defines the interface to the mediaservice.
    """

    def upload_mediafile(self, file: str, id: int, mimetype: str) -> None:
        """
        Throws a MediaServiceException, if there is a ConnectionError or
        any Error reported from MediaService-Request
        """
        ...

    def upload_resource(self, file: str, id: int, mimetype: str) -> None:
        """
        Throws a MediaServiceException, if there is a ConnectionError or
        any Error reported from MediaService-Request
        """
        ...

    def download_mediafile(self, id: int) -> bytes:
        """
        Throws a MediaServiceException, if there is a ConnectionError or
        any Error reported from MediaService-Request
        """
        ...
