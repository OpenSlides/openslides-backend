from collections import defaultdict
from collections.abc import Iterable
from textwrap import dedent
from typing import ContextManager

from openslides_backend.datastore.shared.di import service_as_singleton
from openslides_backend.datastore.shared.postgresql_backend import (
    ALL_TABLES,
    EVENT_TYPE,
    ConnectionHandler,
)
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.datastore.shared.typing import (
    JSON,
    Collection,
    Field,
    Fqid,
    Id,
    Model,
    Position,
)
from openslides_backend.datastore.shared.util import (
    META_DELETED,
    META_POSITION,
    BadCodingError,
    DeletedModelsBehaviour,
    InvalidFormat,
    MappedFields,
    logger,
)
from openslides_backend.datastore.writer.core import BaseRequestEvent
from openslides_backend.shared.patterns import (
    collection_and_id_from_fqid,
    collectionfield_from_fqid_and_field,
)

from .db_events import BaseDbEvent, DbCreateEvent, apply_event_to_models
from .event_translator import EventTranslator

# Max lengths of the important key parts:
# collection: 32
# id: 16
# field: 207
# -> collection + id + field = 255
COLLECTION_MAX_LEN = 32
FQID_MAX_LEN = 48  # collection + id
COLLECTIONFIELD_MAX_LEN = 239  # collection + field


EventData = tuple[Position, Fqid, EVENT_TYPE, JSON, int]


@service_as_singleton
class SqlDatabaseBackendService:
    connection: ConnectionHandler
    read_database: ReadDatabase
    event_translator: EventTranslator

    def get_context(self) -> ContextManager[None]:
        return self.connection.get_connection_context()

    def insert_events(
        self,
        events: list[BaseRequestEvent],
        migration_index: int,
        information: JSON,
        user_id: int,
    ) -> tuple[Position, dict[Fqid, dict[Field, JSON]]]:
        if not events:
            raise BadCodingError()

        position = self.create_position(migration_index, information, user_id)

        # save all changes to all models to send them over redis
        modified_models: dict[Fqid, dict[Field, JSON]] = defaultdict(dict)
        # save max id per collection to update the id_sequences if needed
        max_id_per_collection: dict[Collection, int] = {}
        # save the raw data of the events to be inserted
        events_data: list[EventData] = []
        # save all event indices which modified collection fields to connect them later
        event_indices_per_modified_collectionfield: dict[str, list[int]] = defaultdict(
            list
        )

        # prefetch all needed data to reduce the amount of queries
        models = self.get_models_from_events(events)

        weight = 0
        for event in events:
            # the event translator also handles the validation of the event preconditions
            db_events = self.event_translator.translate(event, models)
            for db_event in db_events:
                weight += 1
                fqid = db_event.fqid
                collection, id = collection_and_id_from_fqid(fqid)

                # create event data
                events_data.append(
                    (
                        position,
                        fqid,
                        db_event.event_type,
                        self.json(db_event.get_event_data()),
                        weight,
                    )
                )

                for collectionfield in self.get_modified_collectionfields_from_event(
                    db_event
                ):
                    # weight is 1-indexed while the ids are 0-indexed
                    event_indices_per_modified_collectionfield[collectionfield].append(
                        weight - 1
                    )

                if isinstance(db_event, DbCreateEvent):
                    max_id_per_collection[collection] = max(
                        max_id_per_collection.get(collection, 0), id + 1
                    )
                self.apply_event_to_models(db_event, models, position)
                modified_models[fqid].update(db_event.get_modified_fields())

        self.update_id_sequences(max_id_per_collection)
        self.write_model_updates(models)
        event_ids = self.write_events(events_data)

        # update collectionfield tables
        collectionfield_ids = self.insert_modified_collectionfields_into_db(
            event_indices_per_modified_collectionfield.keys(), position
        )
        self.connect_events_and_collection_fields(
            event_ids,
            collectionfield_ids,
            event_indices_per_modified_collectionfield.values(),
        )
        return position, modified_models

    def create_position(
        self, migration_index: int, information: JSON, user_id: int
    ) -> Position:
        statement = dedent(
            """\
            insert into positions (timestamp, migration_index, user_id, information)
            values (current_timestamp, %s, %s, %s) returning position"""
        )
        arguments = [migration_index, user_id, self.json(information)]
        position = self.connection.query_single_value(statement, arguments)
        logger.info(f"Created position {position}")
        return position

    def get_models_from_events(
        self, events: list[BaseRequestEvent]
    ) -> dict[Fqid, Model]:
        fqids = set()
        for event in events:
            if len(event.fqid) > FQID_MAX_LEN:
                raise InvalidFormat(
                    f"fqid {event.fqid} is too long (max: {FQID_MAX_LEN})"
                )

            fqids.add(event.fqid)
        return self.read_database.get_many(
            fqids, MappedFields(), get_deleted_models=DeletedModelsBehaviour.ALL_MODELS
        )

    def apply_event_to_models(
        self, event: BaseDbEvent, models: dict[Fqid, Model], position: Position
    ) -> None:
        apply_event_to_models(event, models)
        models[event.fqid][META_POSITION] = position

    def write_model_updates(self, models: dict[Fqid, Model]) -> None:
        statement = dedent(
            """\
            insert into models (fqid, data, deleted) values %s
            on conflict(fqid) do update set data=excluded.data, deleted=excluded.deleted;"""
        )
        self.connection.execute(
            statement,
            [
                (fqid, self.json(model), model[META_DELETED])
                for fqid, model in models.items()
            ],
            use_execute_values=True,
        )

    def write_model_updates_without_events(self, models: dict[Fqid, Model]) -> None:
        statement = dedent(
            """\
            insert into models (fqid, data, deleted) values %s
            on conflict(fqid) do update set data=models.data || excluded.data, deleted=excluded.deleted;"""
        )
        self.connection.execute(
            statement,
            [
                (fqid, self.json(model), model[META_DELETED])
                for fqid, model in models.items()
            ],
            use_execute_values=True,
        )

    def write_model_deletes_without_events(self, fqids: list[Fqid]) -> None:
        """Physically delete of action_workers or import_previews"""
        statement = "delete from models where fqid in %s;"
        self.connection.execute(statement, [fqids], use_execute_values=True)

    def update_id_sequences(self, max_id_per_collection: dict[Collection, int]) -> None:
        statement = dedent(
            """\
            insert into id_sequences (collection, id) values %s
            on conflict(collection) do update
            set id=greatest(id_sequences.id, excluded.id);"""
        )
        arguments = list(max_id_per_collection.items())
        self.connection.execute(statement, arguments, use_execute_values=True)

    def write_events(self, events_data: list[EventData]) -> list[int]:
        return self.connection.query_list_of_single_values(
            "insert into events (position, fqid, type, data, weight) values %s returning id",
            events_data,
            use_execute_values=True,
        )

    def get_modified_collectionfields_from_event(self, event):
        return [
            collectionfield_from_fqid_and_field(event.fqid, field)
            for field in event.get_modified_fields()
        ]

    def insert_modified_collectionfields_into_db(
        self, modified_collectionfields: Iterable[str], position: Position
    ):
        # insert into db, updating all existing fields with position, returning ids
        arguments = []
        for collectionfield in modified_collectionfields:
            if len(collectionfield) > COLLECTIONFIELD_MAX_LEN:
                raise InvalidFormat(
                    f"Collection field {collectionfield} is too long (max: {COLLECTIONFIELD_MAX_LEN})"
                )
            arguments.append(
                (
                    collectionfield,
                    position,
                )
            )

        statement = dedent(
            """\
            insert into collectionfields (collectionfield, position) values %s
            on conflict(collectionfield) do update set position=excluded.position
            returning id"""
        )
        return self.connection.query_list_of_single_values(
            statement, arguments, use_execute_values=True
        )

    def connect_events_and_collection_fields(
        self,
        event_ids: list[int],
        collectionfield_ids: list[int],
        event_indices_order: Iterable[list[int]],
    ):
        arguments: list[tuple[int, int]] = []
        for collectionfield_id, event_indices in zip(
            collectionfield_ids, event_indices_order
        ):
            arguments.extend(
                (
                    event_ids[event_index],
                    collectionfield_id,
                )
                for event_index in event_indices
            )

        statement = "insert into events_to_collectionfields (event_id, collectionfield_id) values %s"
        self.connection.execute(statement, arguments, use_execute_values=True)

    def json(self, data):
        return self.connection.to_json(data)

    def reserve_next_ids(self, collection: str, amount: int) -> list[Id]:
        if amount <= 0:
            raise InvalidFormat(f"amount must be >= 1, not {amount}")
        if len(collection) > COLLECTION_MAX_LEN or not collection:
            raise InvalidFormat(
                f"collection length must be between 1 and {COLLECTION_MAX_LEN}"
            )

        statement = dedent(
            """\
            insert into id_sequences (collection, id) values (%s, %s)
            on conflict(collection) do update
            set id=id_sequences.id + excluded.id - 1 returning id;"""
        )
        arguments = [collection, amount + 1]
        new_max_id = self.connection.query_single_value(statement, arguments)

        return list(range(new_max_id - amount, new_max_id))

    def delete_history_information(self) -> None:
        self.connection.execute("UPDATE positions SET information = NULL;", [])

    def truncate_db(self) -> None:
        for table in ALL_TABLES:
            self.connection.execute(f"DELETE FROM {table} CASCADE;", [])
        # restart sequences manually to provide a clean db
        for seq in ("positions_position", "events_id", "collectionfields_id"):
            self.connection.execute(f"ALTER SEQUENCE {seq}_seq RESTART WITH 1;", [])
