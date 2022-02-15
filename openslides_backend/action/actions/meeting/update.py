from typing import Any, Dict

from ....models.models import Meeting
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
    has_perm,
    is_admin,
)
from ....permissions.permissions import Permissions
from ....shared.exceptions import MissingPermission, PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.assert_belongs_to_meeting import assert_belongs_to_meeting
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import GetMeetingIdFromIdMixin

meeting_settings_keys = [
    "welcome_title",
    "welcome_text",
    "name",
    "description",
    "location",
    "start_time",
    "end_time",
    "conference_show",
    "conference_auto_connect",
    "conference_los_restriction",
    "conference_stream_url",
    "conference_stream_poster_url",
    "conference_open_microphone",
    "conference_open_video",
    "conference_auto_connect_next_speakers",
    "conference_enable_helpdesk",
    "applause_enable",
    "applause_type",
    "applause_show_level",
    "applause_min_amount",
    "applause_max_amount",
    "applause_timeout",
    "applause_particle_image_url",
    "projector_countdown_default_time",
    "projector_countdown_warning_time",
    "export_csv_encoding",
    "export_csv_separator",
    "export_pdf_pagenumber_alignment",
    "export_pdf_fontsize",
    "export_pdf_pagesize",
    "agenda_show_subtitles",
    "agenda_enable_numbering",
    "agenda_number_prefix",
    "agenda_numeral_system",
    "agenda_item_creation",
    "agenda_new_items_default_visibility",
    "agenda_show_internal_items_on_projector",
    "list_of_speakers_amount_last_on_projector",
    "list_of_speakers_amount_next_on_projector",
    "list_of_speakers_couple_countdown",
    "list_of_speakers_show_amount_of_speakers_on_slide",
    "list_of_speakers_present_users_only",
    "list_of_speakers_show_first_contribution",
    "list_of_speakers_enable_point_of_order_speakers",
    "list_of_speakers_enable_pro_contra_speech",
    "list_of_speakers_can_set_contribution_self",
    "list_of_speakers_speaker_note_for_everyone",
    "list_of_speakers_initially_closed",
    "motions_default_workflow_id",
    "motions_default_amendment_workflow_id",
    "motions_default_statute_amendment_workflow_id",
    "motions_preamble",
    "motions_default_line_numbering",
    "motions_line_length",
    "motions_reason_required",
    "motions_enable_text_on_projector",
    "motions_enable_reason_on_projector",
    "motions_enable_sidebox_on_projector",
    "motions_enable_recommendation_on_projector",
    "motions_show_referring_motions",
    "motions_show_sequential_number",
    "motions_recommendations_by",
    "motions_statute_recommendations_by",
    "motions_recommendation_text_mode",
    "motions_default_sorting",
    "motions_number_type",
    "motions_number_min_digits",
    "motions_number_with_blank",
    "motions_statutes_enabled",
    "motions_amendments_enabled",
    "motions_amendments_in_main_list",
    "motions_amendments_of_amendments",
    "motions_amendments_prefix",
    "motions_amendments_text_mode",
    "motions_amendments_multiple_paragraphs",
    "motions_supporters_min_amount",
    "motions_export_title",
    "motions_export_preamble",
    "motions_export_submitter_recommendation",
    "motions_export_follow_recommendation",
    "motion_poll_ballot_paper_selection",
    "motion_poll_ballot_paper_number",
    "motion_poll_default_type",
    "motion_poll_default_100_percent_base",
    "motion_poll_default_group_ids",
    "motion_poll_default_backend",
    "users_sort_by",
    "users_enable_presence_view",
    "users_enable_vote_weight",
    "users_allow_self_set_present",
    "users_pdf_welcometitle",
    "users_pdf_welcometext",
    "users_pdf_wlan_ssid",
    "users_pdf_wlan_password",
    "users_pdf_wlan_encryption",
    "users_email_sender",
    "users_email_replyto",
    "users_email_subject",
    "users_email_body",
    "assignments_export_title",
    "assignments_export_preamble",
    "assignment_poll_ballot_paper_selection",
    "assignment_poll_ballot_paper_number",
    "assignment_poll_add_candidates_to_list_of_speakers",
    "assignment_poll_sort_poll_result_by_votes",
    "assignment_poll_default_type",
    "assignment_poll_default_method",
    "assignment_poll_default_100_percent_base",
    "assignment_poll_default_group_ids",
    "assignment_poll_default_backend",
    "poll_default_backend",
]


@register_action("meeting.update")
class MeetingUpdate(UpdateAction, GetMeetingIdFromIdMixin):
    model = Meeting()
    schema = DefaultSchema(Meeting()).get_update_schema(
        optional_properties=[
            *meeting_settings_keys,
            "template_for_committee_id",
            "reference_projector_id",
            "organization_tag_ids",
            "jitsi_domain",
            "jitsi_room_name",
            "jitsi_room_password",
            "enable_chat",
            "enable_anonymous",
            "custom_translations",
            "present_user_ids",
            "default_projector_$_id",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_check = []
        if "reference_projector_id" in instance:
            if (
                reference_projector_id := instance["reference_projector_id"]
            ) and reference_projector_id:
                meeting_check.append(
                    FullQualifiedId(Collection("projector"), reference_projector_id)
                )
        if "default_projector_$_id" in instance:
            meeting_check.extend(
                [
                    FullQualifiedId(Collection("projector"), projector_id)
                    for projector_id in instance["default_projector_$_id"].values()
                    if projector_id
                ]
            )

        if meeting_check:
            assert_belongs_to_meeting(self.datastore, meeting_check, instance["id"])
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        # group A check
        if any([field in instance for field in meeting_settings_keys]) and not has_perm(
            self.datastore,
            self.user_id,
            Permissions.Meeting.CAN_MANAGE_SETTINGS,
            instance["id"],
        ):
            raise MissingPermission(Permissions.Meeting.CAN_MANAGE_SETTINGS)

        # group B check
        if "present_user_ids" in instance and not has_perm(
            self.datastore, self.user_id, Permissions.User.CAN_MANAGE, instance["id"]
        ):
            raise MissingPermission(Permissions.User.CAN_MANAGE)

        # group C check
        if (
            "reference_projector_id" in instance or "default_projector_$_id" in instance
        ) and not has_perm(
            self.datastore,
            self.user_id,
            Permissions.Projector.CAN_MANAGE,
            instance["id"],
        ):
            raise MissingPermission(Permissions.Projector.CAN_MANAGE)

        # group D check
        if any(
            [
                field in instance
                for field in [
                    "enable_anonymous",
                    "custom_translations",
                ]
            ]
        ):
            if not is_admin(self.datastore, self.user_id, instance["id"]):
                raise PermissionDenied("Missing permission: Not admin of this meeting")

        # group E check
        if "organization_tag_ids" in instance:
            meeting = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["committee_id"]
            )
            is_manager = has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                meeting["committee_id"],
            )
            if not is_manager:
                raise PermissionDenied(
                    "Missing permission: Not manager and not can_manage_organization"
                )

        # group F check
        if any(
            [
                field in instance
                for field in [
                    "jitsi_domain",
                    "jitsi_room_name",
                    "jitsi_room_password",
                    "enable_chat",
                ]
            ]
        ):

            is_superadmin = has_organization_management_level(
                self.datastore, self.user_id, OrganizationManagementLevel.SUPERADMIN
            )
            if not is_superadmin:
                raise MissingPermission(OrganizationManagementLevel.SUPERADMIN)
