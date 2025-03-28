import threading

from psycopg import Connection, sql
from psycopg.errors import (
    CheckViolation,
    GeneratedAlways,
    NotNullViolation,
    SyntaxError,
    UndefinedColumn,
    UndefinedTable,
    UniqueViolation,
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
        # log_all_modified_fields: bool = True,
    ) -> list[FullQualifiedId]:
        #       with make_span("write request"):
        self.write_requests = write_requests

        modified_models = set()
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

                    modified_models.update(
                        self.write_events(
                            write_request.events,
                            write_request.user_id,
                            # models,
                        )
                    )

                    # return modified_fqfields

        self.print_stats()
        self.print_summary()
        # TODO if returning the id is all then this can be done at the bottom of call stack without generating fqids.
        return list(modified_models)  # type: ignore

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

    def write_events(
        self,
        events: list[Event],
        user_id: int | None,  # TODO is None okay?
    ) -> list[FullQualifiedId]:
        if not events:
            raise BadCodingException("Events are needed.")

        models_created_or_updated = set()
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
            else:
                collection = event["collection"]

            if event["type"] == EventType.Create:
                models_created_or_updated.add(self.insert_model(event, collection))
            if event["type"] == EventType.Update:
                models_created_or_updated.add(self.update_model(event, collection))
            if event["type"] == EventType.Delete:
                models_created_or_updated.discard(self.delete_model(event))

        return list(models_created_or_updated)

    def insert_model(self, event: Event, collection: Collection) -> FullQualifiedId:
        fields = event["fields"]
        statement = sql.SQL(
            """
            INSERT INTO {table_name} ({columns})
            VALUES ({values})
            """
        ).format(
            table_name=sql.Identifier(f"{collection}_t"),
            columns=sql.SQL(", ").join(map(sql.Identifier, fields)),
            values=sql.SQL(", ").join(fields.values()),
        )
        return self.execute_sql(statement, collection, fields.get("id"))

    def delete_model(self, event: Event) -> FullQualifiedId:
        collection, id_ = collection_and_id_from_fqid(event["fqid"])
        statement = sql.SQL(
            """
            DELETE FROM {table_name} WHERE id = {id}
            """
        ).format(id=sql.Literal(id_), table_name=sql.Identifier(f"{collection}_t"))
        return self.execute_sql(statement, collection, id_)

    def update_model(self, event: Event, collection: Collection) -> FullQualifiedId:
        table_name = f"{collection}_t"
        statement = sql.SQL(
            """
            UPDATE {table_name} SET
            """
        ).format(
            table_name=sql.Identifier(table_name),
        )

        set_dict = event["fields"]  # id always exists for updates
        if list_fields := event.get("list_fields"):
            add_dict = list_fields.get("add", dict())
            remove_dict = list_fields.get("remove", dict())
            joined_type_dict = {
                field_name: type(value_list[0])
                for dictionary in [add_dict, remove_dict]
                for field_name, value_list in dictionary.items()
                if value_list
            }
        else:
            joined_type_dict = dict()

        statement += sql.SQL(", ").join(
            sql.SQL("""{field} = {value}""").format(
                field=sql.Identifier(field_name),
                value=sql.Literal(value),
            )
            for field_name, value in set_dict.items()
            if field_name not in joined_type_dict
        )

        values = {
            field_name: sql.SQL(
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
                    self.get_array_with_type(list_type, set_dict[field_name])
                    + sql.SQL(") AS list_element")
                    if set_dict.get(field_name)
                    else sql.Identifier(table_name)
                    + sql.SQL(".")
                    + sql.Identifier(field_name)
                    + sql.SQL(") AS list_element FROM ")
                    + sql.Identifier(table_name)
                ),
                values_add=self.get_array_with_type(
                    list_type, add_dict.get(field_name, [])
                ),
                values_remove=self.get_array_with_type(
                    list_type, remove_dict.get(field_name, [])
                ),
            )
            for field_name, list_type in joined_type_dict.items()
        }

        if values and any(k for k in set_dict if k not in joined_type_dict):
            statement += sql.SQL(", ")
        statement += sql.SQL(", ").join(
            sql.SQL(
                """
            {field} = {values}"""
            ).format(
                field=sql.Identifier(field),
                values=value,
            )
            for field, value in values.items()
        )
        statement += sql.SQL(
            """
            WHERE id = {id}
            """
        ).format(id=set_dict["id"])
        return self.execute_sql(statement, collection, set_dict["id"])

    def execute_sql(
        self, statement: sql.Composable, collection: Collection, target_id: Id | None
    ) -> FullQualifiedId:
        statement += sql.SQL("""RETURNING id;""")

        try:
            with self.connection.cursor() as curs:
                # print(statement.as_string(curs), flush=True)
                curs.execute(statement)
                if curs.statusmessage in ["DELETE 0", "UPDATE 0"]:
                    assert target_id  # we will never reach here with delete or update events being None on id
                    raise ModelDoesNotExist(
                        fqid_from_collection_and_id(collection, target_id)
                    )
                id_ = curs.fetchone().get("id")  # type: ignore
        except UniqueViolation as e:
            if "duplicate key value violates unique constraint" in e.args[0]:
                raise ModelExists(
                    fqid_from_collection_and_id(collection, target_id or id_)
                )
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
        except SyntaxError as e:
            if 'syntax error at or near "WHERE"' in e.args[0]:
                raise ModelDoesNotExist(fqid_from_collection_and_id(collection, id_))
            else:
                raise e
        except Exception as e:
            raise e
            raise ModelLocked(
                f"Model ... is locked on fields .... {e}\
                This is not the end. There will be more next episode. To be continued."
            )

        return fqid_from_collection_and_id(collection, id_)

    def get_array_with_type(
        self,
        list_type: type,
        affected_list: list[int] | list[str],
    ) -> sql.Composable:
        if list_type == int:
            if affected_list:
                return sql.Literal(affected_list)
            else:
                return sql.Literal(affected_list) + sql.SQL("::int2[]")
        elif list_type == str:
            return sql.Literal(affected_list) + sql.SQL("::text[]")
        else:
            raise ValueError("Only integer or string lists are supported.")

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
