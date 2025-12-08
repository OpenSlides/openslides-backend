from typing import Any

from ....models.models import Motion
from ....shared.exceptions import PermissionDenied
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import fqid_from_collection_and_id
from ...action import original_instances
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
    Internal create action for forwarded motion amendments.
    Should only be called by motion.create_forwarded
    """

    schema = DefaultSchema(Motion()).get_create_schema(
        required_properties=["meeting_id", "title", "origin_id", "lead_motion_id"],
        optional_properties=[
            "reason",
            "text",
            "amendment_paragraphs",
            "marked_forwarded",
            "attachment_meeting_mediafile_ids",
        ],
        additional_optional_fields={
            "use_original_submitter": {"type": "boolean"},
            "use_original_number": {"type": "boolean"},
            "with_change_recommendations": {"type": "boolean"},
            "with_attachments": {"type": "boolean"},
        },
    )

    def perform(
        self,
        action_data: ActionData,
        user_id: int,
        internal: bool = False,
        is_sub_call: bool = False,
    ) -> tuple[WriteRequest | None, ActionResults | None]:
        action_data_dict = list(action_data)[0]

        if "meeting_mediafile_replace_map" in action_data_dict:
            self.forwarded_attachments = action_data_dict.pop(
                "forwarded_attachments", {}
            )
            self.meeting_mediafile_replace_map = action_data_dict.pop(
                "meeting_mediafile_replace_map", {}
            )
        action_data = action_data_dict.pop("amendment_data", [])

        return super().perform(action_data, user_id, internal, is_sub_call)

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        if hasattr(self, "meeting_mediafile_replace_map"):
            self.forwarded_attachments, self.meeting_mediafile_replace_map = (
                self.duplicate_mediafiles(
                    action_data,
                    self.forwarded_attachments,
                    self.meeting_mediafile_replace_map,
                )
            )
        return action_data

    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)

        # check if origin motion is normal or statute_amendment
        origin = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["origin_id"]),
            ["lead_motion_id"],
            lock_result=False,
        )
        if not origin.get("lead_motion_id"):
            msg = "Can only forward amendments in internal forward."
            raise PermissionDenied(msg)

    def create_amendments(self, amendment_data: ActionData) -> ActionResults | None:
        for amendment in amendment_data:
            amendment["with_attachments"] = self.with_attachments
        action_data = {"amendment_data": amendment_data}
        if self.with_attachments:
            action_data.update(
                {
                    "forwarded_attachments": self.forwarded_attachments,
                    "meeting_mediafile_replace_map": self.meeting_mediafile_replace_map,
                }
            )
        return self.execute_other_action(MotionCreateForwardedAmendment, [action_data])

    def should_forward_amendments(self, instance: dict[str, Any]) -> bool:
        return True
