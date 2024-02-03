from typing import Any

from ....models.models import Vote
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("vote.anonymize", action_type=ActionType.BACKEND_INTERNAL)
class VoteAnonymize(UpdateAction):
    """
    Action to anonymize a vote by removing the user ids.
    """

    model = Vote()
    schema = DefaultSchema(Vote()).get_update_schema()

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance["user_id"] = None
        instance["delegated_user_id"] = None
        return instance
