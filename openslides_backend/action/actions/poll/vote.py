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
                "pollmethod",
            ],
        )

        # check for analog type
        if poll.get("type") == "analog":
            raise ActionException("poll.vote is not allowed for analog voting.")

        value = instance.pop("value")
        user_id = instance.pop("user_id")

        # handle create the votes.
        if self.check_value_for_option_vote(value):
            self.validate_option_value(value, poll.get("option_ids", []))
            self.handle_option_value(value, poll, user_id)

        elif self.check_value_for_global_vote(value):
            self.handle_global_value(value, poll, user_id)

        return instance

    def check_value_for_option_vote(self, value: Union[str, Dict[str, Any]]) -> bool:
        return isinstance(value, dict)

    def check_value_for_global_vote(self, value: Union[str, Dict[str, Any]]) -> bool:
        return isinstance(value, str)

    def validate_option_value(
        self, value: Dict[str, Any], option_ids: List[int]
    ) -> None:
        for key in value:
            if int(key) not in option_ids:
                raise ActionException(f"Option {key} not in options of the poll.")

    def _get_vote_create_payload(
        self,
        value: str,
        user_id: int,
        option_id: int,
        meeting_id: int,
        weight: str = "1.000000",
    ) -> Dict[str, Any]:
        return {
            "value": value,
            "weight": weight,
            "user_id": user_id,
            "option_id": option_id,
            "meeting_id": meeting_id,
        }

    def handle_option_value(
        self, value: Dict[str, Any], poll: Dict[str, Any], user_id: int
    ) -> None:
        # Different poll methods need to be handle in different ways.
        payload = []

        # handle pollmethod Y and N
        for vote_value in ("Y", "N"):
            if poll.get("pollmethod") == vote_value:
                for key in value:
                    weight = "1.000000" if value[key] == 1 else "0.000000"
                    payload.append(
                        self._get_vote_create_payload(
                            vote_value,
                            user_id,
                            int(key),
                            poll["meeting_id"],
                            weight=weight,
                        )
                    )

        # handle YN, YNA
        if poll.get("pollmethod") in ("YN", "YNA"):
            for key in value:
                if self.check_if_value_allowed_in_pollmethod(
                    value[key], poll["pollmethod"]
                ):
                    payload.append(
                        self._get_vote_create_payload(
                            value[key],
                            user_id,
                            int(key),
                            poll["meeting_id"],
                        )
                    )
        if payload:
            self.execute_other_action(VoteCreate, payload)

    def check_if_value_allowed_in_pollmethod(
        self, value_str: str, pollmethod: str
    ) -> bool:
        """
        value_str is 'Y' or'N' or 'A'
        pollmethod is 'YN' or 'YNA'
        """
        if value_str == "A" and pollmethod == "YN":
            return False
        return True

    def handle_global_value(
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
