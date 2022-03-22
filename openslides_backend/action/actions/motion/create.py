from typing import Any, Dict

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, MissingPermission, PermissionDenied
from ....shared.patterns import POSITIVE_NUMBER_REGEX, Collection, FullQualifiedId
from ....shared.schema import id_list_schema, optional_id_schema
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..agenda_item.agenda_creation import agenda_creation_properties
from .create_base import MotionCreateBase


@register_action("motion.create")
class MotionCreate(MotionCreateBase):
    """
    Create Action for motions.
    """

    schema = DefaultSchema(Motion()).get_create_schema(
        optional_properties=[
            "number",
            "state_extension",
            "sort_parent_id",
            "category_id",
            "block_id",
            "supporter_ids",
            "tag_ids",
            "attachment_ids",
            "text",
            "lead_motion_id",
            "statute_paragraph_id",
            "reason",
        ],
        required_properties=["meeting_id", "title"],
        additional_optional_fields={
            "workflow_id": optional_id_schema,
            "submitter_ids": id_list_schema,
            **Motion().get_property("amendment_paragraph_$", POSITIVE_NUMBER_REGEX),
            **agenda_creation_properties,
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # special check logic
        if instance.get("lead_motion_id"):
            if instance.get("statute_paragraph_id"):
                raise ActionException(
                    "You can't give both of lead_motion_id and statute_paragraph_id."
                )
            if not instance.get("text") and not instance.get("amendment_paragraph_$"):
                raise ActionException(
                    "Text or amendment_paragraph_$ is required in this context."
                )
            if instance.get("text") and instance.get("amendment_paragraph_$"):
                raise ActionException(
                    "You can't give both of text and amendment_paragraph_$"
                )
            if instance.get("text") and "amendment_paragraph_$" in instance:
                del instance["amendment_paragraph_$"]
            if instance.get("amendment_paragraph_$") and "text" in instance:
                del instance["text"]
        else:
            if not instance.get("text"):
                raise ActionException("Text is required")
            if instance.get("amendment_paragraph_$"):
                raise ActionException(
                    "You can't give amendment_paragraph_$ in this context"
                )
        # if lead_motion and not has perm motion.can_manage
        # use category_id and block_id from the lead_motion
        if instance.get("lead_motion_id") and not has_perm(
            self.datastore,
            self.user_id,
            Permissions.Motion.CAN_MANAGE,
            instance["meeting_id"],
        ):
            lead_motion = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["lead_motion_id"]),
                ["block_id", "category_id"],
            )
            instance["block_id"] = lead_motion.get("block_id")
            instance["category_id"] = lead_motion.get("category_id")

        # fetch all needed settings and check reason
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            [
                "motions_default_workflow_id",
                "motions_default_amendment_workflow_id",
                "motions_default_statute_amendment_workflow_id",
                "motions_reason_required",
            ],
        )
        if meeting.get("motions_reason_required") and not instance.get("reason"):
            raise ActionException("Reason is required")

        self.set_state_from_workflow(instance, meeting)
        self.create_submitters(instance)
        self.set_sequential_number(instance)
        self.set_created_last_modified_and_number(instance)
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        # Check can create amendment if needed else check can_create
        if instance.get("lead_motion_id"):
            perm = Permissions.Motion.CAN_CREATE_AMENDMENTS
            if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
                raise MissingPermission(perm)

        else:
            perm = Permissions.Motion.CAN_CREATE
            if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
                raise MissingPermission(perm)

        # if not can manage whitelist the fields.
        perm = Permissions.Motion.CAN_MANAGE
        if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
            whitelist = [
                "title",
                "text",
                "reason",
                "lead_motion_id",
                "amendment_paragraph_$",
                "category_id",
                "statute_paragraph_id",
                "workflow_id",
                "id",
                "meeting_id",
            ]
            if instance.get("lead_motion_id"):
                whitelist.remove("category_id")
            forbidden_fields = []
            for field in instance:
                if field not in whitelist:
                    forbidden_fields.append(field)

            if forbidden_fields:
                msg = f"You are not allowed to perform action {self.name}. "
                msg += f"Forbidden fields: {', '.join(forbidden_fields)}"
                raise PermissionDenied(msg)
