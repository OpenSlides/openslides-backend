from typing import Any, Dict, List

from ....models.models import Poll
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..vote.anonymize import VoteAnonymize


@register_action("poll.anonymize")
class PollAnonymize(UpdateAction):
    """
    Action to anonymize a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()

    def get_updated_instances(self, payload: ActionData) -> ActionData:
        for instance in payload:

            self.check_allowed(instance["id"])
            option_ids = self._get_option_ids(instance["id"])
            options = self._get_options(option_ids)

            for option_id in options:
                option = options[option_id]
                if option.get("vote_ids"):
                    self._remove_user_id_from(option["vote_ids"])
        return []

    def check_allowed(self, poll_id: int) -> None:
        poll = self.datastore.get(
            FullQualifiedId(Collection("poll"), poll_id), ["type", "state"]
        )

        if not poll.get("state") == Poll.STATE_FINISHED:
            raise ActionException("Anonymize only in state finished allowed.")
        if poll.get("type") == Poll.TYPE_ANALOG:
            raise ActionException("Anonymize is not allowed for type analog.")

    def _get_option_ids(self, poll_id: int) -> List[int]:
        poll = self.datastore.get(
            FullQualifiedId(self.model.collection, poll_id),
            ["option_ids", "global_option_id"],
        )
        option_ids = poll.get("option_ids", [])
        if poll.get("global_option_id"):
            option_ids.append(poll["global_option_id"])
        return option_ids

    def _get_options(self, option_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        get_many_request = GetManyRequest(
            Collection("option"), option_ids, ["vote_ids"]
        )
        gm_result = self.datastore.get_many([get_many_request])
        options: Dict[int, Dict[str, Any]] = gm_result.get(Collection("option"), {})
        return options

    def _remove_user_id_from(self, vote_ids: List[int]) -> None:
        payload = []
        for id_ in vote_ids:
            payload.append({"id": id_})
        self.execute_other_action(VoteAnonymize, payload)
