from collections.abc import Iterable
from typing import Any, ContextManager

from mapped_fields import MappedFields
from query_helper import SqlQueryHelper

from openslides_backend.shared.filters import Filter
from openslides_backend.shared.patterns import (
    Collection,
    Field,
    FullQualifiedId,
    Id,
    Position,
)
from openslides_backend.shared.typing import HistoryInformation, Model

from .db_connection_handling import *


class DatabaseReader:

    query_helper = SqlQueryHelper

    def __init__(self, db_connection: psycopg.Connection):
        self.connection = db_connection

    def get_context(self) -> ContextManager[None]:
        return self.connection

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: MappedFields | None = None,
    ) -> Model:
        return self.get_many([fqid], mapped_fields)

    def get_many(
        self,
        fqids: Iterable[FullQualifiedId],
        mapped_fields: MappedFields | None = None,
    ) -> dict[FullQualifiedId, Model]:
        if not fqids:
            return {}
        if mapped_fields is None:
            mapped_fields = MappedFields()

        # TODO Implement me!
        #        arguments: list[Any] = [list(fqids)]
        #
        #        (
        #            mapped_fields_str,
        #            mapped_field_args,
        #        ) = self.query_helper.build_select_from_mapped_fields(mapped_fields)
        #
        #        query = f"""
        #            select fqid, {mapped_fields_str} from models
        #            where fqid = any(%s) {del_cond}"""
        #        result = self.connection.query(
        #            query, mapped_field_args + arguments, mapped_fields.unique_fields
        #        )
        #
        #        models = self.build_models_from_result(result, mapped_fields)
        return {}

    def get_all(
        self,
        collection: Collection,
        mapped_fields: MappedFields | None = None,
    ) -> dict[Id, Model]:
        #        if mapped_fields is None:
        #            mapped_fields = MappedFields()
        #        (
        #            mapped_fields_str,
        #            mapped_field_args,
        #        ) = self.query_helper.build_select_from_mapped_fields(mapped_fields)
        #        query = f"""
        #            select fqid as __fqid__, {mapped_fields_str} from models
        #            where fqid like %s"""
        #        models = self.fetch_models(
        #            query,
        #            mapped_field_args + [fqid_from_collection_and_id(collection, "%")],
        #            mapped_fields.unique_fields,
        #            mapped_fields.unique_fields,
        #        )
        return {}

    def get_everything(
        self,
    ) -> dict[Collection, dict[Id, Model]]:
        #        query = f"""
        #            select fqid as __fqid__, data from models
        #            {"where "}"""
        #        result = self.connection.query(query, [], [])
        #
        #        data: dict[Collection, dict[Id, Model]] = defaultdict(dict)
        #        for row in result:
        #            collection, id = collection_and_id_from_fqid(row["__fqid__"])
        #            model = row["data"]
        #            model["id"] = id
        #            data[collection][id] = model
        #
        return {}

    def filter(
        self, collection: Collection, filter: Filter, mapped_fields: list[Field]
    ) -> dict[Id, Model]:
        #        fields_params = MappedFieldsFilterQueryFieldsParameters(mapped_fields)
        #        query, arguments, sql_params = self.query_helper.build_filter_query(
        #            collection, filter, fields_params, select_fqid=True
        #        )
        #        models = self.fetch_models(query, arguments, sql_params, mapped_fields)
        return {}

    def aggregate(
        self,
        collection: Collection,
        filter: Filter,
        #        fields_params: BaseAggregateFilterQueryFieldsParameters,
    ) -> Any:
        #        query, arguments, sql_params = self.query_helper.build_filter_query(
        #            collection, filter, fields_params
        #        )
        #        value = self.connection.query(query, arguments, sql_params)
        return {}

    def fetch_models(
        self,
        query: str,
        arguments: list[str],
        sql_parameters: list[str],
        mapped_fields: list[str],
    ) -> dict[int, Model]:
        #        """Fetched models for one collection"""
        #        result = self.connection.query(query, arguments, sql_parameters)
        #        models = {}
        #        for row in result:
        #            # if there are mapped_fields, we already resolved them in the query and
        #            # can just copy all fields. else we can just use the whole `data` field
        #            if len(mapped_fields) > 0:
        #                model = row.copy()
        #                del model["__fqid__"]
        #            else:
        #                model = row["data"]
        #            models[id_from_fqid(row["__fqid__"])] = model
        return {}

    def build_models_from_result(
        self, result, mapped_fields: MappedFields
    ) -> dict[str, Model]:
        #        result_map = {}
        #        for row in result:
        #            fqid = row["fqid"]
        #
        #            if mapped_fields.needs_whole_model:
        #                # at least one collection needs all fields, so we need to select data
        #                row = row["data"]
        #
        #            if fqid in mapped_fields.per_fqid and len(mapped_fields.per_fqid[fqid]) > 0:
        #                model = {}
        #                for field in mapped_fields.per_fqid[fqid]:
        #                    if row.get(field) is not None:
        #                        model[field] = row[field]
        #            else:
        #                model = row
        #            result_map[fqid] = model
        #
        return {}

    def build_model_ignore_deleted(
        self, fqid: FullQualifiedId, position: Position | None = None
    ) -> Model:
        #        models = self.build_models_ignore_deleted([fqid], position)
        #        try:
        #            return models[fqid]
        #        except KeyError:
        #            raise ModelDoesNotExist(fqid)
        return {}

    def build_models_ignore_deleted(
        self, fqids: list[FullQualifiedId], position: Position | None = None
    ) -> dict[FullQualifiedId, Model]:
        #        # Optionally only builds the models up to the specified position.
        #        # TODO: There might be a speedup: Get the model from the readdb first.
        #        # If the model exists there, read the position from it, use the model
        #        # as a starting point in `build_model_from_events` and just fetch all
        #        # events after the position.
        #        if position:
        #            pos_cond = "and position <= %s"
        #            pos_args = [position]
        #        else:
        #            pos_cond = ""
        #            pos_args = []
        #
        #        query = dedent(
        #            f"""\
        #            select fqid, type, data, position from events e
        #            where fqid = any(%s) {pos_cond}
        #            order by position asc, weight asc"""
        #        )
        #
        #        args: list[Any] = [fqids]
        #        db_events = self.connection.query(query, args + pos_args)
        #
        #        events_per_fqid: dict[FullQualifiedId, list[dict[str, Any]]] = defaultdict(list)
        #        for event in db_events:
        #            events_per_fqid[event["fqid"]].append(event)
        #
        #        models = {}
        #        for fqid, events in events_per_fqid.items():
        #            models[fqid] = self.build_model_from_events(events)
        #
        return {}

    def build_model_from_events(self, events: list[dict[str, Any]]) -> Model:
        #        if not events:
        #            raise BadCodingError()
        #
        #        create_event = events[0]
        #        assert create_event["type"] == EVENT_TYPE.CREATE
        #        model: Model = {**create_event["data"], META_DELETED: False}
        #
        #        # apply all other update/delete_fields
        #        for event in events[1:]:
        #            if event["type"] == EVENT_TYPE.UPDATE:
        #                model.update(event["data"])
        #            elif event["type"] == EVENT_TYPE.DELETE_FIELDS:
        #                for field in event["data"]:
        #                    if field in model:
        #                        del model[field]
        #            elif event["type"] == EVENT_TYPE.LIST_FIELDS:
        #                for field, value in apply_fields(
        #                    model, event["data"]["add"], event["data"]["remove"]
        #                ).items():
        #                    model[field] = value
        #            elif event["type"] == EVENT_TYPE.DELETE:
        #                model[META_DELETED] = True
        #            elif event["type"] == EVENT_TYPE.RESTORE:
        #                model[META_DELETED] = False
        #            else:
        #                raise BadCodingError()
        #
        #        model[META_POSITION] = events[-1]["position"]
        return {}

    def get_history_information(
        self, fqids: list[FullQualifiedId]
    ) -> dict[FullQualifiedId, list[HistoryInformation]]:
        #        positions = self.connection.query(
        #            """select fqid, position, timestamp, user_id, information from positions natural join events
        #            where fqid = any(%s) and information::text <> %s::text order by position asc""",
        #            [fqids, self.json(None)],
        #        )
        #        history_information = defaultdict(list)
        #        for position in positions:
        #            history_information[position["fqid"]].append(
        #                HistoryInformation(
        #                    position=position["position"],
        #                    timestamp=position["timestamp"].timestamp(),
        #                    user_id=position["user_id"],
        #                    information=position["information"],
        #                )
        #            )
        return {}

    def is_empty(self) -> bool:
        return not self.connection.query_single_value(
            "select exists(select * from positions)", []
        )

    def get_max_position(self) -> Position:
        return self.connection.query_single_value(
            "select max(position) from positions", []
        )

    def get_current_migration_index(self) -> int:
        #        result = self.connection.query(
        #            "select min(migration_index), max(migration_index) from positions", []
        #        )
        #        min_migration_index = result[0]["min"] if result else None
        #        max_migration_index = result[0]["max"] if result else None
        #        if min_migration_index != max_migration_index:
        #            raise InvalidDatastoreState(
        #                "The datastore has inconsistent migration indices: "
        #                + f"Minimum is {min_migration_index}, maximum is {max_migration_index}."
        #            )
        return -1

    def json(self, data):
        return self.connection.to_json(data)
