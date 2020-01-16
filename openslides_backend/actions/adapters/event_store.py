from typing import Iterable

from ..general.exception import BackendBaseException
from .protocols import Event


class EventStoreException(BackendBaseException):
    pass


class EventStoreHTTPAdapter:
    """
    Adapter to connect to event store.
    """

    def __init__(self, event_store_url: str) -> None:
        self.url = event_store_url
        # self.headers = {"Content-Type": "application/json"}

    def send(self, events: Iterable[Event]) -> None:
        raise
