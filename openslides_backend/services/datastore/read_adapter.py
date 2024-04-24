from collections.abc import Callable, Iterable
from typing import Any, ContextManager, TypedDict

from openslides_backend.datastore.reader.core import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetManyRequest,
    GetManyRequestPart,
    GetRequest,
    MinMaxRequest,
)
from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend.connection_handler import (
    ConnectionHandler,
)
from openslides_backend.datastore.shared.postgresql_backend.pg_connection_handler import (
    PgConnectionHandlerService,
    retry_on_db_failure,
)
from openslides_backend.datastore.shared.postgresql_backend.sql_query_helper import (
    SqlQueryHelper,
)
from openslides_backend.datastore.shared.util import (
    BadCodingError,
    InvalidFormat,
    ModelDoesNotExist,
)
from openslides_backend.shared.filters import And, Filter, FilterOperator, Not, Or
from openslides_backend.shared.patterns import Collection, Id

from ...shared.patterns import collection_and_id_from_fqid
from .interface import PartialModel


class IndexBasedQueryData(TypedDict):
    queries_by_index: dict[str, str]
    arguments_by_index: dict[str, list[Any]]
    fields_by_index: dict[str, tuple[str, ...]]


class ReadAdapter:
    connection: PgConnectionHandlerService
    query_helper: SqlQueryHelper

    def __init__(self) -> None:
        self.connection: PgConnectionHandlerService = injector.get(ConnectionHandler)
        self.query_helper = injector.get(SqlQueryHelper)
        self._load_view_names()

    def get_database_context(self) -> ContextManager:
        """Returns the context manager of the underlying database."""
        return self.connection.get_connection_context()

    @retry_on_db_failure
    def get(self, request: GetRequest, lock: bool = True) -> PartialModel:
        """Gets the specified model."""
        collection, id_ = collection_and_id_from_fqid(request.fqid)
        arguments: list[Any] = [id_]

        mapped_fields_str = self._build_select_from_mapped_fields(
            tuple(request.mapped_fields)
        )

        if view_name := self._get_view_name_from_collection(collection):
            query = f"""
                select {mapped_fields_str} from {view_name}
                where id = %s"""
            if lock:
                query += " for update"
            with self.connection.get_connection_context():
                result = self.connection.query(query, (arguments))
                if len(result) != 0:
                    row = result[0]
                    model = {}
                    for field in request.mapped_fields or row.keys():
                        if row.get(field) is not None:
                            model[field] = row[field]
                    return model
        raise ModelDoesNotExist(request.fqid)

    @retry_on_db_failure
    def get_many(
        self, request: GetManyRequest, lock: bool = True
    ) -> dict[Collection, dict[Id, PartialModel]]:
        """Gets multiple models."""
        request_data = self._get_get_many_request_data(request)

        query_data: IndexBasedQueryData = {
            "queries_by_index": {},
            "arguments_by_index": {},
            "fields_by_index": {},
        }
        collections: list[str] = []
        for collection, ids_by_fields in request_data.items():
            collections.append(collection)
            collection_query_data = self._collection_based_get_many_helper(
                collection, ids_by_fields, "#", lock
            )
            query_data["queries_by_index"].update(
                collection_query_data["queries_by_index"]
            )
            query_data["arguments_by_index"].update(
                collection_query_data["arguments_by_index"]
            )
            query_data["fields_by_index"].update(
                collection_query_data["fields_by_index"]
            )

        def collection_by_index(index: str) -> Collection:
            return index.split("#")[0]

        return self._call_multiple_queries(query_data, collection_by_index, collections)

    @retry_on_db_failure
    def get_all(
        self, request: GetAllRequest, lock: bool = True
    ) -> dict[Id, PartialModel]:
        """
        Returns all (non-deleted) models of one collection. May return a huge amount
        of data, so use with caution.
        """
        if query := self._calculate_get_all_query(request, lock):
            with self.connection.get_connection_context():
                result = self.connection.query(query, ())
                return self._build_models_from_single_query_result(
                    result, request.mapped_fields
                )
        return {}

    @retry_on_db_failure
    def get_everything(self) -> dict[Collection, dict[Id, PartialModel]]:
        """
        Returns all models In the form of the example data: Collections mapped to
        lists of models.
        """
        query_data: IndexBasedQueryData = {
            "queries_by_index": {},
            "arguments_by_index": {},
            "fields_by_index": {},
        }

        for collection in self._collections_with_tables.keys():
            if query := self._calculate_get_all_query(
                GetAllRequest(collection=collection), False
            ):
                query_data["queries_by_index"][collection] = query
        result = self._call_multiple_queries(query_data)
        return {key: value for key, value in result.items() if value}

    @retry_on_db_failure
    def filter(
        self, request: FilterRequest, lock: bool = True
    ) -> dict[Id, PartialModel]:
        """Returns all models that satisfy the filter condition."""
        mapped_fields_str = self._build_select_from_mapped_fields(
            tuple(request.mapped_fields)
        )
        arguments: list[str] = []
        filter_str = self._filter_helper(request.filter, arguments)
        final: dict[Id, PartialModel] = {}
        if view_name := self._get_view_name_from_collection(request.collection):
            query = f"""
                select {mapped_fields_str} from {view_name}
                where {filter_str}"""
            if lock:
                query += " for update"
            with self.connection.get_connection_context():
                result = self.connection.query(query, arguments)
                return self._build_models_from_single_query_result(
                    result, request.mapped_fields
                )
        return final

    def exists(self, request: AggregateRequest) -> bool:
        """Determines whether at least one model satisfies the filter conditions."""
        count = self.count(request)
        return count > 0

    @retry_on_db_failure
    def count(self, request: AggregateRequest) -> int:
        """Returns the amount of models that satisfy the filter conditions."""
        arguments: list[str] = []
        filter_str = self._filter_helper(request.filter, arguments)
        if view_name := self._get_view_name_from_collection(request.collection):
            query = f"""
                select count(*) from {view_name}
                where {filter_str}"""
            with self.connection.get_connection_context():
                result = self.connection.query(query, arguments)
                return result[0][0]
        return 0

    @retry_on_db_failure
    def min(self, request: MinMaxRequest) -> Any:
        """
        Returns the mininum value of the given field for all models that satisfy the
        given filter.
        """
        arguments: list[str] = []
        filter_str = self._filter_helper(request.filter, arguments)
        if view_name := self._get_view_name_from_collection(request.collection):
            query = f"""
                select min({request.field}::{request.type}) from {view_name}
                where {filter_str}"""
            with self.connection.get_connection_context():
                result = self.connection.query(query, arguments)
                return result[0][0]
        return None

    @retry_on_db_failure
    def max(self, request: MinMaxRequest) -> Any:
        """
        Returns the maximum value of the given field for all models that satisfy the
        given filter.
        """
        arguments: list[str] = []
        filter_str = self._filter_helper(request.filter, arguments)
        if view_name := self._get_view_name_from_collection(request.collection):
            query = f"""
                select max({request.field}::{request.type}) from {view_name}
                where {filter_str}"""
            with self.connection.get_connection_context():
                result = self.connection.query(query, arguments)
                return result[0][0]
        return None

    def _build_models_from_single_query_result(
        self,
        result: Any,
        fields: Iterable[str] | None = None,
        previous_models: dict[Id, PartialModel] | None = {},
    ) -> dict[Id, PartialModel]:
        models = previous_models or {}
        for row in result:
            id_: int = row["id"]

            model = {}
            for field in fields or row.keys():
                if row.get(field) is not None:
                    model[field] = row[field]
            if models.get(id_):
                models[id_].update(model)
            else:
                models[id_] = model
        return models

    def _build_select_from_mapped_fields(self, fields: tuple[str, ...]) -> str:
        if not len(fields):
            # at least one collection needs all fields, so we just select all and
            # calculate the mapped_fields later
            return "*"
        else:
            return ", ".join({*fields, "id"})

    def _calculate_get_all_query(
        self, request: GetAllRequest, lock: bool
    ) -> str | None:
        mapped_fields_str = self._build_select_from_mapped_fields(
            tuple(request.mapped_fields)
        )

        if view_name := self._get_view_name_from_collection(request.collection):
            query = f"""
                select {mapped_fields_str} from {view_name}"""
            if lock:
                query += " for update"
            return query
        return None

    def _call_multiple_queries(
        self,
        query_data: IndexBasedQueryData,
        collection_from_index: Callable[[str], str] | None = None,
        collections: list[Collection] = [],
    ) -> dict[Collection, dict[Id, PartialModel]]:
        models: dict[str, dict[Id, PartialModel]] = {
            collection: {} for collection in collections
        }
        if len(query_data["queries_by_index"]):
            with self.connection.get_connection_context():
                results = self.connection.query_multiple(
                    query_data["queries_by_index"], query_data["arguments_by_index"]
                )
                for index, result in results.items():
                    collection = (
                        collection_from_index(index) if collection_from_index else index
                    )
                    models[collection] = self._build_models_from_single_query_result(
                        result,
                        query_data["fields_by_index"].get(index),
                        models.get(collection),
                    )
        return models

    def _collection_based_get_many_helper(
        self,
        collection: str,
        ids_by_fields: dict[tuple[str, ...], list[int]],
        separator: str,
        lock: bool,
    ) -> IndexBasedQueryData:
        query_data: IndexBasedQueryData = {
            "queries_by_index": {},
            "arguments_by_index": {},
            "fields_by_index": {},
        }
        if any((len(ids) > 0) for ids in ids_by_fields.values()):
            index = 0

            for fields, ids in ids_by_fields.items():
                arguments: list[Any] = [tuple([0, *ids])]

                mapped_fields_str = self._build_select_from_mapped_fields(fields)

                if view_name := self._get_view_name_from_collection(collection):
                    key = collection + separator + str(index)
                    query = f"""
                        select {mapped_fields_str} from {view_name}
                        where id in %s"""
                    if lock:
                        query += " for update"
                    query_data["queries_by_index"][key] = query
                    query_data["arguments_by_index"][key] = arguments
                    query_data["fields_by_index"][key] = fields
                    index += 1
        return query_data

    def _filter_helper(
        self, filter_segment: Filter, arguments: list[str]
    ) -> str | None:
        if isinstance(filter_segment, FilterOperator):
            if filter_segment.value is None:
                if filter_segment.operator not in ("=", "!="):
                    raise InvalidFormat("You can only compare to None with = or !=")
                operator = (
                    filter_segment.operator[::-1]
                    .replace("=", "IS")
                    .replace("!", " NOT")
                )
                condition = f"{filter_segment.field} {operator} NULL"
            else:
                if filter_segment.operator == "~=":
                    condition = f"LOWER({filter_segment.field}) = LOWER(%s::text)"
                elif filter_segment.operator == "%=":
                    condition = f"{filter_segment.field} ILIKE %s::text"
                elif filter_segment.operator in ("=", "!="):
                    condition = (
                        f"{filter_segment.field} {filter_segment.operator} %s::text"
                    )
                else:
                    condition = (
                        f"{filter_segment.field}::numeric {filter_segment.operator} %s"
                    )
                arguments += [filter_segment.value]
            return condition
        elif isinstance(filter_segment, Not):
            filter_str = self._filter_helper(filter_segment.not_filter, arguments)
            return f"NOT ({filter_str})"
        elif isinstance(filter_segment, And):
            return " AND ".join(
                f"({self._filter_helper(part, arguments)})"
                for part in filter_segment.and_filter
            )
        elif isinstance(filter_segment, Or):
            return " OR ".join(
                f"({self._filter_helper(part, arguments)})"
                for part in filter_segment.or_filter
            )
        else:
            raise BadCodingError("Invalid filter type")

    def _get_get_many_request_data(
        self, request: GetManyRequest
    ) -> dict[str, dict[tuple[str, ...], list[int]]]:  #
        universal_fields: list[str] = request.mapped_fields or []
        request_data: dict[str, dict[tuple[str, ...], list[int]]] = {}
        for req in request.requests:
            if not isinstance(req, GetManyRequestPart):
                # TODO: This isn't used anywhere in the backend
                # Remove FqField request format from GetManyRequest type
                raise BadCodingError("Fqfield-based get_many request not supported")
            coll = req.collection
            fields: list[str] = (
                list({*req.mapped_fields, *universal_fields})
                if req.mapped_fields
                else []
            )
            fields.sort()
            ids: list[int] = req.ids
            t_fields = tuple(fields)
            if not request_data.get(coll):
                request_data[coll] = {t_fields: ids}
            elif not request_data[coll].get(t_fields):
                request_data[coll][t_fields] = ids
            else:
                request_data[coll][t_fields].extend(ids)
        return request_data

    def _get_view_name_from_collection(self, collection: str) -> str | None:
        if view_name := self._collections_with_views.get(collection):
            return view_name
        elif table_name := self._collections_with_tables.get(collection):
            return table_name
        return None

    def _load_view_names(self) -> None:
        """Gets names of all views."""
        query = """
            select table_name, table_type from information_schema.tables
            WHERE table_schema='public' and table_catalog='openslides'"""
        with self.connection.get_connection_context():
            result = self.connection.query(query, ())
            views: list[str] = [
                date["table_name"] for date in result if date["table_type"] == "VIEW"
            ]
            tables: list[str] = [
                date["table_name"]
                for date in result
                if date["table_name"].endswith("_t")
                and not date["table_name"].startswith("nm_")
                and not date["table_name"].startswith("gm_")
            ]
            self._collections_with_views = {view.strip("_"): view for view in views}
            self._collections_with_tables = {table[0:-2]: table for table in tables}
