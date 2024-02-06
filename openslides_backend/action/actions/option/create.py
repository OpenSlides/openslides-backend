from typing import Any

from openslides_backend.shared.schema import id_list_schema

from ....models.models import Option
from ....shared.exceptions import ActionException
from ...generics.create import CreateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..poll_candidate_list.create import PollCandidateListCreate
from ..vote.create import VoteCreate
from ..vote.user_token_helper import get_user_token


@register_action("option.create", action_type=ActionType.BACKEND_INTERNAL)
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
        additional_optional_fields={"poll_candidate_user_ids": id_list_schema},
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        keyword = self.check_one_of_three_keywords(instance)
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
        if keyword == "poll_candidate_user_ids":
            self.apply_instance(instance)
            user_ids = instance.pop("poll_candidate_user_ids")
            self.execute_other_action(
                PollCandidateListCreate,
                [
                    {
                        "option_id": instance["id"],
                        "meeting_id": instance["meeting_id"],
                        "entries": [
                            {"user_id": user_id, "weight": i}
                            for i, user_id in enumerate(user_ids, start=1)
                        ],
                    }
                ],
            )

        return instance

    def get_vote_action_data(
        self, instance: dict[str, Any], value: str, prop: str, user_token: str
    ) -> dict[str, Any] | None:
        if instance.get(prop):
            return {
                "value": value,
                "weight": instance[prop],
                "option_id": instance["id"],
                "user_token": user_token,
            }
        return None

    @staticmethod
    def check_one_of_three_keywords(instance: dict[str, Any]) -> str:
        keys = [
            key
            for key in ("text", "content_object_id", "poll_candidate_user_ids")
            if key in instance
        ]
        if len(keys) != 1:
            raise ActionException(
                "Need one of text, content_object_id or poll_candidate_user_ids."
            )
        return keys[0]
