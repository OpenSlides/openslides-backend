from typing import Any, Dict, TypedDict

from ...models.fields import Field
from ...services.datastore.interface import DatastoreService
from .typing import RelationUpdates


class CalculatedFieldHandlerCall(TypedDict):
    field: Field
    field_name: str
    instance: Dict[str, Any]
    action: str


class CalculatedFieldHandler:
    datastore: DatastoreService

    def __init__(self, datastore: DatastoreService) -> None:
        self.datastore = datastore

    def process_field(
        self, field: Field, field_name: str, instance: Dict[str, Any], action: str
    ) -> RelationUpdates:
        pass
