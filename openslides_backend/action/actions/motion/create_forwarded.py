from typing import Any

from ....models.models import Motion
from ....shared.exceptions import ActionException, PermissionDenied
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
            "with_change_recommendations": {"type": "boolean"},
            "with_amendments": {"type": "boolean"},
            "mark_amendments_as_forwarded": {"type": "boolean"},
            "with_attachments": {"type": "boolean"},
        },
    )

    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)

        # check if origin motion is amendment
        origin = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["origin_id"]),
            ["lead_motion_id"],
            lock_result=False,
        )
        if origin.get("lead_motion_id"):
            msg = "Amendments cannot be forwarded."
            raise PermissionDenied(msg)

    def create_amendments(self, amendment_data: ActionData) -> ActionResults | None:
        return self.execute_other_action(MotionCreateForwardedAmendment, amendment_data)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.with_amendments = instance.pop("with_amendments", False)
        self.with_attachments = instance.pop("with_attachments", False)
        self.check_state_allow_forwarding(instance)
        super().update_instance(instance)
        return instance

    def should_forward_amendments(self, instance: dict[str, Any]) -> bool:
        return self.with_amendments

    def should_forward_attachments(self, instance: dict[str, Any]) -> bool:
        return self.with_attachments

    def check_state_allow_forwarding(self, instance: dict[str, Any]) -> None:
        origin = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["origin_id"]),
            ["state_id"],
            lock_result=False,
        )
        state = self.datastore.get(
            fqid_from_collection_and_id("motion_state", origin["state_id"]),
            ["allow_motion_forwarding"],
            lock_result=False,
        )
        if not state.get("allow_motion_forwarding"):
            raise ActionException("State doesn't allow to forward motion.")
