from typing import Any

from typing_extensions import Protocol

from openslides_backend.services.database.commands import Command

# TODO: Use proper typing here.
EngineResponse = Any


class Engine(Protocol):
    """
    Engine defines the interface to the engine used by the datastore. This will
    be the HTTPEngine per default
    """

    def get(self, data: Command) -> EngineResponse:
        ...

    def get_many(self, data: Command) -> EngineResponse:
        ...

    def get_all(self, data: Command) -> EngineResponse:
        ...

    def filter(self, data: Command) -> EngineResponse:
        ...

    def exists(self, data: Command) -> EngineResponse:
        ...

    def count(self, data: Command) -> EngineResponse:
        ...

    def min(self, data: Command) -> EngineResponse:
        ...

    def max(self, data: Command) -> EngineResponse:
        ...
