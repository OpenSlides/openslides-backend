from typing import Any, Dict

from ....models.models import Projector
from ....permissions.permissions import Permissions
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..meeting.shared_meeting import used_as_default_for_schema


@register_action("projector.create")
class ProjectorCreateAction(SequentialNumbersMixin):
    """
    Action to create a projector.
    """

    model = Projector()
    schema = DefaultSchema(Projector()).get_create_schema(
        ["name", "meeting_id"],
        [
            "width",
            "aspect_ratio_numerator",
            "aspect_ratio_denominator",
            "color",
            "background_color",
            "header_background_color",
            "header_font_color",
            "header_h1_color",
            "chyron_background_color",
            "chyron_font_color",
            "show_header_footer",
            "show_title",
            "show_logo",
            "show_clock",
            "used_as_reference_projector_meeting_id",
        ],
        additional_optional_fields={
            "used_as_default_$_in_meeting_id": used_as_default_for_schema,
        },
    )
    permission = Permissions.Projector.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        instance["sequential_number"] = self.get_sequential_number(
            instance["meeting_id"]
        )
        return instance
