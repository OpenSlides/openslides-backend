from typing import Any

from openslides_backend.migrations import RenameFieldMigration
from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(RenameFieldMigration):
    """
    This migration renames:
      mediafile/meeting_id
    into:
      mediafile/owner_id
    and modify it to generic field.
    """

    target_migration_index = 23

    collection = "mediafile"
    old_field = "meeting_id"
    new_field = "owner_id"

    def modify(self, object: dict[str, Any]) -> None:
        if self.old_field in object:
            object[self.new_field] = fqid_from_collection_and_id(
                "meeting", object[self.old_field]
            )
            del object[self.old_field]
