from typing import Any, Dict

from ....models.models import Option
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
        return instance
