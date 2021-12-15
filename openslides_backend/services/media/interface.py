from typing import Protocol


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

    def duplicate_mediafile(self, source_id: int, target_id: int) -> None:
        """
        Throws a MediaServiceException, if there is a ConnectionError or
        any Error reported from MediaService-Request
        """
        ...
