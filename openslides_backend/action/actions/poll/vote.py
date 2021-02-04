from decimal import Decimal
from typing import Any, Dict, List, Union

from ....models.models import Poll
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..option.update import OptionUpdate
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

        self.check_user_entitled_groups(user_id)
        self.check_user_is_present_in_meeting(user_id)

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
                "entitled_group_ids",
            ],
        )

    def check_user_entitled_groups(self, user_id: int) -> None:
        group_ids = self.poll.get("entitled_group_ids", [])
        gmr = GetManyRequest(
            Collection("group"),
            group_ids,
            ["user_ids"],
        )
        result = self.datastore.get_many([gmr])
        db_groups = result.get(Collection("group"), {})
        for group in db_groups:
            if user_id in db_groups[group].get("user_ids", []):
                return
        raise ActionException("User is not allowed to vote.")

    def check_user_is_present_in_meeting(self, user_id: int) -> None:
        user = self.datastore.get(
            FullQualifiedId(Collection("user"), user_id), ["is_present_in_meeting_ids"]
        )
        if self.poll["meeting_id"] not in user.get("is_present_in_meeting_ids", []):
            raise ActionException("User is not present in the meeting.")

    def validate_option_value(self, value: Dict[str, Any]) -> None:
        for key in value:
            if int(key) not in self.poll.get("option_ids", []):
                raise ActionException(f"Option {key} not in options of the poll.")

    def handle_option_value(self, value: Dict[str, Any], user_id: int) -> None:
        payload: List[Dict[str, Any]] = []
        self._handle_value_keys(value, user_id, payload)
        if payload:
            self.execute_other_action(VoteCreate, payload)
            for data in payload:
                self.update_option(data["option_id"], data["value"], data["weight"])

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
                self.update_option(
                    payload[0]["option_id"], payload[0]["value"], payload[0]["weight"]
                )

    def update_option(
        self, option_id: int, extra_value: str, extra_weight: str
    ) -> None:
        option = self.datastore.get(
            FullQualifiedId(Collection("option"), option_id), ["vote_ids"]
        )
        vote_ids = option.get("vote_ids", [])
        gmr = GetManyRequest(Collection("vote"), vote_ids, ["weight", "value"])
        result = self.datastore.get_many([gmr])
        votes = result.get(Collection("vote"), {})

        yes = Decimal("0.000000")
        no = Decimal("0.000000")
        abstain = Decimal("0.000000")

        for key in votes:
            vote = votes[key]
            if vote.get("value", "") == "Y":
                yes += Decimal(vote.get("weight", "0"))
            elif vote.get("value", "") == "N":
                no += Decimal(vote.get("weight", "0"))
            elif vote.get("value", "") == "A":
                abstain += Decimal(vote.get("weight", "0"))

        if extra_value == "Y":
            yes += Decimal(extra_weight)
        elif extra_value == "N":
            no += Decimal(extra_weight)
        elif extra_weight == "A":
            abstain += Decimal(extra_weight)

        payload = [
            {"id": option_id, "yes": str(yes), "no": str(no), "abstain": str(abstain)}
        ]
        self.execute_other_action(OptionUpdate, payload)


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
