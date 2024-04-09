from typing import ContextManager, Protocol

from openslides_backend.datastore.shared.di import service_interface
from openslides_backend.datastore.shared.typing import (
    JSON,
    Field,
    Fqid,
    Id,
    Model,
    Position,
)
from openslides_backend.datastore.writer.core.write_request import BaseRequestEvent


@service_interface
class Database(Protocol):
    def get_context(self) -> ContextManager[None]:
        """
        Creates a new context to execute all actions inside
        """

    def insert_events(
        self,
        events: list[BaseRequestEvent],
        migration_index: int,
        information: JSON,
        user_id: int,
    ) -> tuple[Position, dict[Fqid, dict[Field, JSON]]]:
        """
        Inserts the given events. This may raise ModelExists,
        ModelDoesNotExist or ModelNotDeleted. Returns the generated position and
        modified fqfields with values.
        """

    def reserve_next_ids(self, collection: str, amount: int) -> list[Id]:
        """
        Reserves next ids and returns the requested ids as a list.
        May Raises InvalidFormat, is collection is malformed or amount too high
        """

    def delete_history_information(self) -> None:
        """Delete all history information from all positions."""

    def truncate_db(self) -> None:
        """Truncate all tables. Only for dev purposes!"""

    def write_model_updates_without_events(self, models: dict[Fqid, Model]) -> None:
        """For writing directly to models-table used for action_workers and import_previews"""

    def write_model_deletes_without_events(self, fqids: list[Fqid]) -> None:
        """For deleting directly to models-table used for action_workers and import_previews"""
