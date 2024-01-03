from typing import Any, Dict

from ....models.models import Motion
from ....permissions.base_classes import Permission
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, MissingPermission, PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import (
    id_list_schema,
    number_string_json_schema,
    optional_id_schema,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..agenda_item.agenda_creation import agenda_creation_properties
from .create_base import MotionCreateBase
from .mixins import AmendmentParagraphHelper


@register_action("motion.create")
class MotionCreate(AmendmentParagraphHelper, MotionCreateBase):
    """
    Create Action for motions.
    """

    schema = DefaultSchema(Motion()).get_create_schema(
        optional_properties=[
            "number",
            "sort_parent_id",
            "category_id",
            "block_id",
            "supporter_meeting_user_ids",
            "tag_ids",
            "attachment_ids",
            "text",
            "lead_motion_id",
            "statute_paragraph_id",
            "reason",
            "amendment_paragraphs",
        ],
        required_properties=["meeting_id", "title"],
        additional_optional_fields={
            "workflow_id": optional_id_schema,
            "submitter_ids": id_list_schema,
            "amendment_paragraphs": number_string_json_schema,
            **agenda_creation_properties,
        },
    )
    history_information = "Motion created"

    def prefetch(self, action_data: ActionData) -> None:
        self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list(
                        {
                            instance["meeting_id"]
                            for instance in action_data
                            if instance.get("meeting_id")
                        }
                    ),
                    [
                        "is_active_in_organization_id",
                        "name",
                        "id",
                        "motions_default_workflow_id",
                        "motions_default_amendment_workflow_id",
                        "motions_default_statute_amendment_workflow_id",
                        "motions_reason_required",
                        "motion_submitter_ids",
                        "motions_number_type",
                        "agenda_item_creation",
                        "agenda_item_ids",
                        "list_of_speakers_initially_closed",
                        "list_of_speakers_ids",
                        "motion_ids",
                    ],
                )
            ]
        )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # special check logic
        if instance.get("lead_motion_id"):
            if instance.get("statute_paragraph_id"):
                raise ActionException(
                    "You can't give both of lead_motion_id and statute_paragraph_id."
                )
            if not instance.get("text") and not instance.get("amendment_paragraphs"):
                raise ActionException(
                    "Text or amendment_paragraphs is required in this context."
                )
            if instance.get("text") and instance.get("amendment_paragraphs"):
                raise ActionException(
                    "You can't give both of text and amendment_paragraphs"
                )
            if instance.get("text") and "amendment_paragraphs" in instance:
                del instance["amendment_paragraphs"]
            if instance.get("amendment_paragraphs") and "text" in instance:
                del instance["text"]
        else:
            if not instance.get("text"):
                raise ActionException("Text is required")
            if instance.get("amendment_paragraphs"):
                raise ActionException(
                    "You can't give amendment_paragraphs in this context"
                )
        if instance.get("amendment_paragraphs"):
            self.validate_amendment_paragraphs(instance)
        # if amendment and no category set, use category from the lead motion
        if instance.get("lead_motion_id") and "category_id" not in instance:
            lead_motion = self.datastore.get(
                fqid_from_collection_and_id(
                    self.model.collection, instance["lead_motion_id"]
                ),
                ["category_id"],
            )
            instance["category_id"] = lead_motion.get("category_id")

        # fetch all needed settings and check reason
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
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
        perm: Permission
        # Check can create amendment if needed else check can_create
        if instance.get("lead_motion_id"):
            perm = Permissions.Motion.CAN_CREATE_AMENDMENTS
            if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
                raise MissingPermission(perm)

        else:
            perm = Permissions.Motion.CAN_CREATE
            if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
                raise MissingPermission(perm)

        # whitelist the fields depending on the user's permissions
        whitelist = []
        forbidden_fields = set()
        perm = Permissions.Mediafile.CAN_SEE
        if has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
            whitelist.append("attachment_ids")
        elif "attachment_ids" in instance:
            forbidden_fields.add("attachment_ids")

        perm = Permissions.Motion.CAN_MANAGE
        if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
            whitelist += [
                "title",
                "text",
                "reason",
                "lead_motion_id",
                "amendment_paragraphs",
                "category_id",
                "statute_paragraph_id",
                "workflow_id",
                "id",
                "meeting_id",
            ]
            if instance.get("lead_motion_id"):
                whitelist.remove("category_id")
            for field in instance:
                if field not in whitelist:
                    forbidden_fields.add(field)

        if forbidden_fields:
            msg = f"You are not allowed to perform action {self.name}. "
            msg += f"Forbidden fields: {', '.join(forbidden_fields)}"
            raise PermissionDenied(msg)
