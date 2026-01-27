from datastore.migrations import BaseModelMigration
from datastore.writer.core.write_request import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    This migration removes the ids of non-existant or deleted meeting_users from group/meeting_user_ids
    """

    target_migration_index = 78

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        all_existing_meeting_user_ids = set(
            self.reader.get_all("meeting_user", ["group_ids"])
        )
        all_existing_groups = self.reader.get_all("group", ["meeting_user_ids"])
        events: list[BaseRequestEvent] = []
        for id_, data in all_existing_groups.items():
            if remove_meeting_user_ids := set(
                data.get("meeting_user_ids") or []
            ).difference(all_existing_meeting_user_ids):
                events.append(
                    RequestUpdateEvent(
                        fqid=fqid_from_collection_and_id("group", id_),
                        fields={},
                        list_fields={
                            "remove": {
                                "meeting_user_ids": list(remove_meeting_user_ids)
                            }
                        },
                    )
                )
        return events
