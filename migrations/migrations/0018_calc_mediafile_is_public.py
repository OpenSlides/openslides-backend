from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from helper.helper import calculate_inherited_groups_helper

from datastore.migrations import (
    BaseEvent,
    BaseMigration,
    CreateEvent,
    DeleteEvent,
    ListUpdateEvent,
    RestoreEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_and_id_from_fqid, id_from_fqid


class Migration(BaseMigration):
    """
    This migration should check for complete mediafile fields "is_public" and
    "inherited_access_group_ids" and should fill them.
    The error-prone action was mediafile.upload, so we check expecially
    mediafile create-events with is_directory = False and
    assert other events.
    """

    target_migration_index = 19

    def position_init(self) -> None:
        self.creates: List[CreateEvent] = []
        self.updates: List[UpdateEvent] = []

    def migrate_event(self, event: BaseEvent) -> Optional[List[BaseEvent]]:
        collection, _ = collection_and_id_from_fqid(event.fqid)

        if (
            collection != "mediafile"
            or not isinstance(event, (CreateEvent, UpdateEvent))
            or type(event.data.get("is_public")) is bool
        ):
            return None

        # mediafile: Optional[Dict[str, Any]]
        if isinstance(event, CreateEvent):
            assert (
                event.data.get("is_directory") is not True
            ), "media-directory without is_public"
            self.creates.append(event)
        else:
            self.updates.append(event)
        return None
        # mediafile = self.new_accessor.get_model_ignore_deleted(f"user/{mediafile_id}")[0]

    def get_additional_events(self) -> Optional[List[BaseEvent]]:
        events: List[BaseEvent] = []

        for event in self.creates:
            mediafile_id = id_from_fqid(event.fqid)
            parent_is_public: Optional[bool] = None
            parent_inherited_access_group_ids: Optional[List[int]] = []

            if parent_id := event.data.get("parent_id"):
                parent = self.new_accessor.get_model_ignore_deleted(
                    f"mediafile/{parent_id}"
                )[0]
                parent_is_public = cast(bool, parent.get("is_public"))
                parent_inherited_access_group_ids = cast(List, parent.get(
                    "inherited_access_group_ids"
                ))
            update_event = UpdateEvent(event.fqid, {})
            (
                update_event.data["is_public"],
                update_event.data["inherited_access_group_ids"],
            ) = calculate_inherited_groups_helper(
                event.data.get("access_group_ids"),
                parent_is_public,
                parent_inherited_access_group_ids,
            )
            events.append(update_event)

        return events
