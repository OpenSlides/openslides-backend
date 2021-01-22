from typing import Any, Dict

from ....models.models import Vote
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("vote.remove_user_id", internal=True)
class VoteRemoveUserId(UpdateAction):
    """
    Action to anonymize a vote by removing the user ids.
    """

    model = Vote()
    schema = DefaultSchema(Vote()).get_update_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["user_id"] = None
        return instance
