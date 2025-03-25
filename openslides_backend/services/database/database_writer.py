import threading
from collections import defaultdict

from psycopg import Connection, sql
from psycopg.errors import (
    CheckViolation,
    GeneratedAlways,
    NotNullViolation,
    UndefinedColumn,
    UndefinedTable,
)

from openslides_backend.services.database.interface import (
    COLLECTION_MAX_LEN,
    FQID_MAX_LEN,
)
from openslides_backend.shared.exceptions import (
    BadCodingException,
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelLocked,
)
from openslides_backend.shared.interfaces.event import Event, EventType
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.shared.otel import make_span
from openslides_backend.shared.patterns import (
    Collection,
    Field,
    FullQualifiedId,
    Id,
    collection_and_id_from_fqid,
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from openslides_backend.shared.typing import JSON, Model

from ...shared.interfaces.env import Env
from ...shared.interfaces.logging import LoggingModule
from .database_reader import DatabaseReader, GetManyRequest
from .event_types import EVENT_TYPE

EventData = tuple[FullQualifiedId, EVENT_TYPE, JSON, int]


class DatabaseWriter:
    _lock = threading.Lock()
    database_reader: DatabaseReader
    env: Env

    def __init__(
        self, connection: Connection, logging: LoggingModule, env: Env
    ) -> None:
        self.env = env
        self.logger = logging.getLogger(__name__)
        self.connection = connection
        self.database_reader = DatabaseReader(self.connection, logging, env)

    # @retry_on_db_failure
    def write(
        self,
        write_requests: list[WriteRequest],
        models: dict[Collection, dict[Id, Model]],
        # log_all_modified_fields: bool = True,
    ) -> list[Id]:
        #       with make_span("write request"):
        self.write_requests = write_requests

        with self._lock:
            for write_request in self.write_requests:
                #         modified_models = self.write_with_database_context(
                #             write_request, models
                #         )
                # def write_with_database_context(
                #     self, write_request: WriteRequest, models: dict[str, dict[Id, Model]]
                # ) -> dict[FullQualifiedId, dict[Field, JSON]]:
                with make_span(self.env, "write with database context"):
                    # # get migration index
                    # if write_request.migration_index is None:
                    #     migration_index = self.database_reader.get_current_migration_index()
                    # else:
                    #     if not self.database_reader.is_empty():
                    #         raise DatastoreNotEmpty(
                    #             f"Passed a migration index of {write_request.migration_index}, but the datastore is not empty."
                    #         )
                    #     migration_index = write_request.migration_index

                    # Check locked_fields -> Possible LockedError
                    # self.occ_locker.assert_locked_fields(write_request)

                    # Insert db events
                    # information = (
                    #     write_request.information if write_request.information else None
                    # )
                    modified_models = self.write_events(
                        write_request.events,
                        # migration_index,
                        # information,
                        write_request.user_id,
                        models,
                    )

                    # return modified_fqfields

        self.print_stats()
        self.print_summary()
        # TODO if returning the id is all then this can be done at the bottom of call stack without generating fqids.
        return [model["id"] for model in modified_models.values()]  # type: ignore

    def print_stats(self) -> None:
        pass
        # stats: dict[str, int] = defaultdict(int)
        # for write_request in self.write_requests:
        #     for event in write_request.events:
        #         stats[self.get_request_name(event)] += 1
        # stats_string = ", ".join(f"{cnt} {name}" for name, cnt in stats.items())
        # logger.info(f"Events executed ({stats_string})")

    def print_summary(self) -> None:
        pass
        # summary: dict[str, set[str]] = defaultdict(set)  # event type <-> set[fqid]
        # for write_request in self.write_requests:
        #     for event in write_request.events:
        #         summary[self.get_request_name(event)].add(event.fqid)
        # logger.info(
        #     "\n".join(
        #         f"{eventType}: {list(fqids)}" for eventType, fqids in summary.items()
        #     )
        # )

    def get_request_name(self, event: WriteRequest) -> str:
        return type(event).__name__.replace("Request", "").replace("Event", "").upper()

    def write_model_updates(
        self, models_per_collection: dict[Collection, dict[int, Model]]
    ) -> dict[FullQualifiedId, dict[Field, JSON]]:
        result = dict()

        def get_array_with_type(
            determining_list: list[int] | list[str],
            affected_list: list[int] | list[str],
        ) -> sql.Composable:
            if all(isinstance(element, int) for element in determining_list):
                if affected_list:
                    return sql.Literal(affected_list)
                else:
                    return sql.Literal(affected_list) + sql.SQL("::int2[]")
            elif all(isinstance(element, str) for element in determining_list):
                return sql.Literal(affected_list) + sql.SQL("::text[]")
            else:
                raise ValueError("Only pure integer or string lists are supported.")

        for collection, models in models_per_collection.items():
            for model in models.values():
                table_name = collection + "_t"
                add_dict = model.pop("add", dict())
                remove_dict = model.pop("remove", dict())
                joined_dict = add_dict | remove_dict
                all_field_names_dict = [*[k for k in model if k not in joined_dict], *joined_dict]
                values = [v for k, v in model.items() if k not in joined_dict]
                for field, joined_list in joined_dict.items():
                    values.append(
                        sql.SQL(
                            """ARRAY(
                                SELECT unnest({base_array}
                                EXCEPT
                                SELECT unnest({values_remove})
                                UNION
                                SELECT unnest({values_add})
                                ORDER BY list_element
                            )"""
                        ).format(
                            base_array=(
                                get_array_with_type(joined_list, model.get(field)) + sql.SQL(") AS list_element")
                                if model.get(field)
                                else sql.Identifier(table_name) + sql.SQL(".") + sql.Identifier(field) + sql.SQL(") AS list_element FROM ") + sql.Identifier(table_name)
                            ),
                            values_add=get_array_with_type(joined_list, add_dict.get(field, [])),
                            values_remove=get_array_with_type(joined_list, remove_dict.get(field, [])),
                        )
                    )

                statement = sql.SQL(
                    """
                    INSERT INTO {table_name} ({columns})
                    VALUES ({values})
                    ON CONFLICT (id) DO UPDATE SET
                    """
                ).format(
                    table_name=sql.Identifier(table_name),
                    columns=sql.SQL(", ").join(map(sql.Identifier, all_field_names_dict)),
                    values=sql.SQL(", ").join(values),
                )
                statement += sql.SQL(", ").join(
                    sql.SQL("""{field} = EXCLUDED.{field}""").format(
                        field=sql.Identifier(field)
                    )
                    for field in all_field_names_dict
                )

                statement += sql.SQL(
                    """
                    RETURNING id;"""
                )

                try:
                    with self.connection.cursor() as curs:
                        # print(statement.as_string(curs), flush=True)
                        curs.execute(statement)
                        id_ = curs.fetchone().get("id")  # type:ignore
                except NotNullViolation as e:
                    raise BadCodingException(f"Missing fields. Ooops! {e}")
                except GeneratedAlways as e:
                    raise BadCodingException(
                        f"Used a field that must only be generated by the database: {e}"
                    )
                except UndefinedColumn as e:
                    column = e.args[0].split('"')[1]
                    raise InvalidFormat(
                        f"Field '{column}' does not exist in collection '{collection}': {e}"
                    )
                except UndefinedTable as e:
                    raise InvalidFormat(
                        f"Collection '{collection}' does not exist in the database: {e}"
                    )
                except CheckViolation as e:
                    raise e
                except Exception as e:
                    raise e
                    raise ModelLocked(
                        f"Model ... is locked on fields .... {e}\
                        This is not the end. There will be more next episode. To be continued."
                    )

                if "id" not in model:
                    model["id"] = id_
                result[fqid_from_collection_and_id(collection, id_)] = model
        return result

    def write_events(
        self,
        events: list[Event],
        user_id: int | None,  # TODO is None okay?
        models: dict[Collection, dict[Id, Model]],
    ) -> dict[FullQualifiedId, dict[Field, JSON]]:
        if not events:
            raise BadCodingException("Events are needed.")

        # TODO isn't the max id handled by the database?
        # save max id per collection to update the id_sequences if needed
        # max_id_per_collection: dict[Collection, int] = {}

        # moved to extended database
        # models = self.get_models_from_database(events)

        # the event translator also handles the validation of the event preconditions
        # TODO decide on basis of type how to validate and what else to do probably
        # not much since this should be more streamlined/ updateEvent?
        # db_events = self.event_translator.translate(event, models)
        no_id = 0
        ids_to_delete = defaultdict(set)
        for event in events:
            if fqid := event.get("fqid"):
                collection, id_ = collection_and_id_from_fqid(fqid)

                # fqid and event_payload.id must match
                if (
                    event["type"] != EventType.Delete
                    and (fields := event.get("fields"))
                    and (event_id := fields.get("id"))
                    and id_ != event_id
                ):
                    raise BadCodingException(
                        f"Fqid '{fqid}' and id '{event_id}' are mismatching."
                    )

                # id must exist(Update, Delete) or not(Create) in models
                if event["type"] == EventType.Create:
                    if id_ in models.get(collection, {}):
                        raise ModelExists(fqid)
                else:
                    if id_ not in models.get(collection, {}):
                        raise ModelDoesNotExist(
                            fqid_from_collection_and_id(collection, id_)
                        )

                # build models_to_write from event data
                if event["type"] == EventType.Delete:
                    ids_to_delete[collection].add(id_)
                    del models[collection][id_]
                    continue
                if fields:
                    if event["type"] == EventType.Update and "id" not in fields:
                        fields["id"] = id_
                    if id_ in models[collection]:
                        models[collection][id_].update(fields)
                    else:
                        models[collection][id_] = fields
                if (list_fields := event["list_fields"]) and event[
                    "type"
                ] == EventType.Update:
                    if "add" in models[collection][id_]:
                        models[collection][id_]["add"].update(list_fields["add"])
                    else:
                        models[collection][id_]["add"] = list_fields.get("add", dict())
                    if "remove" in models[collection][id_]:
                        models[collection][id_]["remove"].update(list_fields["remove"])
                    else:
                        models[collection][id_]["remove"] = list_fields.get(
                            "remove", dict()
                        )
            else:
                if (collection := event["collection"]) in models:
                    models[collection][no_id] = event["fields"]
                else:
                    models[collection] = {no_id: event["fields"]}
                no_id -= 1
        self.write_model_deletes(ids_to_delete)
        if models:
            return self.write_model_updates(models)
        else:
            return dict()

        # return models # TODO transform to fqid

    def get_models_from_database(
        self, events: list[Event]
    ) -> dict[FullQualifiedId, Model]:
        ids_per_collection: dict[Collection, set[Id]] = dict()
        for event in events:
            if not event.get("fqid"):
                continue
            if len(event["fqid"]) > FQID_MAX_LEN:
                raise InvalidFormat(
                    f"fqid {event['fqid']} is too long (max: {FQID_MAX_LEN})"
                )
            collection = collection_from_fqid(events[0]["fqid"])
            ids_per_collection[collection].add(id_from_fqid(event["fqid"]))

        return {
            collection: self.database_reader.get_many(
                [GetManyRequest(collection, list(ids))]
            )
            for collection, ids in ids_per_collection.items()
        }

    # @retry_on_db_failure
    def reserve_ids(self, collection: str, amount: int) -> list[Id]:
        with make_span(self.env, "reserve ids"):
            with self.connection.cursor() as curs:
                if not isinstance(amount, int):
                    raise InvalidFormat("Amount must be integer.")
                if amount <= 0:
                    raise InvalidFormat(f"Amount must be >= 1, not {amount}.")
                if len(collection) > COLLECTION_MAX_LEN or not collection:
                    raise InvalidFormat(
                        f"Collection length must be between 1 and {COLLECTION_MAX_LEN}"
                    )

                # TODO better option to read is_called and last_value?
                curs.execute(f"""SELECT nextval('{collection}_t_id_seq')""")
                # TODO is there a possibility of failure f.e. empty return value?
                current_max_id = curs.fetchone().get("nextval")  # type:ignore
                # TODO this should be set the is_called flag to false. Is that so? Shouldn't then no minus 1?
                curs.execute(
                    f"""SELECT setval('{collection}_t_id_seq', {amount + current_max_id - 1})"""
                )
                new_max_id = curs.fetchone().get("setval")  # type:ignore
                ids = list(range(current_max_id, new_max_id + 1))
                self.logger.info(f"{len(ids)} ids reserved")
                return ids

    # @retry_on_db_failure
    def delete_history_information(self) -> None:
        with self.connection:
            pass
            # self.database_reader.delete_history_information()
            # logger.info("History information deleted")

    # @retry_on_db_failure
    def truncate_db(self) -> None:
        pass
        # with self.database_reader.get_context():
        #     self.database_reader.truncate_db()
        # logger.info("Database truncated")

    # # # @retry_on_db_failure
    # def write_without_events(
    #     self,
    #     write_request: WriteRequest,
    # ) -> None:
    #     """
    #     # TODO can this all be done by the regular write now since we don't store events and positions?
    #     Writes or updates an action_worker- or
    #     import_preview-object.
    #     The record will be written to
    #     the models-table only, because there is no history
    #     needed and after the action is finished and notified,
    #     isn't needed anymore.
    #     There is no position available or needed,
    #     for redis notifying the 0 is used therefore.
    #     """
    #     self.write_requests = [write_request]

    #     with make_span("write action worker"):
    #         if isinstance(write_request.events[0], EventType.Delete):
    #             fqids_to_delete: list[FullQualifiedId] = []
    #             for event in write_request.events:
    #                 fqids_to_delete.append(event.fqid)
    #             self.write_model_deletes_without_events(fqids_to_delete)
    #         else:
    #             for event in write_request.events:
    #                 fields_with_delete = copy.deepcopy(event.fields)  # type: ignore
    #                 self.write_model_updates_without_events(
    #                     {event.fqid: fields_with_delete}
    #                 )

    #     self.print_stats()
    #     self.print_summary()

    # self.write_requests = [write_request]

    # with make_span("write action worker"):
    #     self.position_to_modified_models = {}
    #     if isinstance(write_request.events[0], RequestDeleteEvent):
    #         fqids_to_delete: list[FullQualifiedId] = []
    #         for event in write_request.events:
    #             fqids_to_delete.append(event.fqid)
    #         with self.database.get_context():
    #             self.database.write_model_deletes_without_events(fqids_to_delete)
    #     else:
    #         with self.database.get_context():
    #             for event in write_request.events:
    #         fields_with_delete = copy.deepcopy(event.fields)  # type: ignore
    #         fields_with_delete.update({META_DELETED: False})
    #         self.database.write_model_updates_without_events(
    #             {event.fqid: fields_with_delete}
    #         )
    #         self.position_to_modified_models[0] = {event.fqid: event.fields}  # type: ignore

    # self.print_stats()
    # self.print_summary()

    def write_model_deletes(self, ids_per_collection: dict[str, set[Id]]) -> None:
        """Physically delete of action_workers or import_previews"""
        # ids_per_collection = dict()
        # for fqid in fqids:
        #     collection, id_ = collection_and_id_from_fqid(fqid)
        #     ids_per_collection["collection"].append(id_)

        for collection, ids in ids_per_collection.items():
            statement = f"delete from {collection}_t where id = any(%s);"
            with self.connection.cursor() as curs:
                curs.execute(statement, (list(ids),))
