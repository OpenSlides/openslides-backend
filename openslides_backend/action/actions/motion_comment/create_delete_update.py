from typing import Any, Dict, List, Optional

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin

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


class MotionCommentMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        super().check_permissions(instance)

        section = self.get_section(
            instance, ["write_group_ids", "meeting_id", "submitter_can_write"]
        )
        meeting_id = section["meeting_id"]
        user = self.datastore.get(
            fqid_from_collection_and_id("user", self.user_id),
            [f"group_${meeting_id}_ids"],
            lock_result=False,
        )
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            ["admin_group_id"],
            lock_result=False,
        )

        allowed_groups = set(section.get("write_group_ids", []))
        allowed_groups.add(meeting["admin_group_id"])
        user_groups = set(user.get(f"group_${meeting_id}_ids", []))
        if allowed_groups.intersection(user_groups):
            return

        motion_id = instance.get("motion_id")
        if not motion_id:
            comment = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["motion_id"],
            )
            motion_id = comment.get("motion_id")

        if (
            section.get("submitter_can_write")
            and motion_id
            and self.datastore.exists(
                "motion_submitter",
                And(
                    FilterOperator("user_id", "=", self.user_id),
                    FilterOperator("motion_id", "=", motion_id),
                ),
            )
        ):
            return

        msg = f"You are not allowed to perform action {self.name}."
        msg += " You are not in the write group of the section or in admin group."
        raise PermissionDenied(msg)

    def get_section(
        self, instance: Dict[str, Any], fields: List[str]
    ) -> Dict[str, Any]:
        # get section_id and meeting_id, create vs delete/update case.
        if instance.get("section_id"):
            section_id = instance["section_id"]
        else:
            comment = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["section_id"],
                lock_result=False,
            )
            section_id = comment["section_id"]
        return self.datastore.get(
            fqid_from_collection_and_id("motion_comment_section", section_id),
            fields,
            lock_result=False,
        )

    def get_history_information(self) -> Optional[List[str]]:
        _, action = self.name.split(".")
        if len(self.instances) == 1:
            section = self.get_section(self.instances[0], ["name"])
            return ["Comment {} " + action + "d", section["name"]]
        return ["Comment " + action + "d"]


class MotionCommentCreate(MotionCommentMixin, CreateActionWithInferredMeeting):
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


class MotionCommentUpdate(ExtendHistoryMixin, MotionCommentMixin, UpdateAction):
    extend_history_to = "motion_id"


class MotionCommentDelete(MotionCommentMixin, DeleteAction):
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
