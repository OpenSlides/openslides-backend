from typing import Any, Dict, List, Optional

from datastore.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    ListUpdateEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_from_fqid


class Migration(BaseEventMigration):
    """
    This migration adds ListOfSpeakers.CAN_SEE to a group, if the ListOfSpeakers.CAN_BE_SPEAKER event is present.
    """

    target_migration_index = 42
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

    def modify(self, object: Dict[str, Any]) -> None:
        if "list_of_speakers.can_be_speaker" in object["permissions"]:
            object["permissions"].append("list_of_speakers.can_see")

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection != "group":
            return None

        if (
            isinstance(event, (CreateEvent, UpdateEvent))
            and "permissions" in event.data
        ):
            self.modify(event.data)
        elif isinstance(event, ListUpdateEvent) and "permissions" in event.add:
            self.modify(event.add)
        else:
            return None
        return [event]
