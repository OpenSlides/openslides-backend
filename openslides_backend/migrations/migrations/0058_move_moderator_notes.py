from collections import defaultdict

from datastore.migrations import BaseModelMigration
from datastore.reader.core import GetManyRequestPart
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import (
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
)


class Migration(BaseModelMigration):
    """
    This migration moves all set moderator notes to the related models list_of_speakers.
    It also gives any group which had the permissions agenda_item.can_see_moderator_notes or agenda_item.can_manage_moderator_notes
    the permission list_of_speakers.can_see_moderator_notes or list_of_speakers.can_manage_moderator_notes instead.
    """

    target_migration_index = 59

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        agenda_items = self.reader.get_all(
            "agenda_item", ["id", "content_object_id", "moderator_notes"]
        )
        events: list[BaseRequestEvent] = [
            RequestUpdateEvent(
                fqid_from_collection_and_id("agenda_item", agenda_item["id"]),
                {"moderator_notes": None},
            )
            for agenda_item in agenda_items.values()
            if (mod_note := agenda_item.get("moderator_notes"))
        ]
        if len(events):
            content_object_id_to_mod_note: dict[tuple[str, int], str] = {
                collection_and_id_from_fqid(agenda_item["content_object_id"]): mod_note
                for agenda_item in agenda_items.values()
                if (mod_note := agenda_item.get("moderator_notes"))
            }
            content_object_collection_to_ids: dict[str, list[int]] = defaultdict(list)
            for co_collection, co_id in content_object_id_to_mod_note.keys():
                content_object_collection_to_ids[co_collection].append(co_id)
            content_objects = self.reader.get_many(
                [
                    GetManyRequestPart(co_collection, co_ids, ["list_of_speakers_id"])
                    for co_collection, co_ids in content_object_collection_to_ids.items()
                ]
            )
            events.extend(
                [
                    RequestUpdateEvent(
                        fqid_from_collection_and_id(
                            "list_of_speakers",
                            content_objects[co_collection][co_id][
                                "list_of_speakers_id"
                            ],
                        ),
                        {"moderator_notes": mod_note},
                    )
                    for (
                        co_collection,
                        co_id,
                    ), mod_note in content_object_id_to_mod_note.items()
                ]
            )
        groups = self.reader.get_all("group", ["id", "permissions"])
        events.extend(
            [
                RequestUpdateEvent(
                    fqid_from_collection_and_id("group", group["id"]),
                    {},
                    {
                        "add": {
                            "permissions": [
                                *(
                                    ["agenda_item.can_see"]
                                    if not any(
                                        "agenda_item." + suffix
                                        in group.get("permissions", [])
                                        or []
                                        for suffix in ["can_see_internal", "can_manage"]
                                    )
                                    else []
                                ),
                                *[
                                    "list_of_speakers" + substr
                                    for substr in perm_substrings
                                ],
                            ]
                        },
                        "remove": {
                            "permissions": [
                                "agenda_item" + substr for substr in perm_substrings
                            ]
                        },
                    },
                )
                for group in groups.values()
                if (
                    perm_substrings := [
                        substr
                        for substr in [
                            ".can_see_moderator_notes",
                            ".can_manage_moderator_notes",
                        ]
                        if any(
                            permission == "agenda_item" + substr
                            for permission in group.get("permissions", []) or []
                        )
                    ]
                )
            ]
        )
        return events
