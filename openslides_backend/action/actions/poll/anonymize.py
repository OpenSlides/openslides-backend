from typing import Any

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin

from ....models.models import Poll
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..vote.anonymize import VoteAnonymize
from .mixins import PollHistoryMixin, PollPermissionMixin


@register_action("poll.anonymize")
class PollAnonymize(
    ExtendHistoryMixin, UpdateAction, PollPermissionMixin, PollHistoryMixin
):
    """
    Action to anonymize a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()
    poll_history_information = "anonymized"
    extend_history_to = "content_object_id"

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            self.check_allowed(instance["id"])
            option_ids = self._get_option_ids(instance["id"])
            options = self._get_options(option_ids)

            for option_id in options:
                option = options[option_id]
                if option.get("vote_ids"):
                    self._remove_user_id_from(option["vote_ids"])

            instance["is_pseudoanonymized"] = True
            yield instance

    def check_allowed(self, poll_id: int) -> None:
        poll = self.datastore.get(
            fqid_from_collection_and_id("poll", poll_id), ["type", "state"]
        )

        if not poll.get("state") in (Poll.STATE_FINISHED, Poll.STATE_PUBLISHED):
            raise ActionException(
                "Anonymizing can only be done after finishing a poll."
            )
        if poll.get("type") != Poll.TYPE_NAMED:
            raise ActionException("You can only anonymize named polls.")

    def _get_option_ids(self, poll_id: int) -> list[int]:
        poll = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, poll_id),
            ["option_ids", "global_option_id"],
        )
        option_ids = poll.get("option_ids", [])
        if poll.get("global_option_id"):
            option_ids.append(poll["global_option_id"])
        return option_ids

    def _get_options(self, option_ids: list[int]) -> dict[int, dict[str, Any]]:
        get_many_request = GetManyRequest("option", option_ids, ["vote_ids"])
        gm_result = self.datastore.get_many([get_many_request])
        options: dict[int, dict[str, Any]] = gm_result.get("option", {})
        return options

    def _remove_user_id_from(self, vote_ids: list[int]) -> None:
        action_data = []
        for id_ in vote_ids:
            action_data.append({"id": id_})
        self.execute_other_action(VoteAnonymize, action_data)
