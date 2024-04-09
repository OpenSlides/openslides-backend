from collections.abc import Iterable

from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteFieldsEvent,
    UpdateEvent,
)
from openslides_backend.shared.patterns import (
    collection_from_fqid,
    fqid_from_collection_and_id,
)


class Migration(BaseEventMigration):
    target_migration_index = 38

    def order_events(self, events: list[BaseEvent]) -> Iterable[BaseEvent]:
        """
        We always have to process create events for projections first so that we can filter them out
        correctly when processing the reverse relations.
        """
        create_events = []
        other_events = []
        for event in events:
            collection = collection_from_fqid(event.fqid)
            if event.type == "create":
                if collection == "projection":
                    yield event
                else:
                    create_events.append(event)
            else:
                other_events.append(event)
        yield from create_events
        yield from other_events

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection = collection_from_fqid(event.fqid)
        # remove all projection ids from users
        if collection == "user":
            if isinstance(event, (CreateEvent, UpdateEvent)):
                for field in list(event.data.keys()):
                    if field.startswith("projection_$"):
                        del event.data[field]
            elif isinstance(event, DeleteFieldsEvent):
                event.data = [
                    field
                    for field in event.data
                    if not field.startswith("projection_$")
                ]

        # remove all no longer existing projector ids from meetings
        if collection == "meeting":
            if (
                isinstance(event, (CreateEvent, UpdateEvent))
                and "all_projection_ids" in event.data
            ):
                event.data["all_projection_ids"] = self.filter_projection_ids(
                    event.data["all_projection_ids"]
                )

        # remove all no longer existing projector ids from projectors
        if collection == "projector":
            if isinstance(event, UpdateEvent):
                for field in (
                    "current_projection_ids",
                    "preview_projection_ids",
                    "history_projection_ids",
                ):
                    if field in event.data:
                        event.data[field] = self.filter_projection_ids(
                            event.data[field]
                        )

        # remove all user projections
        if collection == "projection":
            if isinstance(event, CreateEvent):
                data = event.data
            else:
                data, _ = self.old_accessor.get_model_ignore_deleted(event.fqid)
            if data.get("content_object_id"):
                # some imported projections do not have a content object, even though it is required
                content_collection = collection_from_fqid(data["content_object_id"])
                if content_collection == "user":
                    return []

        return [event]

    def filter_projection_ids(self, projection_ids: list[int]) -> list[int]:
        new_projection_ids = []
        for projection_id in projection_ids:
            if self.new_accessor.model_exists(
                fqid_from_collection_and_id("projection", projection_id)
            ):
                new_projection_ids.append(projection_id)
        return new_projection_ids
