from collections import defaultdict
from collections.abc import Iterable
from typing import Any, ContextManager, Dict, List, Set, Tuple, cast

from datastore.reader.core.requests import GetManyRequest, GetManyRequestPart
from datastore.shared.di import injector
from datastore.shared.postgresql_backend.connection_handler import ConnectionHandler
from datastore.shared.postgresql_backend.sql_query_helper import SqlQueryHelper
from datastore.shared.typing import Collection, Fqid, Id, Model
from datastore.shared.util import MappedFields

from openslides_backend.shared.patterns import collection_and_id_from_fqid, collection_from_fqid, fqid_from_fqfield, field_from_fqfield, fqid_from_collection_and_id


class ReadAdapter:
    connection: ConnectionHandler  # TODO use PgConnectionHandlerService from datastore
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

    # TODO: I don't see a point in constantly calculating and then splitting fqids,
    # this should all just use separate collection and id variables
    def get_many(self, request: GetManyRequest) -> dict[Collection, dict[Id, Model]]:
        """Gets multiple models."""
        mapped_fields = MappedFields()
        unique_fields_set = set()
        collections_set = set()
        if isinstance(request.requests[0], GetManyRequestPart):
            unique_fields_set.update(request.mapped_fields)
            requests = cast(List[GetManyRequestPart], request.requests)
            for part in requests:
                unique_fields_set.update(part.mapped_fields)
                collections_set.add(part.collection)
                for id in part.ids:
                    fqid = fqid_from_collection_and_id(part.collection, str(id))
                    mapped_fields.per_fqid[fqid].extend(
                        part.mapped_fields + request.mapped_fields
                    )
        else:
            fqfield_requests = cast(List[str], request.requests)
            for fqfield in fqfield_requests:
                fqid = fqid_from_fqfield(fqfield)
                collections_set.add(collection_from_fqid(fqid))
                field = field_from_fqfield(fqfield)
                mapped_fields.per_fqid[fqid].append(field)
                unique_fields_set.add(field)
        mapped_fields.unique_fields = list(unique_fields_set)
        mapped_fields.collections = list(collections_set)
        mapped_fields.post_init()

        ids_per_collection: Dict[str, List[int]] = { collection:[] for collection in mapped_fields.collections }
        for fqid in mapped_fields.per_fqid:
            col, id_ = collection_and_id_from_fqid(fqid)
            ids_per_collection[col].append(id_)

        # Use multiple calls of _collection_based_get_many_helper instead, put results in same format
        result = self._get_many_helper(
            mapped_fields.fqids,
            mapped_fields,
        )

        # change mapping fqid->model to collection->id->model
        final: dict[Collection, dict[Id, Model]] = defaultdict(dict)
        for fqid, model in result.items():
            collection, id = collection_and_id_from_fqid(fqid)
            final[collection][id] = model

        # add back empty collections
        for collection in mapped_fields.collections:
            if not final[collection]:
                final[collection] = {}
        return final

    def _collection_based_get_many_helper(
        self,
        collection: str,
        ids: List[int],
        mapped_fields: MappedFields | None = None,
    ) -> dict[Fqid, Model]:
        #TODO: Finish this and use it instead of _get_many_helper
        # all this can probably be refactored too
        if not ids:
            return {}
        if mapped_fields is None:
            mapped_fields = MappedFields()

        per_payload: List[Tuple[Set[str], List[int]]] = []
        for id_ in ids:
            fields: Set[str] = set(mapped_fields.per_fqid[fqid_from_collection_and_id(collection, id_)])
            for index in range(len(per_payload) + 1):
                if index == len(per_payload):
                    per_payload.append((fields, [id_]))
                elif not per_payload[index][0].symmetric_difference(fields):
                    per_payload[index][1].append(id_)
                    break

        models: dict[str, Model] = {}

        for date in per_payload:
            arguments: list[Any] = [tuple(date[1])]

            needs_whole_model = False # TODO: Somehow fill meaningfully based on request data
            mapped_fields_str = self._build_select_from_mapped_fields(date[0], needs_whole_model)

            query = f"""
                select {mapped_fields_str} from {self._get_view_name_from_collection(collection)}
                where id in %s"""
            with self.connection.get_connection_context():
                result = self.connection.query(
                    query, arguments
                )

                #TODO: Build the models for the returned rows, put them into 'models' dict in a fqid:Model format
        return models

    def _build_select_from_mapped_fields(
        self, fields: Set[str], needs_whole_model: bool = False
    ) -> str:
        if needs_whole_model:
            # at least one collection needs all fields, so we just select all and
            # calculate the mapped_fields later
            return "*"
        else:
            fields.add("id")
            return ", ".join(fields)

    def _get_many_helper(
        self,
        fqids: Iterable[Fqid],
        mapped_fields: MappedFields | None = None,
    ) -> dict[Fqid, Model]:
        if not fqids:
            return {}
        if mapped_fields is None:
            mapped_fields = MappedFields()

        arguments: list[Any] = [tuple(fqids)]

        (
            mapped_fields_str,
            mapped_field_args,
        ) = self.query_helper.build_select_from_mapped_fields(mapped_fields)

        # TODO: This is DEFINATELY the wrong query:
        # - We need to select from the correct table/view
        # - We need to select based on id
        # Something like
        # 'select id, {mapped_fields_str} from {view_name} where id in %s'
        # Where:
        # - view_name is the collection name (except for the user and group collection where a '_' should be appended)
        # - the arguments are now the ids of the models, not the fqids
        query = f"""
            select fqid, {mapped_fields_str} from models
            where fqid in %s"""
        with self.connection.get_connection_context():
            result = self.connection.query(
                query, mapped_field_args + arguments, mapped_fields.unique_fields
            )

            models = self._build_models_from_result(result, mapped_fields)
        return models

    def _get_view_name_from_collection(self, collection: str) -> str:
        if collection in ["group", "user"]:
            return "_" + collection
        return collection

    def _build_models_from_result(
        self, result: Any, mapped_fields: MappedFields
    ) -> dict[str, Model]:
        result_map = {}
        for row in result:
            fqid = row["fqid"]

            if mapped_fields.needs_whole_model:
                # at least one collection needs all fields, so we need to select data
                row = row["data"]

            if fqid in mapped_fields.per_fqid and len(mapped_fields.per_fqid[fqid]) > 0:
                model = {}
                for field in mapped_fields.per_fqid[fqid]:
                    if row.get(field) is not None:
                        model[field] = row[field]
            else:
                model = row
            result_map[fqid] = model

        return result_map

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
