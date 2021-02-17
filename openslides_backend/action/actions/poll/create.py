from typing import Any, Dict

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import decimal_schema, optional_fqid_schema
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..option.create import OptionCreateAction

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
                "uniqueItems": True,
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
        additional_optional_fields={
            "amount_global_yes": decimal_schema,
            "amount_global_no": decimal_schema,
            "amount_global_abstain": decimal_schema,
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        payload = []

        # check enabled_electronic_voting
        if instance["type"] in (Poll.TYPE_NAMED, Poll.TYPE_PSEUDOANONYMOUS):
            organisation = self.datastore.get(
                FullQualifiedId(Collection("organisation"), 1),
                ["enable_electronic_voting"],
            )
            if not organisation.get("enable_electronic_voting"):
                raise ActionException("Electronic voting is not allowed.")

        # handle non-global options
        weight = 1
        for option in instance.get("options", []):
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

            payload.append(data)

        # handle global option
        global_data = {
            "text": "global option",
            "used_as_global_option_in_poll_id": instance["id"],
            "meeting_id": instance["meeting_id"],
            "weight": 1,
        }
        if instance["type"] == "analog":
            global_yes_enabled = instance["global_yes"] and instance["pollmethod"] in (
                "Y",
                "N",
            )
            if "amount_global_yes" in instance and global_yes_enabled:
                global_data["yes"] = self.parse_vote_value(
                    instance, "amount_global_yes"
                )

            global_no_enabled = instance["global_no"] and instance["pollmethod"] in (
                "Y",
                "N",
            )
            if "amount_global_no" in instance and global_no_enabled:
                global_data["no"] = self.parse_vote_value(instance, "amount_global_no")

            global_abstain_enabled = instance["global_abstain"] and instance[
                "pollmethod"
            ] in ("Y", "N")
            if "amount_global_abstain" in instance and global_abstain_enabled:
                global_data["abstain"] = self.parse_vote_value(
                    instance, "amount_global_abstain"
                )
        payload.append(global_data)

        # Execute the create option actions
        additional_relation_models = {
            FullQualifiedId(self.model.collection, instance["id"]): instance
        }
        self.execute_other_action(
            OptionCreateAction, payload, additional_relation_models
        )

        # set state
        instance["state"] = "created"
        if instance["type"] == "analog":
            instance["state"] = "finished"
            if instance.get("publish_immediately"):
                instance["state"] = "published"

        # set votescast, votesvalid, votesinvalid defaults
        for field in ("votescast", "votesvalid", "votesinvalid"):
            instance[field] = instance.get(field, "0.000000")

        return instance

    def parse_vote_value(self, data: Dict[str, Any], field: str) -> Any:
        return data.get(field, "0.000000")
