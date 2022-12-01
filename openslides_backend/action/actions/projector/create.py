from ....models.models import Projector
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
            "used_as_default_agenda_all_items_in_meeting_id",
            "used_as_default_topics_in_meeting_id",
            "used_as_default_list_of_speakers_in_meeting_id",
            "used_as_default_current_list_of_speakers_in_meeting_id",
            "used_as_default_motion_in_meeting_id",
            "used_as_default_amendment_in_meeting_id",
            "used_as_default_motion_block_in_meeting_id",
            "used_as_default_assignment_in_meeting_id",
            "used_as_default_user_in_meeting_id",
            "used_as_default_mediafile_in_meeting_id",
            "used_as_default_projector_message_in_meeting_id",
            "used_as_default_projector_countdowns_in_meeting_id",
            "used_as_default_assignment_poll_in_meeting_id",
            "used_as_default_motion_poll_in_meeting_id",
            "used_as_default_poll_in_meeting_id",
        ],
    )
    permission = Permissions.Projector.CAN_MANAGE
