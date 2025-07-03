import threading
from typing import Any

from psycopg import Connection, rows, sql
from psycopg.errors import (
    CheckViolation,
    GeneratedAlways,
    NotNullViolation,
    SyntaxError,
    UndefinedColumn,
    UndefinedTable,
    UniqueViolation,
)

from openslides_backend.models.base import model_registry
from openslides_backend.models.fields import (
    Field,
    GenericRelationListField,
    RelationListField,
)
from openslides_backend.services.database.interface import FQID_MAX_LEN
from openslides_backend.services.postgresql.db_connection_handling import (
    retry_on_db_failure,
)
from openslides_backend.shared.exceptions import (
    BadCodingException,
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelLocked,
    RelationException,
)
from openslides_backend.shared.interfaces.event import (
    Event,
    EventType,
    ListField,
    ListFieldsDict,
)
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
from openslides_backend.shared.typing import JSON, Model, PartialModel

from ...shared.interfaces.env import Env
from ...shared.interfaces.logging import LoggingModule
from .database_reader import DatabaseReader, GetManyRequest
from .event_types import EVENT_TYPE
from .query_helper import SqlQueryHelper

EventData = tuple[FullQualifiedId, EVENT_TYPE, JSON, int]


class DatabaseWriter(SqlQueryHelper):
    _lock = threading.Lock()
    database_reader: DatabaseReader
    env: Env

    def __init__(
        self, connection: Connection[rows.DictRow], logging: LoggingModule, env: Env
    ) -> None:
        self.env = env
        self.logger = logging.getLogger(__name__)
        self.connection = connection
        self.database_reader = DatabaseReader(self.connection, logging, env)

    @retry_on_db_failure
    def write(
        self,
        write_requests: list[WriteRequest],
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

                    modified_models.update(self.write_events(write_request.events))

        self.print_stats()
        self.print_summary()
        return sorted(modified_models)

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
                id_ = None

            if event["type"] == EventType.Create:
                models_created_or_updated.add(self.insert_model(event, collection, id_))
            if event["type"] == EventType.Update:
                assert id_
                models_created_or_updated.add(self.update_model(event, collection, id_))
            if event["type"] == EventType.Delete:
                assert id_
                models_created_or_updated.discard(
                    self.delete_model(event, collection, id_)
                )

        return list(models_created_or_updated)

    def insert_model(
        self, event: Event, collection: Collection, id_: Id | None
    ) -> FullQualifiedId:
        event_fields = event.get("fields", dict())
        simple_fields, intermediate_tables = self.get_simple_fields_intermediate_table(
            event_fields, collection
        )
        if id_ and not simple_fields.get("id"):
            simple_fields["id"] = id_
        statement = sql.SQL(
            """
            INSERT INTO {table_name} ({columns})
            VALUES ({values})
            """
        ).format(
            table_name=sql.Identifier(f"{collection}_t"),
            columns=sql.SQL(", ").join(map(sql.Identifier, simple_fields)),
            values=sql.SQL(", ").join(sql.SQL("%s") for _ in range(len(simple_fields))),
        )
        id_ = self.execute_sql(statement, list(simple_fields.values()), collection, id_)
        self.write_to_intermediate_tables(
            event_fields, intermediate_tables, id_, collection
        )
        return fqid_from_collection_and_id(collection, id_)

    def delete_model(
        self, event: Event, collection: Collection, id_: Id
    ) -> FullQualifiedId:
        statement = sql.SQL(
            """
            DELETE FROM {table_name} WHERE id = {id}
            """
        ).format(id=sql.Literal(id_), table_name=sql.Identifier(f"{collection}_t"))
        return fqid_from_collection_and_id(
            collection, self.execute_sql(statement, [], collection, id_)
        )

    def update_model(
        self, event: Event, collection: Collection, id_: Id
    ) -> FullQualifiedId:
        table = sql.Identifier(f"{collection}_t")
        statement = sql.SQL(
            """
            UPDATE {table} SET
            """
        ).format(
            table=table,
        )

        event_fields = event["fields"]
        set_fields_dict, intermediate_tables = (
            self.get_simple_fields_intermediate_table(event_fields, collection)
        )

        self.delete_from_intermediate_tables(
            event_fields, intermediate_tables, id_, collection, directly=False
        )
        self.write_to_intermediate_tables(
            event_fields, intermediate_tables, id_, collection
        )

        list_fields = event.get("list_fields") or dict()
        add_dict = list_fields.get("add", dict())
        remove_dict = list_fields.get("remove", dict())
        list_types, nm_relation_list_fields = (
            self.get_list_types_and_nm_relation_list_fields(
                collection, add_dict, remove_dict
            )
        )

        for field_name in nm_relation_list_fields:
            if field_name in add_dict:
                self.write_to_intermediate_tables(
                    add_dict, nm_relation_list_fields, id_, collection
                )
            if field_name in remove_dict:
                self.delete_from_intermediate_tables(
                    remove_dict, nm_relation_list_fields, id_, collection, directly=True
                )

        array_statements_per_field, array_values = self.get_array_values(
            collection, table, set_fields_dict, add_dict, remove_dict, list_types
        )

        statement += sql.SQL(", ").join(
            sql.SQL("""{field} = %s""").format(
                field=sql.Identifier(field_name),
            )
            for field_name in set_fields_dict.keys()
            if field_name not in array_statements_per_field
        )
        arguments = [
            value
            for field_name, value in set_fields_dict.items()
            if field_name not in array_statements_per_field
        ]

        if array_statements_per_field and any(
            k for k in set_fields_dict if k not in array_statements_per_field
        ):
            statement += sql.SQL(", ")
        statement += sql.SQL(", ").join(
            sql.SQL(
                """
            {field} = {array_statement}"""
            ).format(
                field=sql.Identifier(field),
                array_statement=statement,
            )
            for field, statement in array_statements_per_field.items()
        )
        for array_value in array_values:
            arguments.extend(array_value)

        # to prevent missing exceptions and a malformed statement we construct a noop
        if not arguments:
            statement += sql.SQL("id = id")

        statement += sql.SQL(
            """
            WHERE id = {id}
            """
        ).format(id=id_)
        return fqid_from_collection_and_id(
            collection,
            self.execute_sql(statement, arguments, collection, id_),
        )

    def get_simple_fields_intermediate_table(
        self, event_fields: PartialModel, collection: Collection
    ) -> tuple[dict, dict]:
        """
        returns in the first dict the fields that do not need special handling within an intermediate table.
        returns in the second dict the other fields with their field representation from the model_registry.
        """
        collection_cls = model_registry[collection]()
        return {
            field_name: value
            for field_name, value in event_fields.items()
            if (field := collection_cls.get_field(field_name))
            if not field.is_view_field
            if not field_name == "organization_id"
        }, {
            field_name: field
            for field_name in event_fields
            if (field := collection_cls.get_field(field_name))
            if field.is_primary and field.write_fields
            if any(
                isinstance(field, type_)
                for type_ in [RelationListField, GenericRelationListField]
            )
        }

    def get_list_types_and_nm_relation_list_fields(
        self,
        collection: Collection,
        add_dict: ListFieldsDict,
        remove_dict: ListFieldsDict,
    ) -> tuple[dict[Collection, type], dict[Collection, Field]]:
        """
        used for 'add' and 'remove' list fields
        returns in the tuple a dict of all fields that are just list fields with the field information
        returns in the second dict all fields that are relation fields
        """
        collection_cls = model_registry[collection]()
        lists_type_dict = dict()
        nm_relation_list_fields = dict()
        for dictionary in [add_dict, remove_dict]:
            for field_name, value_list in dictionary.items():
                if field := collection_cls.get_field(field_name):
                    if value_list and not field.is_view_field:
                        lists_type_dict[field_name] = type(value_list[0])
                    if (
                        field.is_primary
                        and field.write_fields
                        and any(
                            isinstance(field, type_)
                            for type_ in [RelationListField, GenericRelationListField]
                        )
                    ):
                        nm_relation_list_fields[field_name] = field
        return (lists_type_dict, nm_relation_list_fields)

    def write_to_intermediate_tables(
        self,
        event_fields: PartialModel,
        intermediate_tables: dict[str, Field],
        id_: Id,
        collection: Collection,
    ) -> None:
        """writes a row to the intermediate table with the own id and the relationfield from the event."""
        for field_name, field in intermediate_tables.items():
            if not field.write_fields:
                raise BadCodingException(
                    f"The field {field_name} should be in an n:m relation and thus have the corresponding table information."
                )
            intermediate_table, close_side, far_side, _ = field.write_fields
            if event_fields[field_name]:
                statement = sql.SQL(
                    """
                    INSERT INTO {table_name} ({columns})
                    VALUES {placeholders}
                    ON CONFLICT ({columns}) DO NOTHING
                    """
                ).format(
                    table_name=sql.Identifier(intermediate_table),
                    columns=sql.Identifier(close_side)
                    + sql.SQL(", ")
                    + sql.Identifier(far_side),
                    placeholders=sql.SQL(", ").join(
                        sql.SQL(f"({id_}, %s)")
                        for _ in range(len(event_fields[field_name]))
                    ),
                )
                self.execute_sql(
                    statement,
                    event_fields[field_name],
                    collection,
                    id_,
                    return_id=False,
                )

    def delete_from_intermediate_tables(
        self,
        event_fields: PartialModel,
        intermediate_tables: dict[str, Field],
        id_: Id,
        collection: Collection,
        directly: bool,
    ) -> None:
        """
        Deletes all rows with the combination of the given id_ and the list from the intermediate tables.
        If directly is True, the values of the list are used. Otherwise the negation of those is used.
        """
        for field_name, field in intermediate_tables.items():
            if not field.write_fields:
                raise BadCodingException(
                    f"The field {field_name} should be in an n:m relation and thus have the corresponding table information."
                )
            intermediate_table, own_column, other_column, *_ = field.write_fields
            statement = sql.SQL(
                """
                DELETE FROM {table_name}
                WHERE ({own_column} = {id} AND {negation}({other_column} = ANY(%s)))
                """
            ).format(
                table_name=sql.Identifier(intermediate_table),
                own_column=sql.Identifier(own_column),
                other_column=sql.Identifier(other_column),
                negation=sql.SQL("") if directly else sql.SQL("NOT "),
                id=id_,
            )
            if isinstance((values := event_fields[field_name]), list | None):
                other_column_values: list[int] = values or []
            else:
                other_column_values = [values]
            self.execute_sql(
                statement,
                [other_column_values],
                collection,
                id_,
                return_id=False,
            )

    def get_array_values(
        self,
        collection: Collection,
        table: sql.Identifier,
        set_dict: PartialModel,
        add_dict: ListFieldsDict,
        remove_dict: ListFieldsDict,
        field_list_types: dict[str, type],
    ) -> tuple[
        dict[str, sql.Composed],
        list[tuple[ListField, ListField, ListField] | tuple[ListField, ListField]],
    ]:
        """
        returns the composed array calculation strings and the lists/arrays to be inserted as arguments
        """
        return (
            {
                field_name: sql.SQL(
                    """ARRAY(
                SELECT unnest({col_or_placeholder_plus_type}) AS list_element{nothing_or_table}
                EXCEPT
                SELECT unnest(%s{remove_list_type})
                UNION
                SELECT unnest(%s{add_list_type})
                ORDER BY list_element
            )"""
                ).format(
                    col_or_placeholder_plus_type=(
                        sql.Placeholder()
                        + self.get_array_type(list_type, set_dict[field_name])
                        if field_name in set_dict
                        else sql.Identifier(field_name)
                    ),
                    nothing_or_table=(
                        sql.SQL("")
                        if field_name in set_dict
                        else sql.SQL(" FROM ") + table
                    ),
                    add_list_type=self.get_array_type(
                        list_type, add_dict.get(field_name, [])
                    ),
                    remove_list_type=self.get_array_type(
                        list_type, remove_dict.get(field_name, [])
                    ),
                )
                for field_name, list_type in field_list_types.items()
            },
            [
                (
                    (
                        set_dict[field_name],
                        remove_dict.get(field_name, []),
                        add_dict.get(field_name, []),
                    )
                    if field_name in set_dict
                    else (
                        remove_dict.get(field_name, []),
                        add_dict.get(field_name, []),
                    )
                )
                for field_name in field_list_types.keys()
            ],
        )

    def execute_sql(
        self,
        statement: sql.Composed,
        arguments: list[Any],
        collection: Collection,
        target_id: Id | None,
        return_id: bool = True,
    ) -> Id:
        """
        executes the statement with the arguments
        returns the id if return_id is True else returns zero
        """
        if return_id:
            statement += sql.SQL("""RETURNING id;""")

        try:
            with self.connection.cursor() as curs:
                curs.execute(statement, arguments)
                if return_id:
                    result = curs.fetchone()
                    if not result or curs.statusmessage in ["DELETE 0", "UPDATE 0"]:
                        assert target_id  # we will never reach here with delete or update events being None on id
                        raise ModelDoesNotExist(
                            fqid_from_collection_and_id(collection, target_id)
                        )
                    id_ = result.get("id", 0)
                    return id_
        except UniqueViolation as e:
            if "duplicate key value violates unique constraint" in e.args[0]:
                if "Key (id)" in e.args[0]:
                    raise ModelExists(
                        fqid_from_collection_and_id(collection, target_id or id_)
                    )
                else:
                    raise RelationException(
                        f"Relation from {fqid_from_collection_and_id(collection, target_id or id_)} violates UNIQUE constraint: {e}"
                    )
        except NotNullViolation as e:
            raise BadCodingException(
                f"Missing fields in {collection}/{target_id}. Ooopsy Daisy! {e}"
            )
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
                raise ModelDoesNotExist(
                    fqid_from_collection_and_id(collection, target_id or id_)
                )
            else:
                raise e
        except Exception as e:
            raise e
            raise ModelLocked(
                f"Model ... is locked on fields .... {e}\
                This is not the end. There will be more next episode. To be continued."
            )

        return 0

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
                [GetManyRequest(collection, sorted(ids))]
            )
            for collection, ids in ids_per_collection.items()
        }

    @retry_on_db_failure
    def reserve_ids(self, collection: str, amount: int) -> list[Id]:
        with make_span(self.env, "reserve ids"):
            with self.connection.cursor() as curs:
                statement = sql.SQL(
                    """SELECT nextval('{collection}_t_id_seq') FROM generate_series(1, {amount})"""
                ).format(
                    collection=sql.SQL(collection),
                    amount=sql.Literal(amount),
                )
                if result := curs.execute(statement).fetchall():
                    ids = [item.get("nextval", 0) for item in result]
                else:
                    raise BadCodingException("db id sequence broken.")
                self.logger.info(f"{len(ids)} ids reserved")
                return ids

    @retry_on_db_failure
    def truncate_db(self) -> None:
        with self.connection.cursor() as curs:
            curs.execute("SELECT tablename from pg_tables WHERE schemaname = 'public'")
            table_names = ", ".join(table["tablename"] for table in curs.fetchall())
        self.connection.execute(f"TRUNCATE TABLE {table_names} RESTART IDENTITY;")
