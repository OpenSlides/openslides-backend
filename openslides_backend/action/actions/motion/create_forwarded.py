from typing import Any, Dict

from ....models.models import Motion
from ....shared.patterns import Collection, FullQualifiedId
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_base import MotionCreateBase


@register_action("motion.create_forwarded")
class MotionCreateForwarded(MotionCreateBase):
    """
    Create action for forwarded motions.
    """

    schema = DefaultSchema(Motion()).get_create_schema(
        optional_properties=[
            "reason",
        ],
        required_properties=["meeting_id", "title", "text", "origin_id"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            [
                "motions_default_workflow_id",
            ],
        )
        self.set_state_from_workflow(instance, meeting)
        self.check_for_origin_id(instance)
        self.create_submitters(instance)
        self.set_created_last_modified_and_number(instance)
        return instance
