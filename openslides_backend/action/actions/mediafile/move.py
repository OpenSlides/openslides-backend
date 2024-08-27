from typing import Any

from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import KEYSEPARATOR, fqid_from_collection_and_id
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...mixins.meeting_mediafile_helper import find_meeting_mediafile
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..meeting_mediafile.create import MeetingMediafileCreate
from ..meeting_mediafile.delete import MeetingMediafileDelete
from ..meeting_mediafile.update import MeetingMediafileUpdate
from .calculate_mixins import (
    MediafileCalculatedFieldsMixin,
    calculate_inherited_groups_helper_with_parent_id,
)
from .mixins import MediafileMixin


@register_action("mediafile.move")
class MediafileMoveAction(
    MediafileMixin,
    UpdateAction,
    SingularActionMixin,
    MediafileCalculatedFieldsMixin,
):
    """
    Action to move mediafiles.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_default_schema(
        title="Mediafile new parent schema",
        description="An object containing an array of mediafile ids and the new parent id the items should be moved to.",
        required_properties=["parent_id", "owner_id"],
        additional_required_fields={
            "ids": {
                "description": "An array of agenda item ids where the items should be assigned to the new parent id.",
                **id_list_schema,
            }
        },
    )
    permission = Permissions.Mediafile.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        owner_collection, owner_id_str = str(instance["owner_id"]).split(KEYSEPARATOR)
        owner_id = int(owner_id_str)
        yield from self.prepare_move_data(
            parent_id=instance["parent_id"],
            ids=instance["ids"],
            owner_collection=owner_collection,
            owner_id=owner_id,
        )

    def prepare_move_data(
        self,
        parent_id: int | None,
        ids: list[int],
        owner_collection: str,
        owner_id: int,
    ) -> ActionData:
        get_many_request = GetManyRequest(
            self.model.collection,
            ids,
            [
                "owner_id",
                "parent_id",
                "published_to_meetings_in_organization_id",
                "meeting_mediafile_ids",
                "child_ids",
            ],
        )
        gm_result = self.datastore.get_many([get_many_request])
        db_instances = gm_result.get(self.model.collection, {})

        parent: dict[str, Any] | None = None
        if parent_id is not None:
            # Calculate the ancesters of parent
            ancesters = [parent_id]
            parent = grandparent = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, parent_id),
                [
                    "parent_id",
                    "meeting_mediafile_ids",
                    "published_to_meetings_in_organization_id",
                ],
            )
            while grandparent.get("parent_id") is not None:
                gp_parent_id = grandparent["parent_id"]
                ancesters.append(gp_parent_id)
                grandparent = self.datastore.get(
                    fqid_from_collection_and_id(self.model.collection, gp_parent_id),
                    ["parent_id"],
                )
            for id_ in ids:
                if id_ in ancesters:
                    raise ActionException(
                        f"Moving item {id_} to one of its children is not possible."
                    )
        for id_ in ids:
            if id_ not in db_instances:
                raise ActionException(f"Id {id_} not in db_instances.")
            if db_instances[id_].get("published_to_meetings_in_organization_id") and not db_instances[id_].get("parent_id"):
                raise ActionException(
                    f"Item {id_} is published and may therefore not be moved away from the root directory. Please unpublish it first."
                )
            instance: dict[str, Any] = {
                "id": id_,
                "parent_id": parent_id,
                "owner_id": fqid_from_collection_and_id(owner_collection, owner_id),
            }

            if owner_collection == "meeting":
                if len(db_instances[id_].get("meeting_mediafile_ids", [])) != 1:
                    raise ActionException(
                        f"Database corrupt: Expected meeting-owned mediafile {id_} to have exactly one meeting_mediafile"
                    )
                meeting_mediafile_id = db_instances[id_]["meeting_mediafile_ids"][0]
                meeting_mediafiles: list[dict[str, Any]] = []
                should_be_empty: list[dict[str, Any]] = []
                self.expand_children_meeting_mediafile_payload_lists(
                    instance,
                    meeting_mediafile_id,
                    owner_id,
                    should_be_empty,
                    meeting_mediafiles,
                )
                if len(should_be_empty):
                    raise ActionException(
                        f"Database corrupt: Expected children of meeting-owned mediafile {id_} to all have a meeting_mediafile"
                    )
                self.execute_other_action(MeetingMediafileUpdate, meeting_mediafiles)
            else:
                published = (parent or {}).get(
                    "published_to_meetings_in_organization_id"
                )
                instance["published_to_meetings_in_organization_id"] = published
                yield from self.handle_published_for_children(
                    db_instances[id_],
                    (parent or {}).get("published_to_meetings_in_organization_id"),
                )
                self.handle_orga_meeting_mediafiles(instance, db_instances[id_], parent)
            yield instance

    def handle_published_for_children(
        self,
        db_instance: dict[str, Any],
        published_to_meetings_in_organization_id: int | None,
    ) -> ActionData:
        child_ids = db_instance.get("child_ids", [])
        if len(child_ids):
            db_children = self.datastore.get_many(
                [GetManyRequest("mediafile", child_ids, ["child_ids"])]
            )["mediafile"]
            for id_, db_child in db_children.items():
                yield {
                    "id": id_,
                    "published_to_meetings_in_organization_id": published_to_meetings_in_organization_id,
                }
                yield from self.handle_published_for_children(
                    db_child, published_to_meetings_in_organization_id
                )

    def handle_orga_meeting_mediafiles(
        self,
        instance: dict[str, Any],
        db_instance: dict[str, Any],
        parent_instance: dict[str, Any] | None,
    ) -> None:
        if parent_instance and parent_instance.get(
            "published_to_meetings_in_organization_id"
        ):
            parent_meeting_mediafiles = self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting_mediafile",
                        parent_instance.get("meeting_mediafile_ids", []),
                        ["meeting_id"],
                    )
                ]
            ).get("meeting_mediafile", {})
            instance_meeting_mediafiles = self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting_mediafile",
                        db_instance.get("meeting_mediafile_ids", []),
                        ["meeting_id"],
                    )
                ]
            ).get("meeting_mediafile", {})
            meeting_id_to_meeting_mediafile_id = {
                m_mediafile["meeting_id"]: m_mediafile_id
                for m_mediafile_id, m_mediafile in instance_meeting_mediafiles.items()
            }
            meeting_ids = {
                m_mediafile["meeting_id"]
                for m_mediafile in {
                    **parent_meeting_mediafiles,
                    **instance_meeting_mediafiles,
                }.values()
            }
            update_meeting_mediafiles: list[dict[str, Any]] = []
            create_meeting_mediafiles: list[dict[str, Any]] = []
            for meeting_id in meeting_ids:
                self.expand_children_meeting_mediafile_payload_lists(
                    instance,
                    meeting_id_to_meeting_mediafile_id.get(meeting_id),
                    meeting_id,
                    create_meeting_mediafiles,
                    update_meeting_mediafiles,
                )
            if len(create_meeting_mediafiles):
                self.execute_other_action(
                    MeetingMediafileCreate, create_meeting_mediafiles
                )
            if len(update_meeting_mediafiles):
                self.execute_other_action(
                    MeetingMediafileUpdate, update_meeting_mediafiles
                )
        elif meeting_mediafile_ids := self.get_entire_branch_of_meeting_mediafile_ids(
            db_instance
        ):
            self.execute_other_action(
                MeetingMediafileDelete, [{"id": id_} for id_ in meeting_mediafile_ids]
            )

    def get_entire_branch_of_meeting_mediafile_ids(
        self, db_instance: dict[str, Any]
    ) -> list[int]:
        ids: list[int] = db_instance.get("meeting_mediafile_ids", [])
        if child_ids := db_instance.get("child_ids"):
            children = self.datastore.get_many(
                [
                    GetManyRequest(
                        "mediafile", child_ids, ["child_ids", "meeting_mediafile_ids"]
                    )
                ]
            )["mediafile"]
            for child in children.values():
                ids.extend(self.get_entire_branch_of_meeting_mediafile_ids(child))
        return ids

    def expand_children_meeting_mediafile_payload_lists(
        self,
        instance: dict[str, Any],
        meeting_mediafile_id: int | None,
        meeting_id: int,
        expandable_create_list: list[dict[str, Any]],
        expandable_update_list: list[dict[str, Any]],
    ) -> None:
        if meeting_mediafile_id:
            mm_instance: dict[str, Any] = {"id": meeting_mediafile_id}
            expandable_update_list.append(mm_instance)
            access_group_ids = self.datastore.get(
                fqid_from_collection_and_id("meeting_mediafile", meeting_mediafile_id),
                ["access_group_ids"],
            ).get("access_group_ids", [])
        else:
            mm_instance = {"meeting_id": meeting_id, "mediafile_id": instance["id"]}
            expandable_create_list.append(mm_instance)
            access_group_ids = None
        (
            mm_instance["is_public"],
            mm_instance["inherited_access_group_ids"],
        ) = calculate_inherited_groups_helper_with_parent_id(
            self.datastore, access_group_ids, instance.get("parent_id"), meeting_id
        )
        children = self.handle_children(
            instance,
            mm_instance["is_public"],
            mm_instance["inherited_access_group_ids"],
            meeting_id,
        )
        for child in list(children):
            meeting_mediafile_id, _ = find_meeting_mediafile(
                self.datastore, child["meeting_id"], child["id"]
            )
            if meeting_mediafile_id:
                child["id"] = meeting_mediafile_id
                child.pop("meeting_id")
                expandable_update_list.append(child)
            else:
                child["mediafile_id"] = child.pop("id")
                expandable_create_list.append(child)
