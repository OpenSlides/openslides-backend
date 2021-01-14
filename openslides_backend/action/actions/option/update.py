from typing import Any, Dict, Tuple

from ....models.models import Option
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("option.update")
class OptionUpdateAction(UpdateAction):
    """
    Action to update a user.
    """

    model = Option()
    schema = DefaultSchema(Option()).get_update_schema(
        additional_optional_fields={
            "Y": {"type": "string", "pattern": r"^-?(\d|[1-9]\d+)\.\d{6}$"},
            "N": {"type": "string", "pattern": r"^-?(\d|[1-9]\d+)\.\d{6}$"},
            "A": {"type": "string", "pattern": r"^-?(\d|[1-9]\d+)\.\d{6}$"},
        }
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Update votes and auto calculate yes, no, abstain."""

        poll_id_option, poll = self._get_poll(instance["id"])
        if poll_id_option:
            self._handle_poll_option_data(instance, poll)
        else:
            pass

        return instance

    def _get_poll(self, option_id: int) -> Tuple[bool, Dict[str, Any]]:
        option = self.datastore.get(
            FullQualifiedId(self.model.collection, option_id),
            ["poll_id", "used_as_global_option_in_poll_id"],
        )
        poll_id_option = False
        if option.get("poll_id"):
            poll_id = option["poll_id"]
            poll_id_option = True
        elif option.get("used_as_global_option_in_poll_id"):
            poll_id = option["used_as_global_option_in_poll_id"]
        else:
            raise ActionException("Dont find poll for option")
        return poll_id_option, self.datastore.get(
            FullQualifiedId(Collection("poll"), poll_id), ["type", "pollmethod"]
        )

    def _handle_poll_option_data(
        self, instance: Dict[str, Any], poll: Dict[str, Any]
    ) -> None:
        data = dict()
        if "Y" in instance:
            data["yes"] = instance.pop("Y")
        if "N" in instance:
            data["no"] = instance.pop("N")
        if "A" in instance:
            data["abstain"] = instance.pop("A")

        if poll.get("type") == "analog":
            if poll.get("pollmethod") == "N":
                instance["no"] = data.get("no", "0.000000")
            else:
                instance["yes"] = data.get("yes", "0.000000")
                if poll.get("pollmethod") in ("YN", "YNA"):
                    instance["no"] = data.get("no", "0.000000")
                if poll.get("pollmethod") == "YNA":
                    instance["abstain"] = data.get("abstain", "0.000000")
