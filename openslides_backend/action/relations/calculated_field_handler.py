from typing import Any

from ...models.fields import Field
from ...services.datastore.interface import DatastoreService
from .single_relation_handler import RelationUpdates


class CalculatedFieldHandler:
    datastore: DatastoreService

    def __init__(self, datastore: DatastoreService) -> None:
        self.datastore = datastore

    def process_field(
        self, field: Field, field_name: str, value: Any, action: str
    ) -> RelationUpdates:
        pass
