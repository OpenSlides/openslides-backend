from typing import Any, Dict, List, Optional

from datastore.migrations import (
    BaseEvent,
    BaseMigration,
    CreateEvent,
    DeleteFieldsEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_from_fqid


class Migration(BaseMigration):
    """
    This migration removes the fields url_name and users_pdf_url from meeting.
    """

    target_migration_index = 17

    collection = "meeting"
    fields = ("url_name", "users_pdf_url")

    def remove_field(self, object: Dict[str, Any]) -> None:
        for field in self.fields:
            if field in object:
                del object[field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection != self.collection:
            return None

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.remove_field(event.data)

        elif isinstance(event, DeleteFieldsEvent):
            for field in self.fields:
                if field in event.data:
                    event.data.remove(field)

        return [event]
