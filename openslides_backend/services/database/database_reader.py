from typing import Any, ContextManager

from psycopg.errors import UndefinedColumn, UndefinedTable

from openslides_backend.shared.exceptions import DatabaseException, InvalidFormat
from openslides_backend.shared.filters import Filter
from openslides_backend.shared.patterns import (
    Collection,
    Field,
    FullQualifiedId,
    Id,
    Position,
)
from openslides_backend.shared.typing import HistoryInformation, LockResult, Model

from ..database.commands import GetManyRequest
from .mapped_fields import MappedFields
from .postgresql.db_connection_handling import get_current_os_conn
from .query_helper import SqlQueryHelper


class DatabaseReader:

    query_helper = SqlQueryHelper()

    def __init__(self) -> None:
        with get_current_os_conn() as db_connection:
            self.connection = db_connection

    def get_database_context(self) -> ContextManager[None]:
        return self.connection

    def get_many(
        self,
        get_many_requests: list[GetManyRequest],
        lock_result: LockResult = True,
    ) -> dict[Collection, dict[Id, Model]]:
        result: dict[Collection, dict[int, dict[str, Any]]] = {
            get_many_request.collection: dict()
            for get_many_request in get_many_requests
        }

        # TODO create one transaction from db
        for get_many_request in get_many_requests:
            if not (collection := get_many_request.collection):
                raise DatabaseException(
                    "No collection supplied. Give at least one collection."
                )
            if not (ids := get_many_request.ids):
                raise DatabaseException(
                    f"No id for collection {collection} supplied. Give at least one id."
                )
            for id_ in ids:
                if not id_ > 0:
                    raise InvalidFormat("Id must be positive.")
            if get_many_request.mapped_fields is None:
                mapped_fields = MappedFields()
            else:
                mapped_fields = MappedFields(list(get_many_request.mapped_fields))
            if "id" not in mapped_fields.unique_fields:
                mapped_fields.unique_fields.append("id")

            # arguments: list[Any] = [list(fqids)]

            (
                mapped_fields_str,
                _,  # mapped_field_args,
            ) = self.query_helper.build_select_from_mapped_fields(mapped_fields)
            query = (
                f"""SELECT {mapped_fields_str} FROM {collection}_t WHERE id = ANY(%s)"""
            )

            try:
                cur = self.connection.cursor()
                db_result = cur.execute(query, [list(ids)]).fetchall()
            except UndefinedColumn as e:
                raise InvalidFormat(f"A field does not exist in model table: {e}")
            except UndefinedTable as e:
                raise InvalidFormat(
                    f"The collection does not exist in the database: {e}"
                )
            except Exception as e:
                raise DatabaseException(f"Unexpected error reading from database: {e}")

            self.insert_models_into_result(
                db_result, mapped_fields, collection, result[collection]
            )
            # result[collection].update(self.build_models_from_result(db_result, mapped_fields, collection))
        return result

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

    def insert_models_into_result(
        self,
        db_result: list[dict[str, Any]],
        mapped_fields: MappedFields,
        collection: Collection,
        collection_result_part: dict[int, Any],
    ) -> None:
        # result_map = {}
        for row in db_result:
            id_ = row["id"]

            if (
                not mapped_fields.needs_whole_model
                and mapped_fields.unique_fields
                and id_ in collection_result_part
            ):
                model = collection_result_part[id_]
                for field in mapped_fields.unique_fields:
                    if row.get(field) is not None:
                        model[field] = row[field]
            else:
                collection_result_part[id_] = row
            # result_map[row['id']] = model

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

    # def is_empty(self) -> bool:
    #     return not self.connection.query_single_value(
    #         "select exists(select * from positions)", []
    #     )

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
