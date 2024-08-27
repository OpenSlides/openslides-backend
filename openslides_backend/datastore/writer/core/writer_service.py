import copy
import threading
from collections import defaultdict

from openslides_backend.datastore.shared.di import service_as_factory
from openslides_backend.datastore.shared.postgresql_backend import retry_on_db_failure
from openslides_backend.datastore.shared.services import (
    EnvironmentService,
    ReadDatabase,
)
from openslides_backend.datastore.shared.util import DatastoreNotEmpty, logger
from openslides_backend.shared.otel import make_span
from openslides_backend.shared.patterns import META_DELETED, Field, FullQualifiedId
from openslides_backend.shared.typing import JSON

from .database import Database
from .write_request import BaseRequestEvent, RequestDeleteEvent, WriteRequest


@service_as_factory
class WriterService:
    _lock = threading.Lock()

    database: Database
    read_database: ReadDatabase
    env: EnvironmentService

    @retry_on_db_failure
    def write(
        self,
        write_requests: list[WriteRequest],
    ) -> None:
        with make_span(self.env, "write request"):
            self.write_requests = write_requests

            with self._lock:
                with self.database.get_context():
                    for write_request in self.write_requests:
                        self.write_with_database_context(write_request)

            self.print_stats()
            self.print_summary()

    def print_stats(self) -> None:
        stats: dict[str, int] = defaultdict(int)
        for write_request in self.write_requests:
            for event in write_request.events:
                stats[self.get_request_name(event)] += 1
        stats_string = ", ".join(f"{cnt} {name}" for name, cnt in stats.items())
        logger.info(f"Events executed ({stats_string})")

    def print_summary(self) -> None:
        summary: dict[str, set[str]] = defaultdict(set)  # event type <-> set[fqid]
        for write_request in self.write_requests:
            for event in write_request.events:
                summary[self.get_request_name(event)].add(event.fqid)
        logger.info(
            "\n".join(
                f"{eventType}: {list(fqids)}" for eventType, fqids in summary.items()
            )
        )

    def get_request_name(self, event: BaseRequestEvent) -> str:
        return type(event).__name__.replace("Request", "").replace("Event", "").upper()

    def write_with_database_context(
        self, write_request: WriteRequest
    ) -> tuple[int, dict[FullQualifiedId, dict[Field, JSON]]]:
        with make_span(self.env, "write with database context"):
            # get migration index
            if write_request.migration_index is None:
                migration_index = self.read_database.get_current_migration_index()
            else:
                if not self.read_database.is_empty():
                    raise DatastoreNotEmpty(
                        f"Passed a migration index of {write_request.migration_index}, but the datastore is not empty."
                    )
                migration_index = write_request.migration_index

            # Insert db events with position data
            information = (
                write_request.information if write_request.information else None
            )
            position, modified_fqfields = self.database.insert_events(
                write_request.events,
                migration_index,
                information,
                write_request.user_id,
            )

            return position, modified_fqfields

    @retry_on_db_failure
    def reserve_ids(self, collection: str, amount: int) -> list[int]:
        with make_span(self.env, "reserve ids"):
            with self.database.get_context():
                ids = self.database.reserve_next_ids(collection, amount)
                logger.info(f"{len(ids)} ids reserved")
                return ids

    @retry_on_db_failure
    def delete_history_information(self) -> None:
        with self.database.get_context():
            self.database.delete_history_information()
            logger.info("History information deleted")

    @retry_on_db_failure
    def write_without_events(
        self,
        write_request: WriteRequest,
    ) -> None:
        """Writes or updates an action_worker- or
        import_preview-object.
        The record will be written to
        the models-table only, because there is no history
        needed and after the action is finished and notified,
        isn't needed anymore.
        """
        self.write_requests = [write_request]

        with make_span(self.env, "write action worker"):
            if isinstance(write_request.events[0], RequestDeleteEvent):
                fqids_to_delete: list[FullQualifiedId] = []
                for event in write_request.events:
                    fqids_to_delete.append(event.fqid)
                with self.database.get_context():
                    self.database.write_model_deletes_without_events(fqids_to_delete)
            else:
                with self.database.get_context():
                    for event in write_request.events:
                        fields_with_delete = copy.deepcopy(event.fields)  # type: ignore
                        fields_with_delete.update({META_DELETED: False})
                        self.database.write_model_updates_without_events(
                            {event.fqid: fields_with_delete}
                        )

        self.print_stats()
        self.print_summary()
