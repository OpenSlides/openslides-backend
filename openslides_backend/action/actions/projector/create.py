from ....models.models import Meeting, Projector
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector.create")
class ProjectorCreateAction(SequentialNumbersMixin, CreateAction):
    """
    Action to create a projector.
    """

    model = Projector()
    schema = DefaultSchema(Projector()).get_create_schema(
        ["name", "meeting_id"],
        [
            "is_internal",
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
            "chyron_background_color_2",
            "chyron_font_color_2",
            "show_header_footer",
            "show_title",
            "show_logo",
            "show_clock",
            "used_as_reference_projector_meeting_id",
            *Meeting.reverse_default_projectors(),
        ],
    )
    permission = Permissions.Projector.CAN_MANAGE
