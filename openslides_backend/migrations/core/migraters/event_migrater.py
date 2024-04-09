from dataclasses import dataclass
from datetime import datetime

from openslides_backend.datastore.shared.di import service_as_factory
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.datastore.shared.typing import JSON, Position

from ..base_migrations import PositionData
from ..events import BaseEvent, to_event
from ..exceptions import MismatchingMigrationIndicesException
from ..migration_keyframes import (
    DatabaseMigrationKeyframeModifier,
    InitialMigrationKeyframeModifier,
    MigrationKeyframeModifier,
)
from ..migration_logger import MigrationLogger
from .migrater import EventMigrater


@dataclass
class RawPosition:
    position: Position
    migration_index: int
    timestamp: datetime
    user_id: int
    information: JSON

    def to_position_data(self) -> PositionData:
        return PositionData(
            self.position,
            self.timestamp,
            self.user_id,
            self.information,
        )


@service_as_factory
class EventMigraterImplementation(EventMigrater):
    read_database: ReadDatabase
    connection: ConnectionHandler
    logger: MigrationLogger

    def migrate(self) -> None:
        # TODO: paginate and use "client-side cursor". We cannot use a server-side cursor since
        # currently the implementation of self.connection does nto allow nested transactions (=contexts)
        with self.connection.get_connection_context():
            min_position_1 = self.connection.query_single_value(
                "select min(position) from positions where migration_index<%s",
                [self.target_migration_index],
            )
            min_position_2 = self.connection.query_single_value(
                "select min(position) from migration_positions where migration_index<%s",
                [self.target_migration_index],
            )
            if min_position_2 is None:
                min_position_2 = self.connection.query_single_value(
                    """select min(position) from positions where position >
                    (select max(position) from migration_positions)""",
                    [],
                )
            if min_position_2 is not None:
                min_position = max(min_position_1, min_position_2)
            else:
                min_position = min_position_1

            min_mi_positions = (
                self.connection.query_single_value(
                    "select min(migration_index) from positions", []
                )
                or 1
            )
            min_mi_migration_positions = (
                self.connection.query_single_value(
                    "select min(migration_index) from migration_positions", []
                )
                or 1
            )

            positions = self.connection.query(
                "select * from positions where position >= %s order by position asc",
                [min_position],
            )
            _last_position = self.connection.query(
                "select * from positions where position < %s order by position desc limit 1",
                [min_position],
            )
            last_position: RawPosition | None = (
                None if len(_last_position) == 0 else RawPosition(**_last_position[0])
            )
            last_migration_index = (
                None
                if last_position is None
                else self.get_migration_index(last_position)
            )

        if min_mi_positions < 1 or min_mi_migration_positions < 1:
            raise MismatchingMigrationIndicesException(
                "Datastore has an invalid migration index: MI of positions table="
                + f"{min_mi_positions}; MI of migrations_position table="
                + f"{min_mi_migration_positions}"
            )

        for _position in positions:
            position = RawPosition(**_position)

            with self.connection.get_connection_context():
                last_position_value = (
                    0 if last_position is None else last_position.position
                )
                migration_index = self.get_migration_index(position)

                # sanity check: Do not have raising migration indices
                if (
                    last_position is not None
                    and last_migration_index is not None
                    and migration_index > last_migration_index
                ):
                    raise MismatchingMigrationIndicesException(
                        f"Position {position.position} has a higher migration index as it's predecessor "
                        + f"(position {last_position.position})"
                    )

                self.migrate_position(position, migration_index, last_position_value)
                last_position = position
                last_migration_index = migration_index

    def migrate_position(
        self, position: RawPosition, migration_index: int, last_position_value: int
    ) -> None:
        self.logger.info(
            f"Position {position.position} from MI {migration_index} to MI {self.target_migration_index} ..."
        )
        events_from_migration_table = migration_index != position.migration_index
        for (
            source_migration_index,
            target_migration_index,
            migration,
        ) in self.get_migrations(migration_index):
            is_last_migration_index = (
                target_migration_index == self.target_migration_index
            )
            old_accessor, new_accessor = self.get_accessors(
                last_position_value,
                source_migration_index,
                target_migration_index,
                position.position,
                is_last_migration_index,
            )

            if events_from_migration_table:
                _old_events = self.connection.query(
                    "select id, fqid, type, data from migration_events where position=%s order by weight asc",
                    [position.position],
                )
            else:
                _old_events = self.connection.query(
                    "select id, fqid, type, data from events where position=%s order by weight asc",
                    [position.position],
                )
                # after the first event use the migration table
                events_from_migration_table = True
            old_events = [to_event(row) for row in _old_events]
            try:
                new_events = migration.migrate(
                    old_events, old_accessor, new_accessor, position.to_position_data()
                )
            except Exception:
                self.logger.info(
                    f"Migration from MI {source_migration_index} to MI {target_migration_index} failed!"
                )
                raise
            self.write_new_events(new_events, position.position)

            old_accessor.move_to_next_position()
            if is_last_migration_index:
                # the new accessor is only moved, when the position is fully migrated.
                new_accessor.move_to_next_position()

        # set the migration index of this position
        self.connection.execute(
            """insert into migration_positions (position, migration_index) values (%s, %s)
            on conflict(position) do update set migration_index=excluded.migration_index""",
            [position.position, self.target_migration_index],
        )

    def get_migration_index(self, position: RawPosition) -> int:
        return (
            self.connection.query_single_value(
                "select migration_index from migration_positions where position=%s",
                [position.position],
            )
            or position.migration_index
        )

    def get_accessors(
        self,
        last_position_value: Position,
        source_migration_index: int,
        target_migration_index: int,
        position: Position,
        is_last_migration_index: bool,
    ) -> tuple[MigrationKeyframeModifier, MigrationKeyframeModifier]:
        if last_position_value == 0:  # first position to migrate
            old_accessor: MigrationKeyframeModifier = InitialMigrationKeyframeModifier(
                self.connection,
                last_position_value,
                source_migration_index,
                position,
            )
            new_accessor: MigrationKeyframeModifier = InitialMigrationKeyframeModifier(
                self.connection,
                last_position_value,
                target_migration_index,
                position,
            )
            return old_accessor, new_accessor
        else:
            old_accessor = DatabaseMigrationKeyframeModifier(
                self.connection,
                last_position_value,
                source_migration_index,
                position,
                True,
            )
            new_accessor = DatabaseMigrationKeyframeModifier(
                self.connection,
                last_position_value,
                target_migration_index,
                position,
                is_last_migration_index,
            )
            return old_accessor, new_accessor

    def write_new_events(self, new_events: list[BaseEvent], position: Position) -> None:
        """
        Performs a diff: Update (overwrite) existing events for this position. Delete
        all events, that there are too many, create new events, if there are more new
        events than old events.
        """

        old_event_ids = self.connection.query_list_of_single_values(
            "select id from migration_events where position=%s", [position]
        )

        # simple overwrite the old events with the new ones and delete old
        # events, if there are less new events.
        for i in range(min(len(old_event_ids), len(new_events))):
            # update event old_event_ids[i] to new_events[i] and set weight to i+1
            statement = "update migration_events set fqid=%s, type=%s, data=%s, weight=%s where id=%s"
            new_event = new_events[i]
            arguments = [
                new_event.fqid,
                new_event.type,
                self.connection.to_json(new_event.get_data()),
                i + 1,
                old_event_ids[i],
            ]
            self.connection.execute(statement, arguments)

        if len(old_event_ids) > len(new_events):
            # delete all ids from old_event_ids[len(new_events):] in the database
            statement = "delete from migration_events where id in %s"
            argument = tuple(old_event_ids[len(new_events) :])
            self.connection.execute(statement, [argument])

        if len(new_events) > len(old_event_ids):
            # There are new events, that must be created.
            # TODO: This can be a single insert statement.
            for i in range(len(old_event_ids), len(new_events)):
                # create new event for this position and set weight to i+1
                statement = """
                    insert into migration_events (position, fqid, type, data, weight)
                    values (%s, %s, %s, %s, %s)"""
                new_event = new_events[i]
                arguments = [
                    position,
                    new_event.fqid,
                    new_event.type,
                    self.connection.to_json(new_event.get_data()),
                    i + 1,
                ]
                self.connection.execute(statement, arguments)
