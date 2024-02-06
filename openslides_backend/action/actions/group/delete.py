from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from openslides_backend.shared.exceptions import ActionException

from ....models.models import Group
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
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
    calculate_inherited_groups_helper_with_parent_id,
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
                "mediafile_access_group_ids",
                "mediafile_inherited_access_group_ids",
                "meeting_user_ids",
                "meeting_id",
            ],
        )
        if len(group.get("meeting_user_ids", [])) and not self.is_meeting_deleted(
            group["meeting_id"]
        ):
            raise ActionException("You cannot delete a group with users.")
        self.mediafile_ids: list[int] = list(
            set(group.get("mediafile_access_group_ids", []))
            | set(group.get("mediafile_inherited_access_group_ids", []))
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
        get_many_request = GetManyRequest(
            mediafile_collection,
            self.mediafile_ids,
            [
                "parent_id",
                "is_public",
                "inherited_access_group_ids",
                "access_group_ids",
                "child_ids",
            ],
        )
        gm_result = self.datastore.get_many([get_many_request])
        db_mediafiles = gm_result.get(mediafile_collection, {})

        events = super().handle_relation_updates(instance)
        for event in events:
            if collection_from_fqid(event["fqid"]) != "mediafile":
                yield event

        # search root changed mediafiles
        roots: set[int] = set()
        for id_ in self.mediafile_ids:
            root_id = id_
            while (
                parent_id := self.datastore.get(
                    fqid_from_collection_and_id("mediafile", root_id), ["parent_id"]
                ).get("parent_id", 0)
            ) in self.mediafile_ids:
                root_id = parent_id
            roots.add(root_id)

        self.group_writes: dict[int, list[int]] = defaultdict(list)
        for mediafile_id in roots:
            yield from self.check_recursive(mediafile_id, db_mediafiles)

        for group_id, mediafile_ids in self.group_writes.items():
            yield self.build_event(
                EventType.Update,
                fqid_from_collection_and_id("group", group_id),
                list_fields={
                    "add": {"mediafile_inherited_access_group_ids": mediafile_ids},
                    "remove": {},
                },
            )

    def check_recursive(
        self, id_: int, db_mediafiles: dict[int, Any]
    ) -> Iterable[Event]:
        fqid = fqid_from_collection_and_id("mediafile", id_)

        mediafile = self.datastore.get(
            fqid_from_collection_and_id("mediafile", id_),
            [
                "parent_id",
                "is_public",
                "inherited_access_group_ids",
                "access_group_ids",
                "child_ids",
            ],
        )

        (
            calc_is_public,
            calc_inherited_access_group_ids,
        ) = calculate_inherited_groups_helper_with_parent_id(
            self.datastore,
            mediafile.get("access_group_ids"),
            mediafile.get("parent_id"),
        )
        self.datastore.apply_changed_model(
            fqid,
            {
                "is_public": calc_is_public,
                "inherited_access_group_ids": calc_inherited_access_group_ids,
            },
        )
        event_fields = self.datastore.get(
            fqid, ["is_public", "access_group_ids", "inherited_access_group_ids"]
        )
        yield self.build_event(
            EventType.Update,
            fqid,
            event_fields,
        )

        if group_ids := set(calc_inherited_access_group_ids or ()) - set(
            db_mediafiles[id_].get("inherited_access_group_ids") or set()
        ):
            for group_id in group_ids:
                self.group_writes[group_id].append(id_)
        for child_id in mediafile.get("child_ids", []) or []:
            if child_id in self.mediafile_ids:
                yield from self.check_recursive(child_id, db_mediafiles)

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
