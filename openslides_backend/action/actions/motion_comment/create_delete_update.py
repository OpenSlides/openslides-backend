from typing import Any

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import MotionComment
from ....permissions.permission_helper import has_committee_management_level
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
from ..meeting_user.helper_mixin import MeetingUserHelperMixin


class MotionCommentMixin(MeetingUserHelperMixin, Action):
    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)

        section = self.get_section(
            instance, ["write_group_ids", "meeting_id", "submitter_can_write"]
        )
        meeting_id = section["meeting_id"]
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            ["admin_group_id", "committee_id"],
            lock_result=False,
        )

        allowed_groups = set(section.get("write_group_ids", []))
        allowed_groups.add(meeting["admin_group_id"])
        user_groups = self.get_groups_from_meeting_user(meeting_id, self.user_id)
        if allowed_groups.intersection(user_groups):
            return

        if has_committee_management_level(
            self.datastore, self.user_id, meeting["committee_id"]
        ):
            return

        user_orga_management_level = self.datastore.get(
            fqid_from_collection_and_id("user", self.user_id),
            ["organization_management_level"],
            lock_result=False,
        ).get("organization_management_level")
        if user_orga_management_level in [
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            OrganizationManagementLevel.SUPERADMIN,
        ]:
            return

        if section.get("submitter_can_write"):
            motion_id = self.get_field_from_instance("motion_id", instance)

            meeting_user = self.datastore.filter(
                "meeting_user",
                And(
                    FilterOperator("user_id", "=", self.user_id),
                    FilterOperator("meeting_id", "=", meeting_id),
                ),
                ["id"],
            )
            meeting_user_id = None
            if meeting_user:
                meeting_user_id = int(list(meeting_user)[0])
            if motion_id and self.datastore.exists(
                "motion_submitter",
                And(
                    FilterOperator("meeting_user_id", "=", meeting_user_id),
                    FilterOperator("motion_id", "=", motion_id),
                ),
            ):
                return

        msg = f"You are not allowed to perform action {self.name}."
        msg += " You are not in the write group of the section or in admin group"
        if section.get("submitter_can_write"):
            msg += " and no submitter"
        msg += "."

        raise PermissionDenied(msg)

    def get_section(
        self, instance: dict[str, Any], fields: list[str]
    ) -> dict[str, Any]:
        section_id = self.get_field_from_instance("section_id", instance)
        return self.datastore.get(
            fqid_from_collection_and_id("motion_comment_section", section_id),
            fields,
            lock_result=False,
        )

    def get_history_information(self) -> HistoryInformation | None:
        instances = self.get_instances_with_fields(["motion_id", "section_id"])
        _, action = self.name.split(".")
        return {
            fqid_from_collection_and_id("motion", instance["motion_id"]): [
                "Comment {} " + action + "d",
                fqid_from_collection_and_id(
                    "motion_comment_section", instance["section_id"]
                ),
            ]
            for instance in instances
        }


class MotionCommentCreate(MotionCommentMixin, CreateActionWithInferredMeeting):
    relation_field_for_meeting = "motion_id"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
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
