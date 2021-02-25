from typing import Any, Dict

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll.update")
class PollUpdateAction(UpdateAction):
    """
    Action to update a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema(
        optional_properties=[
            "pollmethod",
            "type",
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
        ]
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        poll = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["state", "type"]
        )

        # check enable_electronic voting
        if instance.get("type") in (Poll.TYPE_NAMED, Poll.TYPE_PSEUDOANONYMOUS):
            organisation = self.datastore.get(
                FullQualifiedId(Collection("organisation"), 1),
                ["enable_electronic_voting"],
            )
            if not organisation.get("enable_electronic_voting"):
                raise ActionException("Electronic voting is not allowed.")

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
        if pollmethod == "Y" and onehundred_percent_base in ("N", "YN", "YNA"):
            raise ActionException(
                "This onehundred_percent_base not allowed in this pollmethod"
            )
        elif pollmethod == "N" and onehundred_percent_base in ("Y", "YN", "YNA"):
            raise ActionException(
                "This onehundred_percent_base not allowed in this pollmethod"
            )
        elif pollmethod == "YN" and onehundred_percent_base == "YNA":
            raise ActionException(
                "This onehundred_percent_base not allowed in this pollmethod"
            )
