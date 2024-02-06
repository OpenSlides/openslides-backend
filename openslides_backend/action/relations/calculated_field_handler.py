from abc import ABC, abstractmethod
from typing import Any, TypedDict

from ...models.fields import Field
from ...services.datastore.interface import DatastoreService
from .typing import RelationUpdates


class CalculatedFieldHandlerCall(TypedDict):
    field: Field
    field_name: str
    instance: dict[str, Any]
    action: str


class CalculatedFieldHandler(ABC):
    datastore: DatastoreService

    def __init__(self, datastore: DatastoreService) -> None:
        self.datastore = datastore

    @abstractmethod
    def process_field(
        self, field: Field, field_name: str, instance: dict[str, Any], action: str
    ) -> RelationUpdates: ...
