from typing import Any

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import collection_from_fqid, fqid_from_collection_and_id
from ....shared.schema import decimal_schema, id_list_schema, optional_fqid_schema
from ...generics.create import CreateAction
from ...mixins.forbid_anonymous_group_mixin import ForbidAnonymousGroupMixin
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..option.create import OptionCreateAction
from .base import base_check_onehundred_percent_base
from .mixins import PollHistoryMixin, PollPermissionMixin, PollValidationMixin

options_schema = {
    "description": "A option inside a poll create schema",
    "type": "object",
    "properties": {
        "text": {"type": "string", "description": "the text of an option"},
        "content_object_id": optional_fqid_schema,
        "poll_candidate_user_ids": id_list_schema,
        "Y": decimal_schema,
        "N": decimal_schema,
        "A": decimal_schema,
    },
    "additionalProperties": False,
}


@register_action("poll.create")
class PollCreateAction(
    PollValidationMixin,
    SequentialNumbersMixin,
    CreateAction,
    PollPermissionMixin,
    PollHistoryMixin,
    ForbidAnonymousGroupMixin,
):
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
            "max_votes_per_option",
            "global_yes",
            "global_no",
            "global_abstain",
            "onehundred_percent_base",
            "votesvalid",
            "votesinvalid",
            "votescast",
            "entitled_group_ids",
            "backend",
            "live_voting_enabled",
        ],
        additional_optional_fields={
            "publish_immediately": {"type": "boolean"},
            "amount_global_yes": decimal_schema,
            "amount_global_no": decimal_schema,
            "amount_global_abstain": decimal_schema,
        },
    )
    poll_history_information = "created"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        action_data = []

        state_change = self.check_state_change(instance)
        is_motion_poll = collection_from_fqid(instance["content_object_id"]) == "motion"
        is_assignment_poll = (
            collection_from_fqid(instance["content_object_id"]) == "assignment"
        )

        # check enabled_electronic_voting
        if instance["type"] in (Poll.TYPE_NAMED, Poll.TYPE_PSEUDOANONYMOUS):
            organization = self.datastore.get(
                ONE_ORGANIZATION_FQID,
                ["enable_electronic_voting"],
            )
            if not organization.get("enable_electronic_voting"):
                raise ActionException("Electronic voting is not allowed.")

        # check named and live_voting_enabled
        if instance.get("live_voting_enabled") and not (
            instance["type"] == Poll.TYPE_NAMED
            and (
                is_motion_poll
                or (
                    is_assignment_poll
                    and not instance.get("global_yes")
                    and instance["pollmethod"] == "Y"
                    and instance.get("max_votes_amount") == 1
                )
            )
        ):
            raise ActionException(
                "live_voting_enabled only allowed for named motion polls and named Yes assignment polls."
            )

        # check entitled_group_ids and analog
        if instance["type"] == Poll.TYPE_ANALOG and "entitled_group_ids" in instance:
            raise ActionException("entitled_group_ids is not allowed for analog.")
        # check analog and onehundredpercentbase entitled
        if instance["type"] == Poll.TYPE_ANALOG and (
            base := instance.get("onehundred_percent_base")
        ) in (
            Poll.ONEHUNDRED_PERCENT_BASE_ENTITLED,
            Poll.ONEHUNDRED_PERCENT_BASE_ENTITLED_PRESENT,
        ):
            raise ActionException(
                f"onehundred_percent_base: value {base} is not allowed for analog."
            )
        self.check_onehundred_percent_base(instance)

        # check non-analog and publish_immediately
        if instance["type"] != Poll.TYPE_ANALOG and "publish_immediately" in instance:
            raise ActionException("publish_immediately only allowed for analog polls.")

        # check content_object_id motion and state allow_create_poll
        if is_motion_poll:
            motion = self.datastore.get(instance["content_object_id"], ["state_id"])
            if not motion.get("state_id"):
                raise ActionException("Motion doesn't have a state.")
            state = self.datastore.get(
                fqid_from_collection_and_id("motion_state", motion["state_id"]),
                ["allow_create_poll"],
            )
            if not state.get("allow_create_poll"):
                raise ActionException("Motion state doesn't allow to create poll.")

        # handle non-global options
        unique_set = set()

        for weight, option in enumerate(instance.get("options", []), start=1):
            # check the keys with staticmethod from option.create, where they belong
            key = OptionCreateAction.check_one_of_three_keywords(option)
            data: dict[str, Any] = {
                "poll_id": instance["id"],
                "meeting_id": instance["meeting_id"],
                "weight": weight,
                key: option[key],
            }

            o_obj = f"{key},{option[key]}"
            if o_obj in unique_set:
                raise ActionException(
                    f"Duplicated option in poll.options: {option[key]}"
                )
            else:
                unique_set.add(o_obj)

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
        if instance["type"] == "analog":
            for option in ["yes", "no", "abstain"]:
                if instance["type"] == "analog" and instance.get(f"global_{option}"):
                    global_data[option] = self.parse_vote_value(
                        instance, f"amount_global_{option}"
                    )
                instance.pop(f"amount_global_{option}", None)
        action_data.append(global_data)

        # Execute the create option actions
        self.apply_instance(instance)
        self.execute_other_action(
            OptionCreateAction,
            action_data,
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
            instance[field] = (
                self.parse_vote_value(instance, field)
                if instance["type"] == Poll.TYPE_ANALOG
                else instance.get(field, "0.000000")
            )

        # calculate is_pseudoanonymized
        instance["is_pseudoanonymized"] = instance["type"] == Poll.TYPE_PSEUDOANONYMOUS

        instance.pop("options", None)
        instance.pop("publish_immediately", None)
        self.check_anonymous_not_in_list_fields(instance, ["entitled_group_ids"])
        return instance

    def parse_vote_value(self, data: dict[str, Any], field: str) -> Any:
        return data.get(field, "-2.000000")

    def check_onehundred_percent_base(self, instance: dict[str, Any]) -> None:
        pollmethod = instance["pollmethod"]
        onehundred_percent_base = instance.get("onehundred_percent_base")
        base_check_onehundred_percent_base(pollmethod, onehundred_percent_base)

    def check_state_change(self, instance: dict[str, Any]) -> bool:
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
