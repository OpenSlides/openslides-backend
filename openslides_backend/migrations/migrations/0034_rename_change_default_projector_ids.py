from typing import Any, Dict, List, Optional, cast

from datastore.migrations import (
    BaseEvent,
    BaseMigration,
    CreateEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_from_fqid

from openslides_backend.models.models import Meeting


class Migration(BaseMigration):
    """
    This migration renames default_projector_$.._id into
      default_projector_$.._ids and changes value to list.
    """

    target_migration_index = 35
    collection = "meeting"

    def modify(self, object: Dict[str, Any]) -> None:
        if "default_projector_$_id" in object:
            object["default_projector_$_ids"] = object["default_projector_$_id"]
            del object["default_projector_$_id"]
        for name in cast(List[str], Meeting.default_projector__ids.replacement_enum):
            old_field = f"default_projector_${name}_id"
            new_field = f"default_projector_${name}_ids"
            if old_field in object:
                object[new_field] = [object[old_field]]
                del object[old_field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection != self.collection:
            return None

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.modify(event.data)

        elif isinstance(event, DeleteFieldsEvent):
            for field in (
                "default_projector_$_id",
                *[
                    f"default_projector_${name}_id"
                    for name in cast(
                        List[str], Meeting.default_projector__ids.replacement_enum
                    )
                ],
            ):

                if field in event.data:
                    event.data.remove(field)
                    event.data.append(field + "s")

        elif isinstance(event, ListUpdateEvent):
            self.modify(event.add)
            self.modify(event.remove)

        return [event]
