from typing import Any

from openslides_backend.shared.exceptions import ActionException

from ....models.models import MeetingMediafile
from ...generics.create import CreateAction
from ...mixins.meeting_mediafile_helper import get_meeting_mediafile_filter
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action

relations_to_group = ["access_group_ids", "inherited_access_group_ids"]

extra_relations_to_meeting = [
    "used_as_font_bold_in_meeting_id",
    "used_as_font_bold_italic_in_meeting_id",
    "used_as_font_chyron_speaker_name_in_meeting_id",
    "used_as_font_italic_in_meeting_id",
    "used_as_font_monospace_in_meeting_id",
    "used_as_font_projector_h1_in_meeting_id",
    "used_as_font_projector_h2_in_meeting_id",
    "used_as_font_regular_in_meeting_id",
    "used_as_logo_pdf_ballot_paper_in_meeting_id",
    "used_as_logo_pdf_footer_l_in_meeting_id",
    "used_as_logo_pdf_footer_r_in_meeting_id",
    "used_as_logo_pdf_header_l_in_meeting_id",
    "used_as_logo_pdf_header_r_in_meeting_id",
    "used_as_logo_projector_header_in_meeting_id",
    "used_as_logo_projector_main_in_meeting_id",
    "used_as_logo_web_header_in_meeting_id",
]


@register_action("meeting_mediafile.create", action_type=ActionType.BACKEND_INTERNAL)
class MeetingMediafileCreate(CreateAction):
    """
    Action to create a meeting mediafile.
    This only adds data, calculations will have to be done in calling class.
    """

    model = MeetingMediafile()
    schema = DefaultSchema(MeetingMediafile()).get_create_schema(
        required_properties=["meeting_id", "mediafile_id", "is_public"],
        optional_properties=relations_to_group + extra_relations_to_meeting,
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if self.datastore.exists(
            "meeting_mediafile",
            get_meeting_mediafile_filter(
                instance["meeting_id"], instance["mediafile_id"]
            ),
            lock_result=False,
        ):
            raise ActionException(
                f"MeetingMediafile instance with mediafile {instance['mediafile_id']} and meeting {instance['meeting_id']} already exists"
            )
        return super().update_instance(instance)
