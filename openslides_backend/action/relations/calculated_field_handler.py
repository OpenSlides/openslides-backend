from abc import ABC, abstractmethod
from typing import Any, TypedDict

from ...models.fields import Field
from ...services.database.interface import Database
from .typing import RelationUpdates


class CalculatedFieldHandlerCall(TypedDict):
    field: Field
    field_name: str
    instance: dict[str, Any]
    action: str


class CalculatedFieldHandler(ABC):
    datastore: Database

    def __init__(self, datastore: Database) -> None:
        self.datastore = datastore

    @abstractmethod
    def process_field(
        self, field: Field, field_name: str, instance: dict[str, Any], action: str
    ) -> RelationUpdates: ...
