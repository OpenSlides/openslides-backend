from typing import Any, Dict

from ...models.models import MotionSubmitter
from ...shared.exceptions import ActionException
from ...shared.filters import And, FilterOperator
from ...shared.patterns import Collection, FullQualifiedId
from ..create_action_with_inferred_meeting import CreateActionWithInferredMeetingMixin
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action


@register_action("motion_submitter.create")
class MotionSubmitterCreateAction(CreateActionWithInferredMeetingMixin, CreateAction):
    """
    Action to create a motion submitter.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_create_schema(
        ["motion_id", "user_id"],
    )

    relation_field_for_meeting = "motion_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if motion and user belong to the same meeting if the user is a temporary user.
        """
        instance = self.update_instance_with_meeting_id(instance)
        motion_meeting_id = instance["meeting_id"]  # meeting_id is set from motion
        user_meeting_id = self.database.get(
            FullQualifiedId(Collection("user"), instance["user_id"]), ["meeting_id"]
        ).get("meeting_id")

        if user_meeting_id is not None and motion_meeting_id != user_meeting_id:
            raise ActionException(
                "Cannot create motion_submitter, meeting id of motion and (temporary) user don't match."
            )

        # check, if (user_id, motion_id) already in the databse.
        filter = And(
            FilterOperator("user_id", "=", instance["user_id"]),
            FilterOperator("motion_id", "=", instance["motion_id"]),
        )
        another_exist = self.database.exists(
            collection=self.model.collection, filter=filter
        )
        if another_exist["exists"]:
            raise ActionException("(user_id, motion_id) must be unique.")
        return instance
