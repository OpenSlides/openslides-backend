from typing import Any, ContextManager, Protocol, TypedDict

from openslides_backend.datastore.shared.di import service_interface
from openslides_backend.datastore.shared.services import HistoryInformation
from openslides_backend.datastore.shared.typing import Collection, Fqid, Id, Model

from .requests import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetEverythingRequest,
    GetManyRequest,
    GetRequest,
    HistoryInformationRequest,
    MinMaxRequest,
)


class FilterResult(TypedDict):
    data: dict[Id, Model]
    position: int


class ExistsResult(TypedDict):
    exists: bool
    position: int


class CountResult(TypedDict):
    count: int
    position: int


class MinResult(TypedDict):
    min: Any
    position: int


class MaxResult(TypedDict):
    max: Any
    position: int


@service_interface
class Reader(Protocol):
    """An abstract class for the reader. For more details, see the specs."""

    def get_database_context(self) -> ContextManager[None]:
        """Returns the context manager of the underlying database."""

    def get(self, request: GetRequest) -> Model:
        """Gets the specified model."""

    def get_many(self, request: GetManyRequest) -> dict[Collection, dict[Id, Model]]:
        """Gets multiple models."""

    def get_all(self, request: GetAllRequest) -> dict[Id, Model]:
        """
        Returns all (non-deleted) models of one collection. May return a huge amount
        of data, so use with caution.
        """

    def get_everything(
        self, request: GetEverythingRequest
    ) -> dict[Collection, dict[Id, Model]]:
        """
        Returns all models In the form of the example data: Collections mapped to
        lists of models.
        """

    def filter(self, request: FilterRequest) -> FilterResult:
        """Returns all models that satisfy the filter condition."""

    def exists(self, request: AggregateRequest) -> ExistsResult:
        """Determines whether at least one model satisfies the filter conditions."""

    def count(self, request: AggregateRequest) -> CountResult:
        """Returns the amount of models that satisfy the filter conditions."""

    def min(self, request: MinMaxRequest) -> MinResult:
        """
        Returns the mininum value of the given field for all models that satisfy the
        given filter.
        """

    def max(self, request: MinMaxRequest) -> MaxResult:
        """
        Returns the maximum value of the given field for all models that satisfy the
        given filter.
        """

    def history_information(
        self, request: HistoryInformationRequest
    ) -> dict[Fqid, list[HistoryInformation]]:
        """
        Returns history information for multiple models.
        """
