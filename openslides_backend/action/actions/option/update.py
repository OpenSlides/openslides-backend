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

        if "Y" in instance:
            instance["yes"] = instance.pop("Y")
        if "N" in instance:
            instance["no"] = instance.pop("N")
        if "A" in instance:
            instance["abstain"] = instance.pop("A")

        poll_id_option, poll = self._get_poll(instance["id"])
        print(poll_id_option, poll)

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
