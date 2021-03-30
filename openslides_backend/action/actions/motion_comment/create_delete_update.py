from typing import Any, Dict

from ....models.models import MotionComment
from ....permissions.permissions import OrganisationManagementLevel, Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
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

        # check for superuser
        if self.user_id > 0:
            user = self.datastore.get(
                FullQualifiedId(Collection("user"), self.user_id),
                [
                    "organisation_management_level",
                ],
            )
            if (
                user.get("organisation_management_level")
                == OrganisationManagementLevel.SUPERADMIN
            ):
                return

        # get section_id, create vs delete/update case.
        if "section_id" in instance:
            section_id = instance["section_id"]
        else:
            comment = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["section_id"]
            )
            section_id = comment["section_id"]
        section = self.datastore.get(
            FullQualifiedId(Collection("motion_comment_section"), section_id),
            ["write_group_ids"],
        )
        gmr = GetManyRequest(
            Collection("group"), section["write_group_ids"], ["user_ids"]
        )
        result = self.datastore.get_many([gmr])
        groups = list(result.get(Collection("group"), {}).values())
        for group in groups:
            if self.user_id in group.get("user_ids", []):
                return
        msg = f"You are not allowed to perform action {self.name}."
        msg += " You are not in the write group of the section."
        raise PermissionDenied(msg)


class MotionCommentCreate(PermissionMixin, CreateActionWithInferredMeeting):
    relation_field_for_meeting = "motion_id"


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
