from ....models.models import Projector
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector.update")
class ProjectorUpdate(UpdateAction):
    """
    Action to update a projector.
    """

    model = Projector()
    schema = DefaultSchema(Projector()).get_update_schema(
        optional_properties=[
            "name",
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
            "used_as_default_projector_for_agenda_all_items_in_meeting_id",
            "used_as_default_projector_for_topics_in_meeting_id",
            "used_as_default_projector_for_list_of_speakers_in_meeting_id",
            "used_as_default_projector_for_current_list_of_speakers_in_meeting_id",
            "used_as_default_projector_for_motion_in_meeting_id",
            "used_as_default_projector_for_amendment_in_meeting_id",
            "used_as_default_projector_for_motion_block_in_meeting_id",
            "used_as_default_projector_for_assignment_in_meeting_id",
            "used_as_default_projector_for_mediafile_in_meeting_id",
            "used_as_default_projector_for_projector_message_in_meeting_id",
            "used_as_default_projector_for_projector_countdowns_in_meeting_id",
            "used_as_default_projector_for_assignment_poll_in_meeting_id",
            "used_as_default_projector_for_motion_poll_in_meeting_id",
            "used_as_default_projector_for_poll_in_meeting_id",
        ],
    )
    permission = Permissions.Projector.CAN_MANAGE
