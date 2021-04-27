from typing import Any, Dict

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .base import base_check_100_percent_base
from .mixins import PollPermissionMixin


@register_action("poll.update")
class PollUpdateAction(UpdateAction, PollPermissionMixin):
    """
    Action to update a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema(
        optional_properties=[
            "pollmethod",
            "min_votes_amount",
            "max_votes_amount",
            "global_yes",
            "global_no",
            "global_abstain",
            "entitled_group_ids",
            "title",
            "description",
            "onehundred_percent_base",
            "majority_method",
            "votesvalid",
            "votesinvalid",
            "votescast",
        ],
        additional_optional_fields={
            "publish_immediately": {"type": "boolean"},
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        poll = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["state", "type"]
        )

        state_change = self.check_state_change(instance, poll)

        self.check_100_percent_base(instance)

        not_allowed = []
        if not poll.get("state") == Poll.STATE_CREATED:
            for key in (
                "pollmethod",
                "type",
                "min_votes_amount",
                "max_votes_amount",
                "global_yes",
                "global_no",
                "global_abstain",
            ):
                if key in instance:
                    not_allowed.append(key)
        if (
            poll.get("state") != Poll.STATE_CREATED
            or poll.get("type") == Poll.TYPE_ANALOG
        ):
            if "entitled_group_ids" in instance:
                not_allowed.append("entitled_group_ids")
        if not poll.get("type") == Poll.TYPE_ANALOG:
            for key in (
                "votesvalid",
                "votesinvalid",
                "votescast",
            ):
                if key in instance:
                    not_allowed.append(key)
        if not_allowed:
            raise ActionException(
                "Following options are not allowed in this state and type: "
                + ", ".join(not_allowed)
            )
        if state_change:
            instance["state"] = Poll.STATE_FINISHED
        if (
            poll["type"] == Poll.TYPE_ANALOG
            and (
                instance.get("state") == Poll.STATE_FINISHED
                or poll["state"] == Poll.STATE_FINISHED
            )
            and instance.get("publish_immediately")
        ):
            instance["state"] = Poll.STATE_PUBLISHED

        return instance

    def check_100_percent_base(self, instance: Dict[str, Any]) -> None:
        onehundred_percent_base = instance.get("onehundred_percent_base")
        if "pollmethod" in instance:
            pollmethod = instance["pollmethod"]
        else:
            poll = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["pollmethod"]
            )
            pollmethod = poll.get("pollmethod")
        base_check_100_percent_base(pollmethod, onehundred_percent_base)

    def check_state_change(
        self, instance: Dict[str, Any], poll: Dict[str, Any]
    ) -> bool:
        if poll.get("type") != Poll.TYPE_ANALOG:
            return False
        if poll.get("state") != Poll.STATE_CREATED:
            return False
        check_fields = (
            "votesvalid",
            "votesinvalid",
            "votescast",
        )
        for field in check_fields:
            if instance.get(field):
                return True
        return False
