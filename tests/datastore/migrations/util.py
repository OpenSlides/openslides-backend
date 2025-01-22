from unittest.mock import MagicMock

from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    BaseModelMigration,
)
from openslides_backend.shared.interfaces.write_request import BaseRequestEvent


class DummyEventMigration(BaseEventMigration):
    target_migration_index = -1


class DummyModelMigration(BaseModelMigration):
    target_migration_index = -1


class LogMock(MagicMock):
    @property
    def output(self) -> tuple[str, ...]:
        return tuple(c[0][0] for c in self.call_args_list)


def get_noop_event_migration(target_migration_index: int | None):
    class NoopMigration(DummyEventMigration):
        def __init__(self):
            if target_migration_index is not None:
                self.target_migration_index = target_migration_index
            super().__init__()

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> list[BaseEvent] | None:
            return None

    return NoopMigration


def get_lambda_event_migration(fn, target_migration_index=2):
    class LambdaMigration(DummyEventMigration):
        def __init__(self):
            self.target_migration_index = target_migration_index
            super().__init__()

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> list[BaseEvent] | None:
            return fn(event)

    return LambdaMigration


def get_noop_model_migration(target_migration_index: int | None):
    class NoopMigration(DummyModelMigration):
        def __init__(self):
            if target_migration_index is not None:
                self.target_migration_index = target_migration_index
            super().__init__()

    return NoopMigration


def get_lambda_model_migration(fn, target_migration_index=2):
    class LambdaMigration(DummyModelMigration):
        def __init__(self):
            self.target_migration_index = target_migration_index
            super().__init__()

        def migrate_models(self) -> list[BaseRequestEvent] | None:
            return fn(self)

    return LambdaMigration
