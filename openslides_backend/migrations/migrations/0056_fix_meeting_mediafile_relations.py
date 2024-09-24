from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    This migration fixes some fields that were not rewritten in migration 54
    """

    target_migration_index = 57
    group_fields = [
        "access_group_ids",
        "inherited_access_group_ids",
    ]

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        groups_to_access_groups: dict[int, dict[str, list[int]]] = {
            group["id"]: {
                "meeting_mediafile_" + field: [] for field in self.group_fields
            }
            for group in self.reader.get_all("group", ["id"]).values()
        }
        for mmediafile in self.reader.get_all(
            "meeting_mediafile", ["id", *self.group_fields]
        ).values():
            for field in self.group_fields:
                for group_id in mmediafile.get(field, []) or []:
                    groups_to_access_groups[group_id][
                        "meeting_mediafile_" + field
                    ].append(mmediafile["id"])
        return [
            RequestUpdateEvent(
                fqid_from_collection_and_id("group", group_id),
                {
                    **{"mediafile_" + field: None for field in self.group_fields},
                    **access_groups,
                },
            )
            for group_id, access_groups in groups_to_access_groups.items()
        ]
