from typing import Any

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin
from openslides_backend.services.database.interface import PartialModel

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...mixins.forbid_anonymous_group_mixin import ForbidAnonymousGroupMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .base import base_check_onehundred_percent_base
from .mixins import PollHistoryMixin, PollPermissionMixin


@register_action("poll.update")
class PollUpdateAction(
    ExtendHistoryMixin,
    UpdateAction,
    PollPermissionMixin,
    PollHistoryMixin,
    ForbidAnonymousGroupMixin,
):
    """
    Action to update a poll.
    """

    internal_fields = [
        "entitled_users_at_stop",
    ]

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema(
        optional_properties=[
            "pollmethod",
            "min_votes_amount",
            "max_votes_amount",
            "max_votes_per_option",
            "global_yes",
            "global_no",
            "global_abstain",
            "entitled_group_ids",
            "title",
            "description",
            "onehundred_percent_base",
            "votesvalid",
            "votesinvalid",
            "votescast",
            "backend",
            *internal_fields,
        ],
        additional_optional_fields={
            "publish_immediately": {"type": "boolean"},
        },
    )
    poll_history_information = "updated"
    extend_history_to = "content_object_id"

    def validate_fields(self, instance: dict[str, Any]) -> dict[str, Any]:
        super().validate_instance(instance)
        if not self.internal and any(
            forbidden := {key for key in instance if key in self.internal_fields}
        ):
            raise ActionException(f"data must not contain {forbidden} properties")
        return super().validate_fields(instance)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        poll = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["state", "type", "entitled_users_at_stop"],
        )

        self.check_entitled_users_at_stop(instance, poll)

        state_change = self.check_state_change(instance, poll)

        self.check_onehundred_percent_base(instance)

        not_allowed = []
        if not poll.get("state") == Poll.STATE_CREATED:
            for key in (
                "pollmethod",
                "type",
                "min_votes_amount",
                "max_votes_amount",
                "max_votes_per_option",
                "global_yes",
                "global_no",
                "global_abstain",
                "backend",
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
                "publish_immediately",
            ):
                if key in instance:
                    not_allowed.append(key)

        if not_allowed:
            raise ActionException(
                "Following options are not allowed in this state and type: "
                + ", ".join(not_allowed)
            )
        if poll["type"] == Poll.TYPE_ANALOG and (
            base := instance.get("onehundred_percent_base")
        ) in (
            Poll.ONEHUNDRED_PERCENT_BASE_ENTITLED,
            Poll.ONEHUNDRED_PERCENT_BASE_ENTITLED_PRESENT,
        ):
            raise ActionException(
                f"onehundred_percent_base: value {base} is not allowed for analog."
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

        # set votescast, votesvalid, votesinvalid defaults
        if poll["type"] == Poll.TYPE_ANALOG:
            for field in ("votescast", "votesvalid", "votesinvalid"):
                if field not in instance:
                    instance[field] = "-2.000000"

        instance.pop("publish_immediately", None)
        self.check_anonymous_not_in_list_fields(instance, ["entitled_group_ids"])
        return instance

    def check_onehundred_percent_base(self, instance: dict[str, Any]) -> None:
        onehundred_percent_base = instance.get("onehundred_percent_base")
        if "pollmethod" in instance:
            pollmethod = instance["pollmethod"]
        else:
            poll = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["pollmethod"],
            )
            pollmethod = poll.get("pollmethod")
        base_check_onehundred_percent_base(pollmethod, onehundred_percent_base)

    def check_state_change(
        self, instance: dict[str, Any], poll: dict[str, Any]
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

    def check_entitled_users_at_stop(
        self, instance: dict[str, Any], poll: PartialModel
    ) -> None:
        field = "entitled_users_at_stop"
        if field not in instance:
            return
        if field not in poll:
            raise ActionException(
                "Can not set 'entitled_users_at_stop' via poll.update"
            )
        if not isinstance(instance[field], list) or any(
            entry
            for entry in instance[field]
            if not isinstance(entry, dict) or not entry.get("user_id")
        ):
            raise ActionException("'entitled_users_at_stop' has the wrong format")
        original_main_user_id_to_entry: dict[int, dict[str, Any]] = {
            date["user_id"]: date for date in poll[field]
        }
        new_main_user_id_to_entry: dict[int, dict[str, Any]] = {
            date["user_id"]: date for date in instance[field]
        }
        original_ids = {user_id for user_id in original_main_user_id_to_entry}
        new_ids = {user_id for user_id in new_main_user_id_to_entry}
        if (len(original_ids) != len(new_ids)) or len(original_ids.difference(new_ids)):
            raise ActionException(
                "Can not change essential 'entitled_users_at_stop' data via poll.update"
            )
        if any(
            original_entry.get(field) != new_main_user_id_to_entry[user_id].get(field)
            for user_id, original_entry in original_main_user_id_to_entry.items()
            for field in ["voted", "present", "user_id", "vote_delegated_to_user_id"]
        ):
            raise ActionException(
                "Can not change essential 'entitled_users_at_stop' data via poll.update"
            )
