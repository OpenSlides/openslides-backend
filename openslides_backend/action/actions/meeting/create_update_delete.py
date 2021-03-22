from typing import Any, Dict, Iterable, List, Type, cast

from ....models.models import Meeting
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action
from ...action_set import ActionSet
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set
from ..group.create import GroupCreate
from ..motion_workflow.create import MotionWorkflowCreateSimpleWorkflowAction
from ..projector.create import ProjectorCreateAction
from ..projector_countdown.create import ProjectorCountdownCreate
from ..user.update import UserUpdate
from .shared_meeting import meeting_projector_default_replacements

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


class MeetingCreate(CreateActionWithDependencies):
    dependencies = [
        MotionWorkflowCreateSimpleWorkflowAction,
        ProjectorCreateAction,
    ]

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)

        action_data = [
            {
                "name": "Default",
                "meeting_id": instance["id"],
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
            },
            {
                "name": "Admin",
                "meeting_id": instance["id"],
            },
            {
                "name": "Delegates",
                "meeting_id": instance["id"],
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
            },
            {
                "name": "Staff",
                "meeting_id": instance["id"],
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
            },
            {
                "name": "Committees",
                "meeting_id": instance["id"],
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
            },
        ]
        action_results = self.execute_other_action(GroupCreate, action_data)

        fqid_default_group = FullQualifiedId(
            Collection("group"), action_results[0]["id"]  # type: ignore
        )
        fqid_admin_group = FullQualifiedId(Collection("group"), action_results[1]["id"])  # type: ignore
        assert (
            self.datastore.additional_relation_models[fqid_default_group]["name"]
            == "Default"
        )
        assert (
            self.datastore.additional_relation_models[fqid_admin_group]["name"]
            == "Admin"
        )
        instance["default_group_id"] = fqid_default_group.id
        instance["admin_group_id"] = fqid_admin_group.id

        # Add user to admin group
        action_data = [
            {
                "id": self.user_id,
                "group_$_ids": {str(instance["id"]): [fqid_admin_group.id]},
            }
        ]
        self.execute_other_action(UserUpdate, action_data)
        action_data_countdowns = [
            {
                "title": "List of speakers countdown",
                "meeting_id": instance["id"],
                "used_as_list_of_speaker_countdown_meeting_id": instance["id"],
                "default_time": instance["projector_countdown_default_time"],
            },
            {
                "title": "Voting countdown",
                "meeting_id": instance["id"],
                "used_as_poll_countdown_meeting_id": instance["id"],
                "default_time": instance["projector_countdown_default_time"],
            },
        ]
        self.execute_other_action(
            ProjectorCountdownCreate,
            action_data_countdowns,
        )
        return instance

    def get_dependent_action_data(
        self, instance: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> List[Dict[str, Any]]:
        if CreateActionClass == MotionWorkflowCreateSimpleWorkflowAction:
            return [
                {
                    "name": "Simple Workflow",
                    "default_workflow_meeting_id": instance["id"],
                    "default_amendment_workflow_meeting_id": instance["id"],
                    "default_statute_amendment_workflow_meeting_id": instance["id"],
                    "meeting_id": instance["id"],
                }
            ]
        elif CreateActionClass == ProjectorCreateAction:
            return [
                {
                    "name": "Default projector",
                    "meeting_id": instance["id"],
                    "used_as_reference_projector_meeting_id": instance["id"],
                    "used_as_default_$_in_meeting_id": {
                        name: instance["id"]
                        for name in meeting_projector_default_replacements
                    },
                }
            ]
        return []

    def validate_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for guest_ids being in committee/member_ids or committee/manager_ids
        """
        instance = super().validate_fields(instance)
        if instance.get("guest_ids"):
            committee = self.datastore.get(
                FullQualifiedId(Collection("committee"), instance["committee_id"]),
                ["member_ids", "manager_ids"],
            )
            diff = (
                set(cast(Iterable[Any], instance.get("guest_ids")))
                - set(cast(Iterable[Any], committee.get("member_ids", ())))
                - set(cast(Iterable[Any], committee.get("manager_ids", ())))
            )
            if diff:
                raise ActionException(
                    f"Guest-ids {diff} are not part of committee-member or manager_ids."
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
