import time
from typing import Any, Dict

from ....models.models import Motion
from ....shared.exceptions import ActionException
from ....shared.patterns import POSITIVE_NUMBER_REGEX, Collection, FullQualifiedId
from ....shared.schema import optional_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion.update")
class MotionUpdate(UpdateAction):
    """
    Action to update motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(
        optional_properties=[
            "title",
            "number",
            "text",
            "reason",
            "modified_final_version",
            "attachment_ids",
            "supporter_ids",
        ],
        additional_optional_fields={
            **Motion().get_property("amendment_paragraph_$", POSITIVE_NUMBER_REGEX),
            "workflow_id": optional_id_schema,
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["last_modified"] = round(time.time())
        if (
            instance.get("text")
            or instance.get("amendment_paragraph_$")
            or instance.get("reason") == ""
        ):
            motion = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]),
                ["text", "amendment_paragraph_$", "meeting_id"],
            )

        if instance.get("text"):
            if not motion.get("text"):
                raise ActionException(
                    "Cannot update text, because it was not set in the old values."
                )
        if instance.get("amendment_paragraph_$"):
            if not motion.get("amendment_paragraph_$"):
                raise ActionException(
                    "Cannot update amendment_paragraph_$, because it was not set in the old values."
                )
        if instance.get("reason") == "":
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), motion["meeting_id"]),
                ["motions_reason_required"],
            )
            if meeting.get("motions_reason_required"):
                raise ActionException("Reason is required to update.")

        if instance.get("workflow_id"):
            motion = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["state_id"]
            )
            state = self.datastore.get(
                FullQualifiedId(Collection("motion_state"), motion["state_id"]),
                ["workflow_id"],
            )
            if instance["workflow_id"] != state.get("workflow_id"):
                workflow = self.datastore.get(
                    FullQualifiedId(
                        Collection("motion_workflow"), instance["workflow_id"]
                    ),
                    ["first_state_id"],
                )
                instance["state_id"] = workflow["first_state_id"]
                instance["recommendation_id"] = None
        return instance
