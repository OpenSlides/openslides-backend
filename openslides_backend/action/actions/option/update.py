from typing import Any

from ....models.models import Option, Poll
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import decimal_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..poll.functions import check_poll_or_option_perms
from ..poll.set_state import PollSetState
from ..vote.create import VoteCreate
from ..vote.update import VoteUpdate
from ..vote.user_token_helper import get_user_token

option_keys = ("yes", "no", "abstain")
option_keys_map = {key[0].upper(): key for key in option_keys}


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
            "publish_immediately": {"type": "boolean"},
        }
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """Update votes and auto calculate yes, no, abstain."""

        option, poll = self._get_option_and_poll(instance["id"])
        state_change = self.check_state_change(instance, poll)

        if option.get("used_as_global_option_in_poll_id"):
            self._handle_global_option_data(instance, poll)
        else:
            self._handle_poll_option_data(instance, poll)

        id_to_vote = self._fetch_votes(option.get("vote_ids", []))

        action_data_create = []
        action_data_update = []
        user_token = get_user_token()

        for letter, option_key in option_keys_map.items():
            if option_key in instance:
                vote_id = self._get_vote_id(letter, id_to_vote)
                if vote_id is None:
                    action_data_create.append(
                        {
                            "option_id": instance["id"],
                            "value": letter,
                            "weight": instance[option_key],
                            "user_token": user_token,
                        }
                    )
                else:
                    action_data_update.append(
                        {"id": vote_id, "weight": instance[option_key]}
                    )
        if action_data_create:
            self.execute_other_action(VoteCreate, action_data_create)
        if action_data_update:
            self.execute_other_action(VoteUpdate, action_data_update)

        execute_other_action = False
        if state_change:
            state = Poll.STATE_FINISHED
            execute_other_action = True
        if (
            execute_other_action
            or (
                poll["state"] == Poll.STATE_FINISHED
                and poll["type"] == Poll.TYPE_ANALOG
            )
        ) and instance.get("publish_immediately"):
            state = Poll.STATE_PUBLISHED
            execute_other_action = True
        if execute_other_action:
            self.execute_other_action(
                PollSetState, [{"id": poll["id"], "state": state}]
            )

        instance.pop("publish_immediately", None)
        return instance

    def _get_option_and_poll(
        self, option_id: int
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        option = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, option_id),
            ["poll_id", "used_as_global_option_in_poll_id", "vote_ids", "meeting_id"],
        )
        return (
            option,
            self.datastore.get(
                fqid_from_collection_and_id("poll", option["poll_id"]),
                [
                    "id",
                    "state",
                    "type",
                    "pollmethod",
                    "global_yes",
                    "global_no",
                    "global_abstain",
                    "meeting_id",
                    "content_object_id",
                ],
                lock_result=["type"],
            ),
        )

    def _handle_poll_option_data(
        self, instance: dict[str, Any], poll: dict[str, Any]
    ) -> None:
        if poll.get("type") == "analog":
            data = self._get_data(instance)
            pollmethod = poll["pollmethod"]
            for letter, key in option_keys_map.items():
                if letter in pollmethod:
                    instance[key] = data.get(key, "-2.000000")
                elif data.get(key) is not None:
                    raise ActionException(
                        f"Pollmethod {pollmethod} does not support {key} votes"
                    )

    def _handle_global_option_data(
        self, instance: dict[str, Any], poll: dict[str, Any]
    ) -> None:
        if poll.get("type") == "analog":
            data = self._get_data(instance)
            for key in option_keys:
                if poll.get(f"global_{key}") and poll.get("pollmethod") in ("Y", "N"):
                    instance[key] = data.get(key, "-2.000000")
                elif key in data:
                    raise ActionException(
                        f"Global {key} votes are not allowed for this poll"
                    )

    def _get_data(self, instance: dict[str, Any]) -> dict[str, Any]:
        return {
            key: instance.pop(letter)
            for letter, key in option_keys_map.items()
            if letter in instance
        }

    def _fetch_votes(self, vote_ids: list[int]) -> dict[int, dict[str, Any]]:
        get_many_request = GetManyRequest("vote", vote_ids, ["value"])
        gm_result = self.datastore.get_many([get_many_request])
        votes = gm_result.get("vote", {})
        return votes

    def _get_vote_id(
        self, search_value: str, id_to_vote: dict[int, dict[str, Any]]
    ) -> int | None:
        for key, item in id_to_vote.items():
            if item["value"] == search_value:
                return key
        return None

    def check_state_change(
        self, instance: dict[str, Any], poll: dict[str, Any]
    ) -> bool:
        return (
            poll.get("type") == Poll.TYPE_ANALOG
            and poll.get("state") == Poll.STATE_CREATED
            and any(letter in instance for letter in option_keys_map.keys())
        )

    def check_permissions(self, instance: dict[str, Any]) -> None:
        _, poll = self._get_option_and_poll(instance["id"])
        content_object_id = poll.get("content_object_id", "")
        meeting_id = poll["meeting_id"]
        check_poll_or_option_perms(
            content_object_id, self.datastore, self.user_id, meeting_id
        )
