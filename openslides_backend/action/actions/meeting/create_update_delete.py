from typing import Any, Dict, List

from ....models.models import Meeting
from ...action_set import ActionSet
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set
from ..group.create import GroupCreate
from ..motion_workflow.create import MotionWorkflowCreateSimpleWorkflowAction

meeting_settings_keys = [
    "welcome_title",
    "welcome_text",
    "name",
    "description",
    "location",
    "start_time",
    "end_time",
    "url_name",
    "enable_anonymous",
    "conference_show",
    "conference_auto_connect",
    "conference_los_restriction",
    "conference_stream_url",
    "conference_stream_poster_url",
    "projector_default_countdown_time",
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
    "motion_poll_default_majority_method",
    "motion_poll_default_group_ids",
    "users_sort_by",
    "users_enable_presence_view",
    "users_enable_vote_weight",
    "users_allow_self_set_present",
    "users_pdf_welcometitle",
    "users_pdf_welcometext",
    "users_pdf_url",
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
    "assignment_poll_default_majority_method",
    "assignment_poll_default_group_ids",
]


class MeetingCreate(CreateAction):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        instance = self._create_default_group(instance)
        instance = self._create_admin_group(instance)
        instance = self._create_delegates_group(instance)
        instance = self._create_staff_group(instance)
        instance = self._create_committees_group(instance)
        instance = self._create_motion_workflow(
            instance,
            "Simple Workflow",
            [
                "default_workflow_meeting_id",
                "default_amendment_workflow_meeting_id",
                "default_statute_amendment_workflow_meeting_id",
                "meeting_id",
            ],
        )
        return instance

    def _create_default_group(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        additional_dict = {
            "name": "Default",
            "permissions": [
                "agenda_item.can_see_internal",
                "assignment.can_see",
                "list_of_speakers.can_see",
                "mediafile.can_see",
                "meeting.can_see_frontpage",
                "motion.can_see",
                "projector.can_see",
                "user.can_see",
                "user.can_change_own_password",
            ],
        }
        instance = self.concurrent_create_per_execute_other_action(
            instance,
            GroupCreate,
            [
                "meeting_id",
                "default_group_for_meeting_id",
            ],
            additional_dict,
        )
        return instance

    def _create_admin_group(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        additional_dict = {"name": "Admin"}
        instance = self.concurrent_create_per_execute_other_action(
            instance,
            GroupCreate,
            [
                "meeting_id",
                "admin_group_for_meeting_id",
            ],
            additional_dict,
        )
        return instance

    def _create_delegates_group(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        additional_dict = {
            "name": "Delegates",
            "permissions": [
                "agenda_item.can_see_internal",
                "assignment.can_nominate_other",
                "assignment.can_nominate_self",
                "list_of_speakers.can_be_speaker",
                "mediafile.can_see",
                "meeting.can_see_autopilot",
                "meeting.can_see_frontpage",
                "motion.can_create",
                "motion.can_create_amendments",
                "motion.can_support",
                "projector.can_see",
                "user.can_see",
                "user.can_change_own_password",
            ],
        }
        instance = self.concurrent_create_per_execute_other_action(
            instance,
            GroupCreate,
            [
                "meeting_id",
            ],
            additional_dict,
        )
        return instance

    def _create_staff_group(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        additional_dict = {
            "name": "Staff",
            "permissions": [
                "agenda_item.can_manage",
                "assignment.can_manage",
                "assignment.can_nominate_self",
                "list_of_speakers.can_be_speaker",
                "list_of_speakers.can_manage",
                "mediafile.can_manage",
                "meeting.can_see_frontpage",
                "meeting.can_see_history",
                "motion.can_manage",
                "projector.can_manage",
                "tag.can_manage",
                "user.can_manage",
                "user.can_change_own_password",
            ],
        }
        instance = self.concurrent_create_per_execute_other_action(
            instance,
            GroupCreate,
            [
                "meeting_id",
            ],
            additional_dict,
        )
        return instance

    def _create_committees_group(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        additional_dict = {
            "name": "Committees",
            "permissions": [
                "agenda_item.can_see_internal",
                "assignment.can_see",
                "list_of_speakers.can_see",
                "mediafile.can_see",
                "meeting.can_see_frontpage",
                "motion.can_create",
                "motion.can_create_amendments",
                "motion.can_support",
                "projector.can_see",
                "user.can_see",
            ],
        }
        instance = self.concurrent_create_per_execute_other_action(
            instance,
            GroupCreate,
            [
                "meeting_id",
            ],
            additional_dict,
        )
        return instance

    def _create_motion_workflow(
        self, instance: Dict[str, Any], name: str, fields: List[str]
    ) -> Dict[str, Any]:
        additional_dict = {"name": name}
        instance = self.concurrent_create_per_execute_other_action(
            instance,
            MotionWorkflowCreateSimpleWorkflowAction,
            fields,
            additional_dict,
        )
        return instance


@register_action_set("meeting")
class MeetingActionSet(ActionSet):
    """
    Actions to create, update and delete meetings.
    """

    model = Meeting()
    create_schema = DefaultSchema(Meeting()).get_create_schema(
        required_properties=["committee_id", "name", "welcome_title"],
        optional_properties=[
            "welcome_text",
            "description",
            "location",
            "start_time",
            "end_time",
            "url_name",
            "enable_anonymous",
            "guest_ids",
        ],
    )
    update_schema = DefaultSchema(Meeting()).get_update_schema(
        optional_properties=[
            *meeting_settings_keys,
            "template_for_committee_id",
            "guest_ids",
        ],
    )
    delete_schema = DefaultSchema(Meeting()).get_delete_schema()

    CreateActionClass = MeetingCreate
