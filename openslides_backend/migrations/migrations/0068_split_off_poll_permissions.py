from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    This migration splits motion.can_manage_polls away from motion.can_manage
    and gives the new permission assignment.can_manage_polls to any group with assignment.can_manage.
    """

    target_migration_index = 69

    perms = ["motion.can_manage", "assignment.can_manage"]

    def migrate_models(self) -> list[BaseRequestEvent]:
        groups = self.reader.get_all("group", ["permissions"])
        events: list[BaseRequestEvent] = [
            RequestUpdateEvent(
                fqid_from_collection_and_id("group", id_),
                {},
                {
                    "add": {
                        "permissions": (
                            ["motion.can_manage_polls"]
                            if "assignment.can_manage" not in group["permissions"]
                            else (
                                ["assignment.can_manage_polls"]
                                if "motion.can_manage" not in group["permissions"]
                                else [
                                    "assignment.can_manage_polls",
                                    "motion.can_manage_polls",
                                ]
                            )
                        )
                    }
                },
            )
            for id_, group in groups.items()
            if any(perm in group.get("permissions", []) for perm in self.perms)
        ]

        return events
