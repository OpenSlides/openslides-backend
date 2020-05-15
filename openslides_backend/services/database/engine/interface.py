from typing import Any, Dict, List

from typing_extensions import Protocol

from openslides_backend.services.database.commands import Command

EngineResponse = Dict[str, Any]


class Engine(Protocol):
    """Datastore defines the interface to the engine used by the datastore
       This will be the HTTPEngine per default
    """

    def get(self, data: Command) -> EngineResponse:
        ...

    def getMany(self, data: Command) -> EngineResponse:
        ...

    def getManyByFQIDs(self, data: Command) -> EngineResponse:
        ...

    def getAll(self, data: Command) -> List[EngineResponse]:
        ...

    def filter(self, data: Command) -> List[EngineResponse]:
        ...

    def exists(self, data: Command) -> EngineResponse:
        ...

    def count(self, data: Command) -> EngineResponse:
        ...

    def min(self, data: Command) -> EngineResponse:
        ...

    def max(self, data: Command) -> EngineResponse:
        ...

    def getId(self, data: Command) -> EngineResponse:
        ...
