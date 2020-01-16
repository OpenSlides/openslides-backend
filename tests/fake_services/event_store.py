from typing import Any, Iterable

from openslides_backend.shared.interfaces import Event


class EventStoreTestAdapter:
    """
    Test adapter for event store.

    See openslides_backend.adapters.protocols.EventStoreProvider for
    implementation.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...

    def send(self, events: Iterable[Event]) -> None:
        pass
