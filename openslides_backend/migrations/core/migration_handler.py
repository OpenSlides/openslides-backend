from enum import Enum
from textwrap import dedent
from typing import Any, Protocol

from openslides_backend.datastore.shared.di import service_as_factory, service_interface
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.datastore.shared.util import InvalidDatastoreState
from openslides_backend.migrations.core.base_migrations.base_event_migration import (
    BaseEventMigration,
)
from openslides_backend.migrations.core.migraters import (
    EventMigraterImplementationMemory,
    ModelMigraterImplementationMemory,
)
from openslides_backend.shared.patterns import (
    KEYSEPARATOR,
    META_DELETED,
    FullQualifiedId,
    strip_reserved_fields,
)
from openslides_backend.shared.typing import Model

from .base_migrations.base_migration import BaseMigration
from .exceptions import MigrationSetupException, MismatchingMigrationIndicesException
from .migraters.migrater import EventMigrater, ModelMigrater
from .migration_keyframes import DatabaseMigrationKeyframeModifier
from .migration_logger import MigrationLogger


class MigrationState(str, Enum):
    NO_MIGRATION_REQUIRED = "no_migration_required"
    FINALIZATION_REQUIRED = "finalization_required"
    MIGRATION_REQUIRED = "migration_required"


@service_interface
class MigrationHandler(Protocol):
    def register_migrations(self, *migrations: type[BaseMigration]) -> None:
        """
        Provide the class objects of all migrations to run. It is checked, that they
        have the right target_migration_index set.
        """

    def migrate(self) -> None:
        """
        Run migrations. They are not finalized, so additional migrations (and positions)
        can be executed later on.
        """

    def finalize(self) -> None:
        """
        Run migrations and finalize them.
        """

    def reset(self) -> None:
        """
        Remove all not-finalized migration data. `migrate` and `reset` in combination
        is some kind of dry-run of the migrations.
        """

    def delete_collectionfield_aux_tables(self) -> None:
        """
        Clears the collectionfield tables.
        """

    def get_stats(self) -> dict[str, Any]:
        """
        Returns a dict with some useful stats about the migration state.
        """

    def print_stats(self) -> None:
        """
        Prints the dict returned by `get_stats` in a readable way.
        """


@service_as_factory
class MigrationHandlerImplementation(MigrationHandler):
    read_database: ReadDatabase
    connection: ConnectionHandler
    event_migrater: EventMigrater
    model_migrater: ModelMigrater
    logger: MigrationLogger
    target_migration_index: int
    last_event_migration_target_index: int

    def __init__(self) -> None:
        self.migrations_by_target_migration_index: dict[int, BaseMigration] = {}
        self.target_migration_index = 1
        self.last_event_migration_target_index = 1

    def register_migrations(self, *migrations: type[BaseMigration]) -> None:
        if self.migrations_by_target_migration_index:
            raise MigrationSetupException("Already registered some migrations!")

        _migrations = [migration() for migration in migrations]  # instantiate
        _migrations.sort(key=lambda x: x.target_migration_index)
        for i, migration in enumerate(_migrations):
            if migration.target_migration_index != i + 2:
                raise MigrationSetupException(
                    "target_migration_index: Migrations are not numbered sequentially "
                    + f"beginning at 2. Found {migration.name} at position {i+1} and "
                    + f"target_migration_index {migration.target_migration_index}, "
                    + f"expected migration index {i+2}"
                )
            if isinstance(migration, BaseEventMigration):
                if (
                    self.last_event_migration_target_index
                    < migration.target_migration_index - 1
                ):
                    raise MigrationSetupException(
                        f"All migrations with target_migration_index > {self.last_event_migration_target_index} "
                        + f"must be model migrations. Invalid event migration: {migration.name}."
                    )
                self.last_event_migration_target_index = (
                    migration.target_migration_index
                )
            self.migrations_by_target_migration_index[
                migration.target_migration_index
            ] = migration
        self.target_migration_index = len(_migrations) + 1

        self.event_migrater.init(
            self.last_event_migration_target_index,
            self.migrations_by_target_migration_index,
        )
        self.model_migrater.init(
            self.target_migration_index,
            self.migrations_by_target_migration_index,
        )

    def migrate(self) -> None:
        self.logger.info("Running migrations.")
        if self.run_checks():
            return
        state = self.get_migration_state()
        if state == MigrationState.MIGRATION_REQUIRED:
            self.event_migrater.migrate()
        if state != MigrationState.NO_MIGRATION_REQUIRED:
            self.logger.info("Done. Finalizing is still needed.")

    def get_migration_state(self, verbose: bool = True) -> MigrationState:
        def log(message: str) -> None:
            if verbose:
                self.logger.info(message)

        with self.connection.get_connection_context():
            current_migration_index = self.read_database.get_current_migration_index()
            count_positions = (
                self.connection.query_single_value("select count(*) from positions", [])
                or 0
            )
            min_mi_migration_positions = (
                self.connection.query_single_value(
                    "select min(migration_index) from migration_positions", []
                )
                or current_migration_index
            )
            count_migration_positions = (
                self.connection.query_single_value(
                    "select count(*) from migration_positions", []
                )
                or 0
            )

        # Event migration state
        state = MigrationState.NO_MIGRATION_REQUIRED
        if current_migration_index >= self.last_event_migration_target_index:
            log("No event migrations to apply.")
        elif (
            min_mi_migration_positions == self.last_event_migration_target_index
            and count_positions == count_migration_positions
        ) or current_migration_index == -1:
            log("No event migrations to apply, but finalizing is still needed.")
            state = MigrationState.FINALIZATION_REQUIRED
        else:
            cnt = self.last_event_migration_target_index - min_mi_migration_positions
            log(f"{cnt} event migration{'s' if cnt != 1 else ''} to apply.")
            state = MigrationState.MIGRATION_REQUIRED

        # Model migration state
        start_model_migration_index = max(
            current_migration_index, self.last_event_migration_target_index
        )
        if (
            current_migration_index > -1
            and start_model_migration_index < self.target_migration_index
        ):
            cnt = self.target_migration_index - start_model_migration_index
            log(f"{cnt} model migration{'s' if cnt != 1 else ''} to apply.")
            if state == MigrationState.NO_MIGRATION_REQUIRED:
                state = MigrationState.FINALIZATION_REQUIRED
        else:
            log("No model migrations to apply.")

        log(f"Current migration index: {current_migration_index}")
        return state

    def run_checks(self) -> bool:
        with self.connection.get_connection_context():
            if self.check_datastore_empty():
                return True

            self.assert_valid_migration_index()

            if self.check_for_latest():
                return True
        return False

    def check_datastore_empty(self) -> bool:
        if self.read_database.is_empty():
            self.logger.info("Datastore is empty, nothing to do.")
            return True
        return False

    def assert_valid_migration_index(self) -> None:
        # assert consistent migration index
        try:
            max_db_mi = self.read_database.get_current_migration_index()
        except InvalidDatastoreState as e:
            raise MismatchingMigrationIndicesException(str(e))

        max_migrations_mi = (
            self.connection.query_single_value(
                "select max(migration_index) from migration_positions", []
            )
            or 1
        )
        datastore_max_migration_index = max(max_db_mi, max_migrations_mi)

        if datastore_max_migration_index > self.target_migration_index:
            raise MismatchingMigrationIndicesException(
                "The datastore has a higher migration index "
                + f"({datastore_max_migration_index}) than the registered"
                + f" migrations ({self.target_migration_index})"
            )

    def check_for_latest(self) -> bool:
        min_migration_index = (
            self.connection.query_single_value(
                "select min(migration_index) from positions", []
            )
            or 1
        )
        if min_migration_index == -1:
            self.logger.info("The datastore has a migration index of -1.")
            self._update_migration_index()
            self.connection.execute("delete from migration_events", [])
            self.connection.execute("delete from migration_positions", [])
            self.connection.execute("delete from migration_keyframes", [])
            self.connection.execute("delete from migration_keyframe_models", [])

            return True
        return False

    def finalize(self) -> None:
        self.logger.info("Finalize migrations.")
        if self.run_checks():
            self.delete_collectionfield_aux_tables()
            return
        state = self.get_migration_state()
        if state == MigrationState.NO_MIGRATION_REQUIRED:
            return
        elif state == MigrationState.MIGRATION_REQUIRED:
            self.event_migrater.migrate()

        with self.connection.get_connection_context():
            current_mi = self.read_database.get_current_migration_index()

        if current_mi < self.last_event_migration_target_index:
            self.delete_collectionfield_aux_tables()

            self.logger.info("Calculate helper tables...")
            with self.connection.get_connection_context():
                self.fill_models_aux_tables()
                self.fill_id_sequences_table()

            self._delete_migration_keyframes()

            self.logger.info("Swap events and migration_events tables...")
            with self.connection.get_connection_context():
                self.connection.execute("alter table events rename to events_swap", [])
                self.connection.execute(
                    "alter table migration_events rename to events", []
                )
                self.connection.execute(
                    "alter table events_swap rename to migration_events", []
                )
            with self.connection.get_connection_context():
                self._update_migration_index(self.last_event_migration_target_index)

            self._clean_migration_data()

        if self.last_event_migration_target_index < self.target_migration_index:
            self.model_migrater.migrate()
            self.delete_collectionfield_aux_tables()
            with self.connection.get_connection_context():
                self._update_migration_index()
            self.logger.info("Done.")

    def reset(self) -> None:
        self.logger.info("Reset migrations.")
        with self.connection.get_connection_context():
            if self.check_datastore_empty():
                return

            self.assert_valid_migration_index()

        self._delete_migration_keyframes()
        self._clean_migration_data()

    def _update_migration_index(
        self, target_migration_index: int | None = None
    ) -> None:
        if target_migration_index is None:
            target_migration_index = self.target_migration_index
        self.logger.info(f"Set the new migration index to {target_migration_index}...")
        self.connection.execute(
            "update positions set migration_index=%s",
            [target_migration_index],
        )

    def _delete_migration_keyframes(self) -> None:
        self.logger.info("Deleting all migration keyframes...")
        with self.connection.get_connection_context():
            self.connection.execute("delete from migration_keyframes", [])
            self.connection.execute("delete from migration_keyframe_models", [])

    def _clean_migration_data(self) -> None:
        self.logger.info("Clean up migration data...")
        with self.connection.get_connection_context():
            self.connection.execute("delete from migration_positions", [])
            self.connection.execute("delete from migration_events", [])
            sequence = self.connection.query_single_value(
                "select pg_get_serial_sequence('migration_events', 'id');", []
            )
            self.connection.execute(f"alter sequence {sequence} restart with 1", [])

    def delete_collectionfield_aux_tables(self) -> None:
        self.logger.info("Cleaning collectionfield helper tables...")
        with self.connection.get_connection_context():
            self.connection.execute("delete from events_to_collectionfields", [])
            self.connection.execute("delete from collectionfields", [])

    def fill_models_aux_tables(self) -> None:
        # Use the DatabaseMigrationKeyframeModifier to copy all models into `models`
        max_position = self.connection.query_single_value(
            "select max(position) from positions", []
        )
        keyframe_id = DatabaseMigrationKeyframeModifier.get_keyframe_id(
            self.connection, max_position, self.last_event_migration_target_index
        )
        self.connection.execute("delete from models", [])

        self.connection.execute(
            """insert into models (fqid, data, deleted) select fqid, data, deleted
            from migration_keyframe_models where keyframe_id=%s""",
            [keyframe_id],
        )

    def fill_id_sequences_table(self) -> None:
        """Rebuild the `id_sequences` table from the models in `models`."""
        self.connection.execute("delete from id_sequences", [])
        self.connection.execute(
            """\
            insert into id_sequences (collection, id)
            select split_part(fqid, %s, 1) as collection,
            max((split_part(fqid, %s, 2))::int) + 1 as id
            from models group by collection
            """,
            [KEYSEPARATOR] * 2,
        )

    def get_stats(self) -> dict[str, Any]:  # pragma: no cover
        def count(table: str) -> int:
            return (
                self.connection.query_single_value(f"select count(*) from {table}", [])
                or 0
            )

        with self.connection.get_connection_context():
            count_positions = count("positions")
            count_events = count("events")
            current_migration_index = self.read_database.get_current_migration_index()

            count_migration_positions = count("migration_positions")
            count_migration_positions_full = (
                self.connection.query_single_value(
                    "select count(*) from migration_positions where migration_index=%s",
                    [self.target_migration_index],
                )
                or 0
            )
            count_migration_positions_partial = (
                count_migration_positions - count_migration_positions_full
            )

        state = self.get_migration_state(verbose=False)

        return {
            "status": state,
            "current_migration_index": current_migration_index,
            "target_migration_index": self.target_migration_index,
            "positions": count_positions,
            "events": count_events,
            "partially_migrated_positions": count_migration_positions_partial,
            "fully_migrated_positions": count_migration_positions_full,
        }

    def print_stats(self) -> None:  # pragma: no cover
        stats = self.get_stats()
        if stats["current_migration_index"] == stats["target_migration_index"]:
            action = "The datastore is up-to-date"
        else:
            action = "Migration/Finalization is needed"
        if stats["status"] == MigrationState.NO_MIGRATION_REQUIRED:
            migration_action = "No action needed"
        elif stats["status"] == MigrationState.MIGRATION_REQUIRED:
            migration_action = "Migration and finalization needed"
        elif stats["status"] == MigrationState.FINALIZATION_REQUIRED:
            migration_action = "Finalization needed"
        self.logger.info(
            dedent(
                f"""\
            - Registered migrations for migration index {self.target_migration_index}
            - Datastore has {stats['positions']} positions with {stats['events']} events
            - The positions have a migration index of {stats['current_migration_index']}
            -> {action}
            - There are {stats['fully_migrated_positions']} fully migrated positions and
            {stats['partially_migrated_positions']} partially migrated ones
            -> {migration_action}
            - {stats['positions'] - stats['fully_migrated_positions']} positions have to be migrated (including
            partially migrated ones)\
            """
            )
        )


class MigrationHandlerImplementationMemory(MigrationHandlerImplementation):
    """
    All migrations are made in-memory only for the import of meetings.
    """

    event_migrater: EventMigraterImplementationMemory
    model_migrater: ModelMigraterImplementationMemory

    def set_import_data(
        self, models: dict[FullQualifiedId, Model], start_migration_index: int
    ) -> None:
        for model in models.values():
            model[META_DELETED] = False
        self.models = models
        self.start_migration_index = start_migration_index
        indices = (self.last_event_migration_target_index, start_migration_index)
        self.event_migrater.start_migration_index = min(indices)
        self.model_migrater.start_migration_index = max(indices)

    def finalize(self) -> None:
        if (
            self.start_migration_index < 1
            or self.start_migration_index > self.target_migration_index
        ):
            raise MismatchingMigrationIndicesException(
                "The migration index of import data is invalid: "
                + f"Given migration index of import data: {self.start_migration_index}, "
                + f"current backend migration index: {self.target_migration_index}"
            )
        self.logger.info("Finalize in memory migrations.")
        for migrater in (self.event_migrater, self.model_migrater):
            if migrater.start_migration_index < migrater.target_migration_index:
                migrater.models = self.models
                migrater.migrate()
                self.models = migrater.get_migrated_models()
        self.logger.info("Finalize in memory migrations ready.")

    def get_migrated_models(self) -> dict[FullQualifiedId, Model]:
        for model in self.models.values():
            strip_reserved_fields(model)
        return self.models
