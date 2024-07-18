from typing import ContextManager, Protocol

from openslides_backend.datastore.shared.di import service_interface
from openslides_backend.datastore.writer.core.write_request import BaseRequestEvent
from openslides_backend.shared.patterns import Field, FullQualifiedId, Id, Position
from openslides_backend.shared.typing import JSON, Model


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
    ) -> tuple[Position, dict[FullQualifiedId, dict[Field, JSON]]]:
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

    def write_model_updates_without_events(
        self, models: dict[FullQualifiedId, Model]
    ) -> None:
        """For writing directly to models-table used for action_workers and import_previews"""

    def write_model_deletes_without_events(self, fqids: list[FullQualifiedId]) -> None:
        """For deleting directly to models-table used for action_workers and import_previews"""
