from typing import Any, Dict

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import decimal_schema, optional_fqid_schema
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..option.create import OptionCreateAction
from .base import base_check_100_percent_base

options_schema = {
    "description": "A option inside a poll create schema",
    "type": "object",
    "properties": {
        "text": {"type": "string", "description": "the text of an option"},
        "content_object_id": optional_fqid_schema,
        "Y": decimal_schema,
        "N": decimal_schema,
        "A": decimal_schema,
    },
    "additionalProperties": False,
}


@register_action("poll.create")
class PollCreateAction(CreateAction):
    """
    Action to create a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_create_schema(
        required_properties=["title", "type", "pollmethod", "meeting_id"],
        additional_required_fields={
            "options": {
                "type": "array",
                "items": options_schema,
                "minItems": 1,
            }
        },
        optional_properties=[
            "content_object_id",
            "description",
            "min_votes_amount",
            "max_votes_amount",
            "global_yes",
            "global_no",
            "global_abstain",
            "onehundred_percent_base",
            "majority_method",
            "votesvalid",
            "votesinvalid",
            "votescast",
            "entitled_group_ids",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        action_data = []

        state_change = self.check_state_change(instance)

        # check enabled_electronic_voting
        if instance["type"] in (Poll.TYPE_NAMED, Poll.TYPE_PSEUDOANONYMOUS):
            organisation = self.datastore.get(
                FullQualifiedId(Collection("organisation"), 1),
                ["enable_electronic_voting"],
            )
            if not organisation.get("enable_electronic_voting"):
                raise ActionException("Electronic voting is not allowed.")

        self.check_100_percent_base(instance)

        # handle non-global options
        weight = 1
        unique_set = set()
        for option in instance.get("options", []):
            c_letter = "T" if "text" in option else "C"
            content = (
                option.get("content_object_id")
                if c_letter == "C"
                else option.get("text")
            )
            o_obj = f"{c_letter},{content}"
            if o_obj in unique_set:
                raise ActionException(f"Duplicated option in poll.options: {content}")
            else:
                unique_set.add(o_obj)
            data: Dict[str, Any] = {
                "poll_id": instance["id"],
                "meeting_id": instance["meeting_id"],
                "weight": weight,
            }
            weight += 1
            for key in ("text", "content_object_id"):
                if key in option:
                    data[key] = option[key]
                    if instance["type"] == "analog":
                        if instance["pollmethod"] == "N":
                            data["no"] = self.parse_vote_value(option, "N")
                        else:
                            data["yes"] = self.parse_vote_value(option, "Y")
                            if instance["pollmethod"] in ("YN", "YNA"):
                                data["no"] = self.parse_vote_value(option, "N")
                            if instance["pollmethod"] == "YNA":
                                data["abstain"] = self.parse_vote_value(option, "A")

            action_data.append(data)

        # handle global option
        global_data = {
            "text": "global option",
            "used_as_global_option_in_poll_id": instance["id"],
            "meeting_id": instance["meeting_id"],
            "weight": 1,
        }
        action_data.append(global_data)

        # Execute the create option actions
        additional_relation_models = {
            FullQualifiedId(self.model.collection, instance["id"]): instance
        }
        self.execute_other_action(
            OptionCreateAction, action_data, additional_relation_models
        )

        # set state
        instance["state"] = Poll.STATE_CREATED
        if state_change:
            instance["state"] = Poll.STATE_FINISHED
        if (
            instance["type"] == Poll.TYPE_ANALOG
            and instance["state"] == Poll.STATE_FINISHED
            and instance.get("publish_immediately")
        ):
            instance["state"] = Poll.STATE_PUBLISHED

        # set votescast, votesvalid, votesinvalid defaults
        for field in ("votescast", "votesvalid", "votesinvalid"):
            instance[field] = instance.get(field, "0.000000")

        return instance

    def parse_vote_value(self, data: Dict[str, Any], field: str) -> Any:
        return data.get(field, "-2.000000")

    def check_100_percent_base(self, instance: Dict[str, Any]) -> None:
        pollmethod = instance["pollmethod"]
        onehundred_percent_base = instance.get("onehundred_percent_base")
        base_check_100_percent_base(pollmethod, onehundred_percent_base)

    def check_state_change(self, instance: Dict[str, Any]) -> bool:
        if instance["type"] != Poll.TYPE_ANALOG:
            return False
        check_fields = (
            "votesvalid",
            "votesinvalid",
            "votescast",
        )
        for field in check_fields:
            if instance.get(field):
                return True
        for option in instance.get("options", []):
            if option.get("Y") or option.get("N") or option.get("A"):
                return True
        return False
