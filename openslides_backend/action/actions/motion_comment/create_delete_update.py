from typing import Any, Dict

from ....models.models import MotionComment
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action
from ...action_set import ActionSet
from ...generics.delete import DeleteAction
from ...generics.update import UpdateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set


class PermissionMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        super().check_permissions(instance)

        # get section_id and meeting_id, create vs delete/update case.
        if "section_id" in instance:
            section_id = instance["section_id"]
        else:
            comment = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["section_id"],
            )
            section_id = comment["section_id"]
        section = self.datastore.get(
            fqid_from_collection_and_id("motion_comment_section", section_id),
            ["write_group_ids", "meeting_id"],
        )
        meeting_id = section["meeting_id"]
        user = self.datastore.get(
            fqid_from_collection_and_id("user", self.user_id),
            [f"group_${meeting_id}_ids"],
        )
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id), ["admin_group_id"]
        )

        allowed_groups = set(section.get("write_group_ids", []))
        allowed_groups.add(meeting["admin_group_id"])
        user_groups = set(user.get(f"group_${meeting_id}_ids", []))
        if allowed_groups.intersection(user_groups):
            return

        msg = f"You are not allowed to perform action {self.name}."
        msg += " You are not in the write group of the section or in admin group."
        raise PermissionDenied(msg)


class MotionCommentCreate(PermissionMixin, CreateActionWithInferredMeeting):
    relation_field_for_meeting = "motion_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        # check, if (section_id, motion_id) already in the datastore.
        filter_ = And(
            FilterOperator("section_id", "=", instance["section_id"]),
            FilterOperator("motion_id", "=", instance["motion_id"]),
            FilterOperator("meeting_id", "=", instance["meeting_id"]),
        )
        exists = self.datastore.exists(collection=self.model.collection, filter=filter_)
        if exists:
            raise ActionException(
                "There already exists a comment for this section, please update it instead."
            )
        return instance


class MotionCommentUpdate(PermissionMixin, UpdateAction):
    pass


class MotionCommentDelete(PermissionMixin, DeleteAction):
    pass


@register_action_set("motion_comment")
class MotionCommentActionSet(ActionSet):
    """
    Actions to create, update and delete motion comment.
    """

    model = MotionComment()
    create_schema = DefaultSchema(MotionComment()).get_create_schema(
        ["comment", "motion_id", "section_id"],
    )
    update_schema = DefaultSchema(MotionComment()).get_update_schema(
        optional_properties=["comment"]
    )
    delete_schema = DefaultSchema(MotionComment()).get_delete_schema()
    permission = Permissions.Motion.CAN_SEE

    CreateActionClass = MotionCommentCreate
    UpdateActionClass = MotionCommentUpdate
    DeleteActionClass = MotionCommentDelete
