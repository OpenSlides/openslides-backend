from typing import Any, Dict

from ....models.models import Motion
from ....shared.exceptions import ActionException
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
            "meeting_id",
            "title",
            "number",
            "state_extension",
            "sort_parent_id",
            "category_id",
            "block_id",
            "supporter_ids",
            "tag_ids",
            "attachment_ids",
            "origin_id",
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
        self.check_for_origin_id(instance)
        self.create_submitters(instance)
        self.set_created_last_modified_and_number(instance)
        return instance
