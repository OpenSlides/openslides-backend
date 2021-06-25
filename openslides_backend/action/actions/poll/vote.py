from decimal import Decimal
from typing import Any, Dict, List, Optional

from ....models.models import Poll
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..option.set_auto_fields import OptionSetAutoFields
from ..vote.create import VoteCreate
from ..vote.user_token_helper import get_user_token


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
            "value": {"type": ["object", "string"]},
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        self.poll = self.fetch_poll(instance["id"])
        value = instance.pop("value")
        user_id = instance.pop("user_id")

        # check if value not empty
        if not value:
            raise ActionException("Value must contain values.")

        # check if in the started state
        if self.poll.get("state") != Poll.STATE_STARTED:
            raise ActionException("poll.vote is only allowed in started state.")

        # check for double vote
        if user_id in self.poll.get("voted_ids", []):
            raise ActionException("Only one vote per poll per user allowed.")
        instance["voted_ids"] = self.poll.get("voted_ids", [])
        instance["voted_ids"].append(user_id)
        instance["votescast"] = f"{len(instance['voted_ids'])}.000000"

        # check for analog type
        if self.poll.get("type") == "analog":
            raise ActionException("poll.vote is not allowed for analog voting.")

        self.check_user_entitled_groups(user_id)
        self.check_user_is_present_in_meeting(user_id)

        # handle create the votes.
        if isinstance(value, dict):
            self.validate_option_value(value)
            self.handle_option_value(value, user_id, instance)

        elif isinstance(value, str):
            self.validate_global_value(value)
            self.handle_global_value(value, user_id, instance)

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
                "state",
                "votesvalid",
                "min_votes_amount",
                "max_votes_amount",
            ],
        )

    def check_user_entitled_groups(self, user_id: int) -> None:
        group_ids = self.poll.get("entitled_group_ids", [])
        meeting_id = self.poll["meeting_id"]
        user = self.datastore.get(
            FullQualifiedId(Collection("user"), user_id), [f"group_${meeting_id}_ids"]
        )
        for id_ in user.get(f"group_${meeting_id}_ids", []):
            if id_ in group_ids:
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
            if not key.isdigit():
                raise ActionException(f"Option {key} is not an int.")
            if int(key) not in self.poll.get("option_ids", []):
                raise ActionException(f"Option {key} not in options of the poll.")
            if not (
                (isinstance(value[key], int) and value[key] in (0, 1))
                or (
                    isinstance(value[key], str)
                    and value[key] in self.poll["pollmethod"]
                )
            ):
                raise ActionException(
                    f"Option {key} has not a right value. (int, str)."
                )

    def validate_global_value(self, value: str) -> None:
        if value not in ("Y", "N", "A"):
            raise ActionException(f"Option value {value} is not in 'YNA'.")
        elif value == "Y" and not self.poll.get("global_yes"):
            raise ActionException("Global value Y not allowed.")
        elif value == "N" and not self.poll.get("global_no"):
            raise ActionException("Global value N not allowed.")
        elif value == "A" and not self.poll.get("global_abstain"):
            raise ActionException("Global value A not allowed.")

    def handle_option_value(
        self, value: Dict[str, Any], user_id: int, instance: Dict[str, Any]
    ) -> None:
        action_data: List[Dict[str, Any]] = []
        self._handle_value_keys(value, user_id, action_data)
        if action_data:
            self.execute_other_action(VoteCreate, action_data)
            total_votes = 0
            for data in action_data:
                self.update_option(data["option_id"], data["value"], data["weight"])
                self.update_votes_valid(instance, data["weight"])
                total_votes += 1
            self.check_total_votes(total_votes)

    def _handle_value_keys(
        self,
        value: Dict[str, Any],
        user_id: int,
        action_data: List[Dict[str, Any]],
    ) -> None:
        vote_weight = self.get_vote_weigth(user_id)
        user_token = get_user_token()

        for key in value:
            weight = vote_weight
            used_value = value[key]

            if self.poll["pollmethod"] in ("Y", "N"):
                if value[key] == 0:
                    continue
                weight = vote_weight
                used_value = self.poll["pollmethod"]

            if self.check_if_value_allowed_in_pollmethod(used_value):
                action_data.append(
                    self._get_vote_create_action_data(
                        used_value,
                        user_id,
                        int(key),
                        self.poll["meeting_id"],
                        weight,
                        user_token,
                    )
                )

    def get_vote_weigth(self, user_id: int) -> str:
        meeting_id = self.poll["meeting_id"]
        field_id = f"vote_weight_${meeting_id}"
        user = self.datastore.get(
            FullQualifiedId(Collection("user"), user_id),
            [field_id, "default_vote_weight"],
        )
        vote_weight = user.get(field_id)
        if vote_weight is None:
            vote_weight = user.get("default_vote_weight")
        if vote_weight is None:
            vote_weight = "1.000000"
        return vote_weight

    def check_if_value_allowed_in_pollmethod(self, value_str: str) -> bool:
        """
        value_str is 'Y', 'N' or 'A'
        pollmethod is 'Y', 'N', 'YN' or 'YNA'
        """
        return value_str in self.poll.get("pollmethod", "")

    def handle_global_value(
        self, value: str, user_id: int, instance: Dict[str, Any]
    ) -> None:
        user_token = get_user_token()

        for value_check, condition in (
            ("Y", self.poll.get("global_yes")),
            ("N", self.poll.get("global_no")),
            ("A", self.poll.get("global_abstain")),
        ):
            if value == value_check and condition:
                action_data = [
                    self._get_vote_create_action_data(
                        value,
                        user_id,
                        self.poll["global_option_id"],
                        self.poll["meeting_id"],
                        "1.000000",
                        user_token,
                    )
                ]
                self.execute_other_action(VoteCreate, action_data)
                self.update_option(
                    action_data[0]["option_id"],
                    action_data[0]["value"],
                    action_data[0]["weight"],
                )
                self.update_votes_valid(instance, action_data[0]["weight"])

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
        elif extra_value == "A":
            abstain += Decimal(extra_weight)

        action_data = [
            {"id": option_id, "yes": str(yes), "no": str(no), "abstain": str(abstain)}
        ]
        self.execute_other_action(OptionSetAutoFields, action_data)

    def update_votes_valid(self, instance: Dict[str, Any], extra_weight: str) -> None:
        votesvalid = Decimal(self.poll.get("votesvalid", "0.000000")) + Decimal(
            extra_weight
        )
        instance["votesvalid"] = str(votesvalid)

    def _get_vote_create_action_data(
        self,
        value: str,
        user_id: Optional[int],
        option_id: int,
        meeting_id: int,
        weight: str,
        user_token: str,
    ) -> Dict[str, Any]:
        if self.poll.get("type") == Poll.TYPE_PSEUDOANONYMOUS:
            user_id = None
        return {
            "value": value,
            "weight": weight,
            "user_id": user_id,
            "option_id": option_id,
            "user_token": user_token,
            "meeting_id": meeting_id,
        }

    def check_total_votes(self, total: int) -> None:
        if self.poll["pollmethod"] in ("Y", "N") and not (
            self.poll.get("min_votes_amount", 1)
            <= total
            <= self.poll.get("max_votes_amount", 1)
        ):
            raise ActionException("Total amount of votes is not in min-max-interval.")

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        return
