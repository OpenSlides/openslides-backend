from collections import defaultdict
from collections.abc import Iterable
from typing import Any, cast

from ....models.models import Motion
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ...action import original_instances
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

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        self.forwarded_attachments, self.meeting_mediafile_replace_map = (
            self.duplicate_mediafiles(action_data, defaultdict(set), defaultdict(dict))
        )
        return action_data

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
        action_data = {"amendment_data": amendment_data}
        if self.should_forward_attachments():
            action_data.update(
                {
                    "forwarded_attachments": cast(
                        Iterable[dict[str, Any]], self.forwarded_attachments
                    ),
                    "meeting_mediafile_replace_map": cast(
                        Iterable[dict[str, Any]], self.meeting_mediafile_replace_map
                    ),
                }
            )
        return self.execute_other_action(MotionCreateForwardedAmendment, [action_data])

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.with_amendments = instance.pop("with_amendments", False)
        self.check_state_allow_forwarding(instance)
        return super().update_instance(instance)

    def should_forward_amendments(self, instance: dict[str, Any]) -> bool:
        return self.with_amendments

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
