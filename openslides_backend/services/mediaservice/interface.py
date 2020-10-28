from typing import Dict, Optional

from typing_extensions import Protocol


class MediaserviceInterface(Protocol):
    """
    Mediaservice defines the interface to the mediaservice.
    """

    def upload(self, file: str, id: int, mimetype: str,) -> Optional[Dict[str, str]]:
        ...
