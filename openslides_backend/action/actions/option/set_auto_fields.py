from typing import Any

from ....models.models import Option
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("option.set_auto_fields", action_type=ActionType.BACKEND_INTERNAL)
class OptionSetAutoFields(UpdateAction):
    """
    Action to calculate auto fields for options (yes, no, abstain)
    """

    model = Option()
    schema = DefaultSchema(Option()).get_update_schema(
        optional_properties=["yes", "no", "abstain"]
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        set_without_calc = (
            instance.get("yes") or instance.get("no") or instance.get("abstain")
        )
        if not set_without_calc:
            # TODO in this case we should autogenerate the fields.
            raise NotImplementedError()
        return instance
