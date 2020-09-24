from typing import Any, Dict

from ...models.models import MotionSubmitter
from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action


@register_action("motion_submitter.create")
class MotionSubmitterCreateAction(CreateAction):
    """
    Action to create a motion submitter.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_create_schema(
        properties=["motion_id", "user_id"],
        required_properties=["motion_id", "user_id"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        check if motion and user have the same meeting_id
        """
        motion_meeting_id = self.database.get(
            FullQualifiedId(Collection("motion"), instance["motion_id"]), ["meeting_id"]
        ).get("meeting_id")
        user_meeting_id = self.database.get(
            FullQualifiedId(Collection("user"), instance["user_id"]), ["meeting_id"]
        ).get("meeting_id")

        if motion_meeting_id != user_meeting_id:
            raise ActionException(
                "Cannot create motion_submitter, meeting id of motion and user don't match."
            )
        return instance
