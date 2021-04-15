from typing import Any, Dict, Optional

from ....models.models import Option
from ....shared.exceptions import ActionException
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..vote.create import VoteCreate
from ..vote.user_token_helper import get_user_token


@register_action("option.create", internal=True)
class OptionCreateAction(CreateAction):
    """
    (internal) Action to create an option
    """

    model = Option()
    schema = DefaultSchema(Option()).get_create_schema(
        required_properties=["meeting_id"],
        optional_properties=[
            "text",
            "poll_id",
            "used_as_global_option_in_poll_id",
            "content_object_id",
            "yes",
            "no",
            "abstain",
            "weight",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if text xor content_object_id.
        """
        if instance.get("text") and instance.get("content_object_id"):
            raise ActionException("Need text xor content_object_id.")
        if not instance.get("text") and not instance.get("content_object_id"):
            raise ActionException("Need text xor content_object_id.")

        action_data = []
        user_token = get_user_token()
        yes_data = self.get_vote_action_data(instance, "Y", "yes", user_token)
        if yes_data is not None:
            action_data.append(yes_data)
        no_data = self.get_vote_action_data(instance, "N", "no", user_token)
        if no_data is not None:
            action_data.append(no_data)
        abstain_data = self.get_vote_action_data(instance, "A", "abstain", user_token)
        if abstain_data is not None:
            action_data.append(abstain_data)
        if action_data:
            self.apply_instance(instance)
            self.execute_other_action(VoteCreate, action_data)
        return instance

    def get_vote_action_data(
        self, instance: Dict[str, Any], value: str, prop: str, user_token: str
    ) -> Optional[Dict[str, Any]]:
        if instance.get(prop):
            return {
                "value": value,
                "weight": instance[prop],
                "option_id": instance["id"],
                "meeting_id": instance["meeting_id"],
                "user_token": user_token,
            }
        return None
