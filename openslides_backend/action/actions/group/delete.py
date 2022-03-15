from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, Union, cast

from ....models.models import Group
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.interfaces.event import EventType, ListFields
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import Collection, FullQualifiedId
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        group = self.datastore.get(
            FullQualifiedId(Collection("group"), instance["id"]), []
        )
        self.mediafile_ids: List[int] = list(
            (set(group.get("mediafile_access_group_ids", set())) or set())
            | (set(group.get("mediafile_inherited_access_group_ids", set()) or set()))
        )
        return instance

    def handle_relation_updates(
        self,
        instance: Dict[str, Any],
    ) -> Iterable[WriteRequest]:
        """
        Method use the WriteRequests for mediafiles, that were generated
        from the relation handlers, to remove the deleted group from mediafile
        (inherited-)access_group_ids. They will be calculated.
        Hint: datastore request gets all mediafile-data in updated state,
        because the created WriteResults are applied to the changed_data
        """
        self.group_id = instance["id"]
        mediafile_collection = Collection("mediafile")
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

        write_requests = super().handle_relation_updates(instance)
        for write_request in write_requests:
            for event in write_request.events:
                if (event["fqid"]).collection.collection != "mediafile":
                    yield write_request

        # search root changed mediafiles
        roots: Set[int] = set()
        for id_ in self.mediafile_ids:
            root_id = id_
            while (
                parent_id := self.datastore.get(
                    FullQualifiedId(mediafile_collection, root_id), ["parent_id"]
                ).get("parent_id", 0)
            ) in self.mediafile_ids:
                root_id = parent_id
            roots.add(root_id)

        self.group_writes: Dict[int, List[int]] = defaultdict(list)
        for mediafile_id in roots:
            yield from self.check_recursive(mediafile_id, db_mediafiles)

        group_collection = Collection("group")
        for group_id, mediafile_ids in self.group_writes.items():
            yield self.build_write_request(
                EventType.Update,
                FullQualifiedId(group_collection, group_id),
                f"delete group {self.group_id}: add mediafile_ids {mediafile_ids} to group {group_id} 'mediafile_inherited_access_group_ids'",
                list_fields={
                    "add": {
                        "mediafile_inherited_access_group_ids": cast(
                            List[Union[int, str]], mediafile_ids
                        )
                    },
                    "remove": {},
                },
            )

    def check_recursive(
        self, id_: int, db_mediafiles: Dict[int, Any]
    ) -> Iterable[WriteRequest]:
        coll_mediafile = Collection("mediafile")
        fqid = FullQualifiedId(coll_mediafile, id_)

        mediafile = self.datastore.get(
            FullQualifiedId(coll_mediafile, id_),
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
        yield self.build_write_request(
            EventType.Update,
            fqid,
            f"delete group {self.group_id}: calculate fields for mediafile {fqid.id}",
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

    def build_write_request(
        self,
        type: EventType,
        fqid: FullQualifiedId,
        information: str,
        fields: Optional[Dict[str, Any]] = None,
        list_fields: Optional[ListFields] = None,
    ) -> WriteRequest:
        """
        Building write requests by hand, but with eliminating the meta-* fields
        """
        if type == EventType.Update and fields:
            fields = {
                k: v
                for k, v in fields.items()
                if k != "id" and not k.startswith("meta_")
            }
        return super().build_write_request(type, fqid, information, fields, list_fields)
