from abc import ABC, abstractmethod
from typing import Any, TypedDict

from ...models.fields import Field
# from ...services.database.extended_database import ExtendedDatabase
from ...services.database.interface import Database
from .typing import RelationUpdates


class CalculatedFieldHandlerCall(TypedDict):
    field: Field
    field_name: str
    instance: dict[str, Any]
    action: str


class CalculatedFieldHandler(ABC):
    # TODO we still use a type ignore. Maybe cast or maybe there is a solution with Database? Problem is the direct access of _changed_models
    datastore: Database

    def __init__(self, datastore: Database) -> None:
        self.datastore = datastore  # type: ignore

    @abstractmethod
    def process_field(
        self, field: Field, field_name: str, instance: dict[str, Any], action: str
    ) -> RelationUpdates: ...
