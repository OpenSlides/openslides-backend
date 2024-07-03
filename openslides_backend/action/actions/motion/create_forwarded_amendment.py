from typing import Any

from ....models.models import Motion
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResults
from .base_create_forwarded import BaseMotionCreateForwarded


@register_action(
    "motion.create_forwarded_amendment", action_type=ActionType.BACKEND_INTERNAL
)
class MotionCreateForwardedAmendment(BaseMotionCreateForwarded):
    """
    Create action for forwarded motions.
    """

    schema = DefaultSchema(Motion()).get_create_schema(
        required_properties=["meeting_id", "title", "origin_id", "lead_motion_id"],
        optional_properties=["reason", "text", "amendment_paragraphs"],
        additional_optional_fields={
            "use_original_submitter": {"type": "boolean"},
            "use_original_number": {"type": "boolean"},
            "with_amendments": {"type": "boolean"},
        },
    )

    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)

        # check if origin motion is normal or statute_amendment
        origin = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["origin_id"]),
            ["lead_motion_id", "statute_paragraph_id"],
            lock_result=False,
        )
        if not origin.get("lead_motion_id") or origin.get("statute_paragraph_id"):
            msg = "Can only forward amendments in internal forward."
            raise PermissionDenied(msg)

    def create_amendments(self, amendment_data: ActionData) -> ActionResults | None:
        return self.execute_other_action(MotionCreateForwardedAmendment, amendment_data)

    def should_forward_amendments(self, instance: dict[str, Any]) -> bool:
        return True
