from dataclasses import dataclass, field

from openslides_backend.shared.typing import HistoryInformation

from .collection_field_lock import CollectionFieldLock
from .event import Event


@dataclass
class WriteRequest:
    """
    Write request element that can be sent to the datastore.
    """

    events: list[Event]
    information: HistoryInformation | None = None
    user_id: int | None = None


@dataclass
class WriteRequestWithMigrationIndex(WriteRequest):
    """
    Write request element with a migration index.
    """

    migration_index: int | None = None
