from typing import Any, Dict

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..vote.create import VoteCreate


@register_action("poll.vote")
class PollVote(UpdateAction):
    """
    Action to vote for a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_default_schema(
        title="poll.vote schema",
        description="A schema for the vote action.",
        required_properties=["id", "meeting_id"],
        additional_required_fields={
            "user_id": required_id_schema,
            "value": {
                "anyOf": [
                    {"type": "string", "enum": ["Y", "N", "A"]},
                    {
                        "type": "object",
                        "additionalProperties": {
                            "anyOf": [
                                {"type": "integer"},
                                {"type": "string", "enum": ["Y", "N", "A"]},
                            ]
                        },
                    },
                ]
            },
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:

        # check for type analog
        poll = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            [
                "type",
                "option_ids",
                "meeting_id",
                "global_option_id",
                "global_yes",
                "global_no",
                "global_abstain",
            ],
        )
        if poll.get("type") == "analog":
            raise ActionException("poll.vote is not allowed for analog voting.")

        # extra validation
        value = instance.pop("value")
        user_id = instance.pop("user_id")
        if isinstance(value, dict):
            for key in value:
                if int(key) not in poll.get("option_ids", []):
                    raise ActionException(f"Option {key} not in options of the poll.")
        elif isinstance(value, str):
            self.handle_global_option(value, poll, user_id)

        return instance

    def _get_vote_create_payload(
        self, value: str, user_id: int, option_id: int, meeting_id: int
    ) -> Dict[str, Any]:
        return {
            "value": value,
            "weight": "1.000000",
            "user_id": user_id,
            "option_id": option_id,
            "meeting_id": meeting_id,
        }

    def handle_global_option(
        self, value: str, poll: Dict[str, Any], user_id: int
    ) -> None:
        for value_check, condition in (
            ("Y", poll.get("global_yes")),
            ("N", poll.get("global_no")),
            ("A", poll.get("global_abstain")),
        ):
            if value == value_check and condition:
                payload = [
                    self._get_vote_create_payload(
                        value, user_id, poll["global_option_id"], poll["meeting_id"]
                    )
                ]
                self.execute_other_action(VoteCreate, payload)
