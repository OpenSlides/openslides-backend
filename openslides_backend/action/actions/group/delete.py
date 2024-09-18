from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from openslides_backend.shared.exceptions import ActionException

from ....models.models import Group
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.filters import And, FilterOperator
from ....shared.interfaces.event import Event, EventType, ListFields
from ....shared.patterns import (
    FullQualifiedId,
    collection_from_fqid,
    fqid_from_collection_and_id,
)
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..mediafile.calculate_mixins import (
    calculate_inherited_groups_helper_with_parent_meeting_mediafile_id,
)


@register_action("group.delete")
class GroupDeleteAction(DeleteAction):
    """
    Action to delete a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_delete_schema()
    permission = Permissions.User.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        group = self.datastore.get(
            fqid_from_collection_and_id("group", instance["id"]),
            [
                "meeting_mediafile_access_group_ids",
                "meeting_mediafile_inherited_access_group_ids",
                "meeting_user_ids",
                "meeting_id",
            ],
        )
        if len(group.get("meeting_user_ids", [])) and not self.is_meeting_deleted(
            group["meeting_id"]
        ):
            raise ActionException("You cannot delete a group with users.")
        self.meeting_mediafile_ids: list[int] = list(
            set(group.get("meeting_mediafile_access_group_ids", []))
            | set(group.get("meeting_mediafile_inherited_access_group_ids", []))
        )
        return instance

    def handle_relation_updates(
        self,
        instance: dict[str, Any],
    ) -> Iterable[Event]:
        """
        Method use the WriteRequests for mediafiles, that were generated
        from the relation handlers, to remove the deleted group from mediafile
        (inherited-)access_group_ids. They will be calculated.
        Hint: datastore request gets all mediafile-data in updated state,
        because the created WriteResults are applied to the changed_data
        """
        self.group_id = instance["id"]
        mediafile_collection = "mediafile"
        meeting_mediafile_collection = "meeting_mediafile"
        get_many_request = GetManyRequest(
            meeting_mediafile_collection,
            self.meeting_mediafile_ids,
            [
                "is_public",
                "inherited_access_group_ids",
                "access_group_ids",
                "mediafile_id",
                "meeting_id",
            ],
        )
        gm_result = self.datastore.get_many([get_many_request])
        db_meeting_mediafiles = gm_result.get(meeting_mediafile_collection, {})
        mediafile_ids = [
            file["mediafile_id"] for file in db_meeting_mediafiles.values()
        ]

        events = super().handle_relation_updates(instance)
        for event in events:
            if collection_from_fqid(event["fqid"]) not in [
                mediafile_collection,
                meeting_mediafile_collection,
            ]:
                yield event

        # search root changed mediafiles
        roots: set[tuple[int, int]] = set()
        for id_ in self.meeting_mediafile_ids:
            root_id = id_
            meeting_id = db_meeting_mediafiles[id_]["meeting_id"]
            root_source_id = db_meeting_mediafiles[id_]["mediafile_id"]
            while (
                parent_source_id := self.datastore.get(
                    fqid_from_collection_and_id(mediafile_collection, root_source_id),
                    ["parent_id"],
                ).get("parent_id", 0)
            ) in mediafile_ids and (
                parent_id := self.find_meeting_mediafile_id_for_mediafile(
                    parent_source_id, meeting_id
                )
            ):
                root_id = parent_id
                root_source_id = parent_source_id
            roots.add((root_id, root_source_id))

        self.group_writes: dict[int, list[int]] = defaultdict(list)
        for meeting_mediafile_id, mediafile_id in roots:
            yield from self.check_recursive(
                meeting_mediafile_id, mediafile_id, db_meeting_mediafiles
            )

        for group_id, mediafile_ids in self.group_writes.items():
            yield self.build_event(
                EventType.Update,
                fqid_from_collection_and_id("group", group_id),
                list_fields={
                    "add": {
                        "meeting_mediafile_inherited_access_group_ids": mediafile_ids
                    },
                    "remove": {},
                },
            )

    def check_recursive(
        self,
        meeting_mediafile_id: int,
        mediafile_id: int,
        db_meeting_mediafiles: dict[int, Any],
    ) -> Iterable[Event]:
        mediafile_fqid = fqid_from_collection_and_id("mediafile", mediafile_id)
        meeting_mediafile_fqid = fqid_from_collection_and_id(
            "meeting_mediafile", meeting_mediafile_id
        )

        mediafile = self.datastore.get(
            mediafile_fqid,
            [
                "parent_id",
                "child_ids",
            ],
        )
        meeting_mediafile = self.datastore.get(
            meeting_mediafile_fqid,
            [
                "is_public",
                "inherited_access_group_ids",
                "access_group_ids",
                "meeting_id",
            ],
        )
        parent_meeting_mediafile_id = None
        if mediafile.get("parent_id"):
            parent_meeting_mediafile_id = self.find_meeting_mediafile_id_for_mediafile(
                mediafile["parent_id"], meeting_mediafile["meeting_id"]
            )
        (
            calc_is_public,
            calc_inherited_access_group_ids,
        ) = calculate_inherited_groups_helper_with_parent_meeting_mediafile_id(
            self.datastore,
            meeting_mediafile.get("access_group_ids"),
            parent_meeting_mediafile_id,
        )
        self.datastore.apply_changed_model(
            meeting_mediafile_fqid,
            {
                "is_public": calc_is_public,
                "inherited_access_group_ids": calc_inherited_access_group_ids,
            },
        )
        event_fields = self.datastore.get(
            meeting_mediafile_fqid,
            ["is_public", "access_group_ids", "inherited_access_group_ids"],
        )
        yield self.build_event(
            EventType.Update,
            meeting_mediafile_fqid,
            event_fields,
        )

        if group_ids := set(calc_inherited_access_group_ids or ()) - set(
            db_meeting_mediafiles[meeting_mediafile_id].get(
                "inherited_access_group_ids"
            )
            or set()
        ):
            for group_id in group_ids:
                self.group_writes[group_id].append(meeting_mediafile_id)
        for child_id in mediafile.get("child_ids", []) or []:
            if (
                child_meeting_mediafile_id := self.find_meeting_mediafile_id_for_mediafile(
                    child_id, meeting_mediafile["meeting_id"]
                )
            ) in self.meeting_mediafile_ids:
                yield from self.check_recursive(
                    child_meeting_mediafile_id, child_id, db_meeting_mediafiles
                )

    def find_meeting_mediafile_id_for_mediafile(
        self, mediafile_id: int, meeting_id: int
    ) -> int | None:
        meeting_mediafiles = list(
            self.datastore.filter(
                "meeting_mediafile",
                And(
                    FilterOperator("meeting_id", "=", meeting_id),
                    FilterOperator("mediafile_id", "=", mediafile_id),
                ),
                ["id"],
            ).keys()
        )
        if len(meeting_mediafiles):
            assert len(meeting_mediafiles) == 1
            return meeting_mediafiles[0]
        return None

    def build_event(
        self,
        type: EventType,
        fqid: FullQualifiedId,
        fields: dict[str, Any] | None = None,
        list_fields: ListFields | None = None,
    ) -> Event:
        """
        Building event by hand, but with eliminating the meta-* fields
        """
        if type == EventType.Update and fields:
            fields = {
                k: v
                for k, v in fields.items()
                if k != "id" and not k.startswith("meta_")
            }
        return super().build_event(type, fqid, fields, list_fields)
