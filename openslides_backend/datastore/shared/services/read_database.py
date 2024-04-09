from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, ContextManager, Protocol, TypedDict

from openslides_backend.datastore.shared.di import service_interface
from openslides_backend.datastore.shared.util import (
    DeletedModelsBehaviour,
    Filter,
    MappedFields,
)
from openslides_backend.shared.patterns import (
    Collection,
    Field,
    FullQualifiedId,
    Id,
    Position,
)
from openslides_backend.shared.typing import JSON, Model


class HistoryInformation(TypedDict):
    position: Position
    timestamp: int  # unixtime
    user_id: int
    information: JSON


class BaseFilterQueryFieldsParameters:
    pass


class MappedFieldsFilterQueryFieldsParameters(BaseFilterQueryFieldsParameters):
    mapped_fields: MappedFields

    def __init__(self, mapped_fields: list[Field]) -> None:
        self.mapped_fields = MappedFields()
        self.mapped_fields.unique_fields = mapped_fields
        self.mapped_fields.post_init()


@dataclass
class BaseAggregateFilterQueryFieldsParameters(BaseFilterQueryFieldsParameters):
    function: str


@dataclass
class CountFilterQueryFieldsParameters(BaseAggregateFilterQueryFieldsParameters):
    function: str = "count"


@dataclass
class AggregateFilterQueryFieldsParameters(BaseAggregateFilterQueryFieldsParameters):
    function: str
    field: str
    type: str


@service_interface
class ReadDatabase(Protocol):
    def get_context(self) -> ContextManager[None]:
        """
        Creates a new context to execute all actions inside
        """

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: MappedFields | None = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> Model:
        """
        Internally calls `get_many` to retrieve a single model. Raises a
        ModelDoesNotExist if the model does not exist.
        """

    def get_many(
        self,
        fqids: Iterable[FullQualifiedId],
        mapped_fields: MappedFields | None = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> dict[FullQualifiedId, Model]:
        """
        Returns all requested models in a lookup-able fashion mapped the
        fqid <-> model from the read-DB. If a fqid could not be found, the
        model is not included in the result.
        """

    def get_all(
        self,
        collection: Collection,
        mapped_fields: MappedFields | None = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> dict[Id, Model]:
        """
        Returns all models of the given collection. WARNING: May result in a huge
        amount of data. Use with caution!
        """

    def get_everything(
        self,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> dict[Collection, dict[Id, Model]]:
        """
        Returns all models of the given collection. WARNING: May result in a huge
        amount of data. Use with caution!
        """

    def filter(
        self, collection: Collection, filter: Filter, mapped_fields: list[Field]
    ) -> dict[Id, Model]:
        """
        Returns all models of the given collection that satisfy the filter criteria.
        May result in a huge amount of data when used with wide filters.
        """

    def aggregate(
        self,
        collection: Collection,
        filter: Filter,
        fields_params: BaseAggregateFilterQueryFieldsParameters,
    ) -> Any:
        """
        Aggregates the filtered models according to fields_params.
        """

    def build_model_ignore_deleted(
        self, fqid: FullQualifiedId, position: Position | None = None
    ) -> Model:
        """
        Calls `build_models_ignore_deleted` to build a single model.
        Raises ModelDoesNotExist if the model does not exist.
        """

    def build_models_ignore_deleted(
        self, fqids: list[FullQualifiedId], position: Position | None = None
    ) -> dict[FullQualifiedId, Model]:
        """
        Builds the given models, optionally only up to the given position.
        It does not append META_POSITION to the model.
        """

    def is_deleted(
        self, fqid: FullQualifiedId, position: Position | None = None
    ) -> bool:
        """
        Calls `get_deleted_status` to retrieve the deleted state of a single model.
        Raises ModelDoesNotExist if the model does not exist.
        """

    def get_deleted_status(
        self, fqids: list[FullQualifiedId], position: Position | None = None
    ) -> dict[FullQualifiedId, bool]:
        """
        Returns a map indicating if the models with the given fqids are deleted. If
        position is given, the result refers to the state at the position.
        """

    def get_history_information(
        self, fqids: list[FullQualifiedId]
    ) -> dict[FullQualifiedId, list[HistoryInformation]]:
        """
        Returns a list of position data for all fqids.
        """

    def is_empty(self) -> bool:
        """
        Returns true, if there are no positions in the database
        """

    def get_max_position(self) -> Position:
        """Returns the current (highest) position of the datastore."""

    def get_current_migration_index(self) -> int:
        """
        Returns the maximum migration index from all positions or -1 if there are
        no positions.
        """
