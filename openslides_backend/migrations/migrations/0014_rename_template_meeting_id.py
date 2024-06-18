from typing import Any

from datastore.migrations import RenameFieldMigration


class Migration(RenameFieldMigration):
    """
    This migration renames:
    committee/template_meeting_id
    into
    committee/template_meeting_ids
    and changes the type.
    """

    target_migration_index = 15

    collection = "committee"
    old_field = "template_meeting_id"
    new_field = "template_meeting_ids"

    def modify(self, object: dict[str, Any]) -> None:
        if self.old_field in object:
            object[self.new_field] = (
                [object[self.old_field]] if object[self.old_field] else []
            )
            del object[self.old_field]
