from typing import Any, Dict

from ....models.models import Projector
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
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
            "show_header_footer",
            "show_title",
            "show_logo",
            "show_clock",
            "used_as_default_projector_for_agenda_item_list_in_meeting_id",
            "used_as_default_projector_for_topic_in_meeting_id",
            "used_as_default_projector_for_list_of_speakers_in_meeting_id",
            "used_as_default_projector_for_current_list_of_speakers_in_meeting_id",
            "used_as_default_projector_for_motion_in_meeting_id",
            "used_as_default_projector_for_amendment_in_meeting_id",
            "used_as_default_projector_for_motion_block_in_meeting_id",
            "used_as_default_projector_for_assignment_in_meeting_id",
            "used_as_default_projector_for_mediafile_in_meeting_id",
            "used_as_default_projector_for_message_in_meeting_id",
            "used_as_default_projector_for_countdown_in_meeting_id",
            "used_as_default_projector_for_assignment_poll_in_meeting_id",
            "used_as_default_projector_for_motion_poll_in_meeting_id",
            "used_as_default_projector_for_poll_in_meeting_id",
        ],
    )
    permission = Permissions.Projector.CAN_MANAGE

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        super().validate_instance(instance)
        if instance.get("is_internal"):
            projector = self.datastore.get(
                fqid_from_collection_and_id("projector", instance["id"]),
                ["is_internal", "used_as_reference_projector_meeting_id"],
            )
            if projector.get(
                "used_as_reference_projector_meeting_id"
            ) and not projector.get("is_internal"):
                raise ActionException(
                    "Projector cannot be set to internal, because it is the reference projector of the meeting."
                )
