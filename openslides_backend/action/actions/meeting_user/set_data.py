from typing import Any, Dict

from ....models.models import MeetingUser
from ....shared.filters import And, FilterOperator
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import MeetingUserCreate


@register_action("meeting_user.set_data", action_type=ActionType.BACKEND_INTERNAL)
class MeetingUserSetData(UpdateAction):
    """
    Action to create, update or delete a meeting_user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_create_schema(
        optional_properties=[
            "id",
            "meeting_id",
            "user_id",
            "comment",
            "number",
            "structure_level",
            "about_me",
            "vote_weight",
            "vote_delegated_to_id",
            "vote_delegations_from_ids",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_id = instance.pop("meeting_id", None)
        user_id = instance.pop("user_id", None)
        meeting_users = self.datastore.filter(
            "meeting_user",
            And(
                FilterOperator("meeting_id", "=", meeting_id),
                FilterOperator("user_id", "=", user_id),
            ),
            ["id"],
        ).values()
        if instance.get("id"):
            if meeting_users:
                assert instance["id"] == next(iter(meeting_users))["id"]
        elif not meeting_users:
            res = self.execute_other_action(
                MeetingUserCreate, [{"meeting_id": meeting_id, "user_id": user_id}]
            )
            instance["id"] = res[0]["id"]  # type: ignore
        else:
            instance["id"] = next(iter(meeting_users))["id"]
        return instance
