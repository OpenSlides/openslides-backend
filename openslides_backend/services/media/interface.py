from typing_extensions import Protocol


class MediaService(Protocol):
    """
    Mediaservice defines the interface to the mediaservice.
    """

    def upload(
        self,
        file: str,
        id: int,
        mimetype: str,
    ) -> None:
        ...
