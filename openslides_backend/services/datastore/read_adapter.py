from collections import defaultdict
from typing import Any, ContextManager

from datastore.reader.core import GetManyRequest, GetManyRequestPart
from datastore.shared.di import injector
from datastore.shared.postgresql_backend.connection_handler import ConnectionHandler
from datastore.shared.postgresql_backend.sql_query_helper import SqlQueryHelper
from datastore.shared.typing import Collection, Id

Model = dict[str, Any]


class ReadAdapter:
    connection: (
        ConnectionHandler  # TODO use PgConnectionHandlerService from datastore ?
    )
    query_helper: SqlQueryHelper

    def __init__(self) -> None:
        self.connection = injector.get(ConnectionHandler)
        self.query_helper = injector.get(SqlQueryHelper)

    def get_database_context(self) -> ContextManager[None]:
        """Returns the context manager of the underlying database."""
        return self.connection.get_connection_context()

    # def get(self, request: GetRequest) -> Model:
    #     """Gets the specified model."""
    #     return None

    def get_many(self, request: GetManyRequest) -> dict[Collection, dict[Id, Model]]:
        """Gets multiple models."""

        universal_fields: list[str] = request.mapped_fields or []
        request_data: dict[str, dict[tuple[str, ...], list[int]]] = {}
        for req in request.requests:
            if not isinstance(req, GetManyRequestPart):
                # TODO: Is this even used anywhere in the backend?
                raise Exception("Fqfield-based get_many request not supported")
            coll = req.collection
            fields: list[str] = (
                list({*req.mapped_fields, *universal_fields, "id"})
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

        final: dict[Collection, dict[Id, Model]] = defaultdict(dict)
        for collection, ids_by_fields in request_data.items():
            final[collection].update(
                self._collection_based_get_many_helper(collection, ids_by_fields)
            )
        return final

    def _collection_based_get_many_helper(
        self, collection: str, ids_by_fields: dict[tuple[str, ...], list[int]]
    ) -> dict[Id, Model]:
        if not any((len(ids) > 0) for ids in ids_by_fields.values()):
            return {}

        models: dict[Id, Model] = {}

        for fields, ids in ids_by_fields.items():
            arguments: list[Any] = [tuple([0, *ids])]

            mapped_fields_str = self._build_select_from_mapped_fields(fields)

            query = f"""
                select {mapped_fields_str} from {self._get_view_name_from_collection(collection)}
                where id in %s"""
            with self.connection.get_connection_context():
                result = self.connection.query(query, (arguments))
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
            return ", ".join(fields)

    def _get_view_name_from_collection(self, collection: str) -> str:
        if collection in ["group", "user"]:
            return "_" + collection
        return collection

    # def get_all(self, request: GetAllRequest) -> dict[Id, Model]:
    #     """
    #     Returns all (non-deleted) models of one collection. May return a huge amount
    #     of data, so use with caution.
    #     """
    #     return None

    # def get_everything(
    #     self, request: GetEverythingRequest
    # ) -> dict[Collection, dict[Id, Model]]:
    #     """
    #     Returns all models In the form of the example data: Collections mapped to
    #     lists of models.
    #     """
    #     return None

    # def filter(self, request: FilterRequest) -> FilterResult:
    #     """Returns all models that satisfy the filter condition."""
    #     return None

    # def exists(self, request: AggregateRequest) -> ExistsResult:
    #     """Determines whether at least one model satisfies the filter conditions."""
    #     return None

    # def count(self, request: AggregateRequest) -> CountResult:
    #     """Returns the amount of models that satisfy the filter conditions."""
    #     return None

    # def min(self, request: MinMaxRequest) -> MinResult:
    #     """
    #     Returns the mininum value of the given field for all models that satisfy the
    #     given filter.
    #     """
    #     return None

    # def max(self, request: MinMaxRequest) -> MaxResult:
    #     """
    #     Returns the maximum value of the given field for all models that satisfy the
    #     given filter.
    #     """
    #     return None

    # def history_information(
    #     self, request: HistoryInformationRequest
    # ) -> dict[Fqid, list[HistoryInformation]]:
    #     """
    #     Returns history information for multiple models.
    #     """
    #     return None
