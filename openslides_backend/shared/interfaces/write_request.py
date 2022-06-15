from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .collection_field_lock import CollectionFieldLock
from .event import Event


@dataclass
class WriteRequest:
    """
    Write request element that can be sent to the datastore.
    """

    events: List[Event]
    information: Optional[List[str]] = None
    user_id: Optional[int] = None
    locked_fields: Dict[str, CollectionFieldLock] = field(default_factory=dict)


@dataclass
class WriteRequestWithMigrationIndex(WriteRequest):
    """
    Write request element with a migration index.
    """

    migration_index: Optional[int] = None
