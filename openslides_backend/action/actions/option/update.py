from typing import Any, Dict, List, Optional, Tuple

from ....models.models import Option
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import decimal_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..vote.create import VoteCreate
from ..vote.update import VoteUpdate


@register_action("option.update")
class OptionUpdateAction(UpdateAction):
    """
    Action to update an option.
    """

    model = Option()
    schema = DefaultSchema(Option()).get_update_schema(
        additional_optional_fields={
            "Y": decimal_schema,
            "N": decimal_schema,
            "A": decimal_schema,
        }
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Update votes and auto calculate yes, no, abstain."""

        poll_id_option, poll, option = self._get_poll(instance["id"])
        if poll_id_option:
            self._handle_poll_option_data(instance, poll)
        else:
            self._handle_global_option_data(instance, poll)

        id_to_vote = self._fetch_votes(option.get("vote_ids", []))

        action_data_create = []
        action_data_update = []
        for field_name, vote_name in (("yes", "Y"), ("no", "N"), ("abstain", "A")):
            if field_name in instance:
                vote_id = self._get_vote_id(vote_name, id_to_vote)
                if vote_id is None:
                    action_data_create.append(
                        {
                            "option_id": instance["id"],
                            "value": vote_name,
                            "weight": instance[field_name],
                            "meeting_id": option["meeting_id"],
                        }
                    )
                else:
                    action_data_update.append(
                        {"id": vote_id, "weight": instance[field_name]}
                    )
        if action_data_create:
            self.execute_other_action(VoteCreate, action_data_create)
        if action_data_update:
            self.execute_other_action(VoteUpdate, action_data_update)

        return instance

    def _get_poll(self, option_id: int) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
        option = self.datastore.get(
            FullQualifiedId(self.model.collection, option_id),
            ["poll_id", "used_as_global_option_in_poll_id", "vote_ids", "meeting_id"],
        )
        poll_id_option = False
        if option.get("poll_id"):
            poll_id = option["poll_id"]
            poll_id_option = True
        elif option.get("used_as_global_option_in_poll_id"):
            poll_id = option["used_as_global_option_in_poll_id"]
        else:
            raise ActionException("Dont find poll for option")
        return (
            poll_id_option,
            self.datastore.get(
                FullQualifiedId(Collection("poll"), poll_id),
                ["type", "pollmethod", "global_yes", "global_no", "global_abstain"],
            ),
            option,
        )

    def _handle_poll_option_data(
        self, instance: Dict[str, Any], poll: Dict[str, Any]
    ) -> None:
        data = self._get_data(instance)

        if poll.get("type") == "analog":
            if poll.get("pollmethod") == "N":
                instance["no"] = data.get("no", "0.000000")
            else:
                instance["yes"] = data.get("yes", "0.000000")
                if poll.get("pollmethod") in ("YN", "YNA"):
                    instance["no"] = data.get("no", "0.000000")
                if poll.get("pollmethod") == "YNA":
                    instance["abstain"] = data.get("abstain", "0.000000")

    def _handle_global_option_data(
        self, instance: Dict[str, Any], poll: Dict[str, Any]
    ) -> None:
        data = self._get_data(instance)

        if poll.get("type") == "analog":
            global_yes_enabled = poll.get("global_yes") and poll.get("pollmethod") in (
                "Y",
                "N",
            )
            if "yes" in data and global_yes_enabled:
                instance["yes"] = data.get("yes", "0.000000")

            global_no_enabled = poll.get("global_no") and poll.get("pollmethod") in (
                "Y",
                "N",
            )
            if "no" in data and global_no_enabled:
                instance["no"] = data.get("no", "0.000000")

            global_abstain_enabled = poll.get("global_abstain") and poll.get(
                "pollmethod"
            ) in ("Y", "N")
            if "abstain" in data and global_abstain_enabled:
                instance["abstain"] = data.get("abstain", "0.000000")

    def _get_data(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = dict()
        if "Y" in instance:
            data["yes"] = instance.pop("Y")
        if "N" in instance:
            data["no"] = instance.pop("N")
        if "A" in instance:
            data["abstain"] = instance.pop("A")
        return data

    def _fetch_votes(self, vote_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        get_many_request = GetManyRequest(Collection("vote"), vote_ids, ["value"])
        gm_result = self.datastore.get_many([get_many_request])
        votes = gm_result.get(Collection("vote"), {})
        return votes

    def _get_vote_id(
        self, search_value: str, id_to_vote: Dict[int, Dict[str, Any]]
    ) -> Optional[int]:
        for key, item in id_to_vote.items():
            if item["value"] == search_value:
                return key
        return None
