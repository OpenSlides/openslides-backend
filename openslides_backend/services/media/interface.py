from typing import Union

from typing_extensions import Protocol


class MediaService(Protocol):
    """
    Mediaservice defines the interface to the mediaservice.
    """

    def upload_mediafile(
        self,
        file: str,
        id: int,
        mimetype: str,
    ) -> Union[str, None]:
        ...

    def upload_resource(self, file: str, id: int, mimetype: str) -> Union[str, None]:
        ...
