from typing import Any

from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)
from openslides_backend.shared.patterns import collection_from_fqid


class Migration(BaseEventMigration):
    """
    This migration renames a field from old_name to new_name for one collection.
    """

    target_migration_index = 41
    collection_to_old_and_new_field = {
        "user": [("last_email_send", "last_email_sent")],
        "meeting": [
            (
                "motion_poll_default_100_percent_base",
                "motion_poll_default_onehundred_percent_base",
            ),
            (
                "assignment_poll_default_100_percent_base",
                "assignment_poll_default_onehundred_percent_base",
            ),
            ("poll_default_100_percent_base", "poll_default_onehundred_percent_base"),
        ],
    }

    def modify(self, object: dict[str, Any], fields: list[tuple[str, str]]) -> None:
        for old_field, new_field in fields:
            if old_field in object:
                object[new_field] = object[old_field]
                del object[old_field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection = collection_from_fqid(event.fqid)
        if collection not in self.collection_to_old_and_new_field:
            return None

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.modify(event.data, self.collection_to_old_and_new_field[collection])

        elif isinstance(event, DeleteFieldsEvent):
            for old_field, new_field in self.collection_to_old_and_new_field[
                collection
            ]:
                if old_field in event.data:
                    event.data.remove(old_field)
                    event.data.append(new_field)

        elif isinstance(event, ListUpdateEvent):
            self.modify(event.add, self.collection_to_old_and_new_field[collection])
            self.modify(event.remove, self.collection_to_old_and_new_field[collection])

        return [event]
