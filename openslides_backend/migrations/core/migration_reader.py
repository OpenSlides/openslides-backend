from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Protocol

from openslides_backend.datastore.reader.core import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetManyRequest,
    GetRequest,
    MinMaxRequest,
    Reader,
)
from openslides_backend.datastore.reader.core.requests import GetManyRequestPart
from openslides_backend.datastore.shared.di import service_as_factory, service_interface
from openslides_backend.datastore.shared.postgresql_backend import filter_models
from openslides_backend.datastore.shared.services.read_database import ReadDatabase
from openslides_backend.datastore.shared.util import ModelDoesNotExist
from openslides_backend.datastore.shared.util.filter import Filter
from openslides_backend.shared.patterns import (
    Collection,
    Field,
    FullQualifiedId,
    Id,
    collection_from_fqid,
    fqid_from_collection_and_id,
)
from openslides_backend.shared.typing import Model


@service_interface
class MigrationReader(Protocol):
    """
    Adaption of the Reader protocol for ease of use in migrations. Provides access to all current
    models which are not deleted.
    """

    def get(self, fqid: FullQualifiedId, mapped_fields: list[Field] = []) -> Model: ...

    def get_many(
        self, requests: list[GetManyRequestPart]
    ) -> dict[Collection, dict[Id, Model]]: ...

    def get_all(
        self, collection: Collection, mapped_fields: list[Field] = []
    ) -> dict[Id, Model]: ...

    def filter(
        self, collection: Collection, filter: Filter, mapped_fields: list[Field] = []
    ) -> dict[Id, Model]: ...

    def exists(self, collection: Collection, filter: Filter) -> bool: ...

    def count(self, collection: Collection, filter: Filter) -> int: ...

    def min(
        self, collection: Collection, filter: Filter, field: Field
    ) -> int | None: ...

    def max(
        self, collection: Collection, filter: Filter, field: Field
    ) -> int | None: ...

    def is_alive(self, fqid: FullQualifiedId) -> bool:
        """Returns true iff the model exists and is not deleted."""

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        """Returns true iff the model exists and is deleted."""

    def model_exists(self, fqid: FullQualifiedId) -> bool:
        """Returns true iff the model exists, regardless of deletion status."""


@service_as_factory
class MigrationReaderImplementation(MigrationReader):
    reader: Reader
    read_database: ReadDatabase

    def get(self, fqid: FullQualifiedId, mapped_fields: list[Field] = []) -> Model:
        return self.reader.get(GetRequest(fqid, mapped_fields))

    def get_many(
        self, requests: list[GetManyRequestPart]
    ) -> dict[Collection, dict[Id, Model]]:
        return self.reader.get_many(GetManyRequest(requests))

    def get_all(
        self, collection: Collection, mapped_fields: list[Field] = []
    ) -> dict[Id, Model]:
        return self.reader.get_all(GetAllRequest(collection, mapped_fields))

    def filter(
        self, collection: Collection, filter: Filter, mapped_fields: list[Field] = []
    ) -> dict[Id, Model]:
        result = self.reader.filter(FilterRequest(collection, filter, mapped_fields))
        return result["data"]

    def exists(self, collection: Collection, filter: Filter) -> bool:
        result = self.reader.exists(AggregateRequest(collection, filter))
        return result["exists"]

    def count(self, collection: Collection, filter: Filter) -> int:
        result = self.reader.count(AggregateRequest(collection, filter))
        return result["count"]

    def min(self, collection: Collection, filter: Filter, field: Field) -> int | None:
        result = self.reader.min(MinMaxRequest(collection, filter, field))
        return result["min"]

    def max(self, collection: Collection, filter: Filter, field: Field) -> int | None:
        result = self.reader.max(MinMaxRequest(collection, filter, field))
        return result["max"]

    def is_alive(self, fqid: FullQualifiedId) -> bool:
        status = self.read_database.get_deleted_status([fqid])
        return status.get(fqid) is False

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        status = self.read_database.get_deleted_status([fqid])
        return status.get(fqid) is True

    def model_exists(self, fqid: FullQualifiedId) -> bool:
        status = self.read_database.get_deleted_status([fqid])
        return fqid in status


@service_as_factory
class MigrationReaderImplementationMemory(MigrationReader):
    """
    In-memory implementation of the read database. All `mapped_fields` are ignored, all fields are
    always returned.
    """

    models: dict[FullQualifiedId, Model]

    def get(self, fqid: FullQualifiedId, mapped_fields: list[Field] = []) -> Model:
        if fqid not in self.models:
            raise ModelDoesNotExist(fqid)
        return self.models[fqid]

    def get_many(
        self, requests: list[GetManyRequestPart]
    ) -> dict[Collection, dict[Id, Model]]:
        result: dict[Collection, dict[Id, Model]] = defaultdict(dict)
        for request in requests:
            for id in request.ids:
                fqid = fqid_from_collection_and_id(request.collection, id)
                if fqid in self.models:
                    result[request.collection][id] = self.models[fqid]
        return result

    def get_all(
        self, collection: Collection, mapped_fields: list[Field] = []
    ) -> dict[Id, Model]:
        return {
            model["id"]: model
            for fqid, model in self.models.items()
            if collection_from_fqid(fqid) == collection
        }

    def filter(
        self, collection: Collection, filter: Filter, mapped_fields: list[Field] = []
    ) -> dict[Id, Model]:
        return filter_models(self.models, collection, filter)

    def exists(self, collection: Collection, filter: Filter) -> bool:
        return self.count(collection, filter) > 0

    def count(self, collection: Collection, filter: Filter) -> int:
        return len(self.filter(collection, filter))

    def min(self, collection: Collection, filter: Filter, field: Field) -> int | None:
        return self.minmax(collection, filter, field, min)

    def max(self, collection: Collection, filter: Filter, field: Field) -> int | None:
        return self.minmax(collection, filter, field, max)

    def minmax(
        self,
        collection: Collection,
        filter: Filter,
        field: Field,
        func: Callable[[Iterable[int]], int],
    ) -> int | None:
        values = [
            model[field]
            for model in self.filter(collection, filter).values()
            if field in model
        ]
        if values:
            return func(values)
        return None

    def is_alive(self, fqid: FullQualifiedId) -> bool:
        # the in-memory implementation does not support deletion
        return self.model_exists(fqid)

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        # the in-memory implementation does not support deletion
        return False

    def model_exists(self, fqid: FullQualifiedId) -> bool:
        return fqid in self.models
