from typing import Protocol

from openslides_backend.datastore.shared.di import service_interface

from .write_request import WriteRequest


@service_interface
class Writer(Protocol):
    """For detailed interface descriptions, see the docs repo."""

    def write(
        self,
        write_requests: list[WriteRequest],
    ) -> None:
        """Writes into the DB."""

    def reserve_ids(self, collection: str, amount: int) -> list[int]:
        """Gets multiple reserved ids"""

    def delete_history_information(self) -> None:
        """Delete all history information from all positions."""

    def truncate_db(self) -> None:
        """Truncate all tables. Dev mode only"""

    def write_without_events(
        self,
        write_request: WriteRequest,
    ) -> None:
        """Writes or updates an object without events (action_worker or import_preview)"""
