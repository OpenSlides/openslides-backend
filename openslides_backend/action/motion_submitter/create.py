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
        ["motion_id", "user_id"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if motion and user belong to the same meeting if the user is a temporary user.
        """
        motion_meeting_id = self.database.get(
            FullQualifiedId(Collection("motion"), instance["motion_id"]), ["meeting_id"]
        ).get("meeting_id")
        user_meeting_id = self.database.get(
            FullQualifiedId(Collection("user"), instance["user_id"]), ["meeting_id"]
        ).get("meeting_id")

        if user_meeting_id is not None and motion_meeting_id != user_meeting_id:
            raise ActionException(
                "Cannot create motion_submitter, meeting id of motion and (temporary) user don't match."
            )
        return instance
