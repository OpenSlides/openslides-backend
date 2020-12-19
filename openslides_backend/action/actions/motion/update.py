import time
from typing import Any, Dict

from ....models.models import Motion
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...action import PERMISSION_SPECIAL_CASE
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .amendment_paragraphs_mixin import (
    AmendmentParagraphsMixin,
    amendment_paragraphs_schema,
)


@register_action("motion.update")
class MotionUpdate(UpdateAction, AmendmentParagraphsMixin):
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
        ],
        additional_optional_fields={
            "amendment_paragraphs": amendment_paragraphs_schema
        },
    )
    permission_description = PERMISSION_SPECIAL_CASE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["last_modified"] = round(time.time())
        if (
            instance.get("text")
            or instance.get("amendment_paragraphs")
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
        if instance.get("amendment_paragraphs"):
            if not motion.get("amendment_paragraph_$"):
                raise ActionException(
                    "Cannot update amendment_paragraphs, because it was not set in the old values."
                )
        if instance.get("reason") == "":
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), motion["meeting_id"]),
                ["motions_reason_required"],
            )
            if meeting.get("motions_reason_required"):
                raise ActionException("Reason is required to update.")

        self.handle_amendment_paragraphs(instance)
        return instance
