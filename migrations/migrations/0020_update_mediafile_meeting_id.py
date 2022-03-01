from typing import Any, Dict

from datastore.migrations.migrations.rename_field_migration import RenameFieldMigration
from datastore.shared.util import KEYSEPARATOR


class Migration(RenameFieldMigration):
    """
    This migration renames:
      mediafile/meeting_id
    into:
      mediafile/owner_id
    and modify it to generic field.
    """

    target_migration_index = 21

    collection = "mediafile"
    old_field = "meeting_id"
    new_field = "owner_id"

    def modify(self, object: Dict[str, Any]) -> None:
        if self.old_field in object:
            object[self.new_field] = (
                "meeting" + KEYSEPARATOR + str(object[self.old_field])
            )
            del object[self.old_field]
