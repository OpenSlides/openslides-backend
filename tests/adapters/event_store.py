from typing import Any, Iterable

from openslides_backend.utils.types import Event


class EventStoreTestAdapter:
    """
    Test adapter for event store.

    See openslides_backend.services.providers.EventStoreProvider for
    implementation.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...

    def send(self, events: Iterable[Event]) -> None:
        pass
