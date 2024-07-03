from typing import Any

from ....models.models import Motion
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResults
from .base_create_forwarded import BaseMotionCreateForwarded
from .create_forwarded_amendment import MotionCreateForwardedAmendment


@register_action("motion.create_forwarded")
class MotionCreateForwarded(BaseMotionCreateForwarded):
    """
    Create action for forwarded amendments.
    Result amendment will not have a lead_motion_id yet, that will have to be set via the calling action.
    """

    schema = DefaultSchema(Motion()).get_create_schema(
        required_properties=["meeting_id", "title", "text", "origin_id"],
        optional_properties=["reason"],
        additional_optional_fields={
            "use_original_submitter": {"type": "boolean"},
            "use_original_number": {"type": "boolean"},
            "with_amendments": {"type": "boolean"},
        },
    )

    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)

        # check if origin motion is amendment or statute_amendment
        origin = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["origin_id"]),
            ["lead_motion_id", "statute_paragraph_id"],
            lock_result=False,
        )
        if origin.get("lead_motion_id") or origin.get("statute_paragraph_id"):
            msg = "Amendments cannot be forwarded."
            raise PermissionDenied(msg)

    def create_amendments(self, amendment_data: ActionData) -> ActionResults | None:
        return self.execute_other_action(MotionCreateForwardedAmendment, amendment_data)

    def should_forward_amendments(self, instance: dict[str, Any]) -> bool:
        return instance.pop("with_amendments", False)
