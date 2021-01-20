from typing import Any, Dict, List, Union

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
        required_properties=["id"],
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
        self.poll = self.fetch_poll(instance["id"])
        value = instance.pop("value")
        user_id = instance.pop("user_id")

        # check for double vote
        if user_id in self.poll.get("voted_ids", []):
            raise ActionException("Only one vote per poll per user allowed.")
        instance["voted_ids"] = self.poll.get("voted_ids", [])
        instance["voted_ids"].append(user_id)

        # check for analog type
        if self.poll.get("type") == "analog":
            raise ActionException("poll.vote is not allowed for analog voting.")

        # handle create the votes.
        if check_value_for_option_vote(value):
            self.validate_option_value(value)
            self.handle_option_value(value, user_id)

        elif check_value_for_global_vote(value):
            self.handle_global_value(value, user_id)

        return instance

    def fetch_poll(self, poll_id: int) -> Dict[str, Any]:
        return self.datastore.get(
            FullQualifiedId(self.model.collection, poll_id),
            [
                "type",
                "option_ids",
                "meeting_id",
                "global_option_id",
                "global_yes",
                "global_no",
                "global_abstain",
                "pollmethod",
                "voted_ids",
            ],
        )

    def validate_option_value(self, value: Dict[str, Any]) -> None:
        for key in value:
            if int(key) not in self.poll.get("option_ids", []):
                raise ActionException(f"Option {key} not in options of the poll.")

    def handle_option_value(self, value: Dict[str, Any], user_id: int) -> None:
        payload: List[Dict[str, Any]] = []
        self._handle_value_keys(value, user_id, payload)
        if payload:
            self.execute_other_action(VoteCreate, payload)

    def _handle_value_keys(
        self,
        value: Dict[str, Any],
        user_id: int,
        payload: List[Dict[str, Any]],
    ) -> None:
        for key in value:
            weight = "1.000000"
            used_value = value[key]

            if self.poll["pollmethod"] in ("Y", "N"):
                weight = "1.000000" if value[key] == 1 else "0.000000"
                used_value = self.poll["pollmethod"]

            if self.check_if_value_allowed_in_pollmethod(used_value):
                payload.append(
                    _get_vote_create_payload(
                        used_value,
                        user_id,
                        int(key),
                        self.poll["meeting_id"],
                        weight,
                    )
                )

    def check_if_value_allowed_in_pollmethod(self, value_str: str) -> bool:
        """
        value_str is 'Y', 'N' or 'A'
        pollmethod is 'Y', 'N', 'YN' or 'YNA'
        """
        return value_str in self.poll.get("pollmethod", "")

    def handle_global_value(self, value: str, user_id: int) -> None:
        for value_check, condition in (
            ("Y", self.poll.get("global_yes")),
            ("N", self.poll.get("global_no")),
            ("A", self.poll.get("global_abstain")),
        ):
            if value == value_check and condition:
                payload = [
                    _get_vote_create_payload(
                        value,
                        user_id,
                        self.poll["global_option_id"],
                        self.poll["meeting_id"],
                        "1.000000",
                    )
                ]
                self.execute_other_action(VoteCreate, payload)


def check_value_for_option_vote(value: Union[str, Dict[str, Any]]) -> bool:
    return isinstance(value, dict)


def check_value_for_global_vote(value: Union[str, Dict[str, Any]]) -> bool:
    return isinstance(value, str)


def _get_vote_create_payload(
    value: str,
    user_id: int,
    option_id: int,
    meeting_id: int,
    weight: str,
) -> Dict[str, Any]:
    return {
        "value": value,
        "weight": weight,
        "user_id": user_id,
        "option_id": option_id,
        "meeting_id": meeting_id,
    }
