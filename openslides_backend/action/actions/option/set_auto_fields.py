from typing import Any, Dict

from ....models.models import Option
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("option.set_auto_fields", internal=True)
class OptionSetAutoFields(UpdateAction):
    """
    Action to calculate auto fields for options (yes, no, abstain)
    """

    model = Option()
    schema = DefaultSchema(Option()).get_update_schema(
        optional_properties=["yes", "no", "abstain"]
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        set_without_calc = (
            instance.get("yes") or instance.get("no") or instance.get("abstain")
        )
        if not set_without_calc:
            # TODO in this case we should autogenerate the fields.
            raise NotImplementedError
        return instance
