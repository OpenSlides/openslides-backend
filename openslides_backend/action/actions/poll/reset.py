from typing import Any, Dict, List

from ....models.models import Poll
from ....services.datastore.interface import GetManyRequest
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..option.set_auto_fields import OptionSetAutoFields
from ..vote.delete import VoteDelete


@register_action("poll.reset")
class PollResetAction(UpdateAction):
    """
    Action to reset a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["state"] = Poll.STATE_CREATED
        self.delete_all_votes(instance["id"])
        return instance

    def delete_all_votes(self, poll_id: int) -> None:
        option_ids = self._get_option_ids(poll_id)
        options = self._get_options(option_ids)
        for option_id in options:
            option = options[option_id]
            if option.get("vote_ids"):
                self._delete_votes(option["vote_ids"])
                self._clear_option_auto_fields(option_id)

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

    def _delete_votes(self, vote_ids: List[int]) -> None:
        payload = []
        for id_ in vote_ids:
            payload.append({"id": id_})
        self.execute_other_action(VoteDelete, payload)

    def _clear_option_auto_fields(self, option_id: int) -> None:
        payload = [
            {
                "id": option_id,
                "yes": "0.000000",
                "no": "0.000000",
                "abstain": "0.000000",
            }
        ]
        self.execute_other_action(OptionSetAutoFields, payload)
