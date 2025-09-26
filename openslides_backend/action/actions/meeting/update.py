from datetime import datetime
from typing import Any, cast

from psycopg.types.json import Jsonb

from openslides_backend.action.mixins.check_unique_name_mixin import (
    CheckUniqueInContextMixin,
)

from ....i18n.translator import Translator
from ....i18n.translator import translate as _
from ....models.models import Meeting
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
    has_perm,
    is_admin,
)
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, MissingPermission, PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.util import ONE_ORGANIZATION_FQID
from ...generics.update import UpdateAction
from ...mixins.forbid_anonymous_group_mixin import ForbidAnonymousGroupMixin
from ...mixins.send_email_mixin import EmailCheckMixin, EmailSenderCheckMixin
from ...util.assert_belongs_to_meeting import assert_belongs_to_meeting
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..group.create import GroupCreate
from .mixins import GetMeetingIdFromIdMixin, MeetingCheckTimesMixin

meeting_settings_keys = [
    "welcome_title",
    "welcome_text",
    "name",
    "description",
    "location",
    "start_time",
    "end_time",
    "locked_from_inside",
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
    "export_pdf_line_height",
    "export_pdf_page_margin_left",
    "export_pdf_page_margin_top",
    "export_pdf_page_margin_right",
    "export_pdf_page_margin_bottom",
    "agenda_show_subtitles",
    "agenda_enable_numbering",
    "agenda_number_prefix",
    "agenda_numeral_system",
    "agenda_item_creation",
    "agenda_new_items_default_visibility",
    "agenda_show_internal_items_on_projector",
    "agenda_show_topic_navigation_on_detail_view",
    "list_of_speakers_amount_last_on_projector",
    "list_of_speakers_amount_next_on_projector",
    "list_of_speakers_couple_countdown",
    "list_of_speakers_show_amount_of_speakers_on_slide",
    "list_of_speakers_present_users_only",
    "list_of_speakers_show_first_contribution",
    "list_of_speakers_hide_contribution_count",
    "list_of_speakers_allow_multiple_speakers",
    "list_of_speakers_enable_point_of_order_speakers",
    "list_of_speakers_can_create_point_of_order_for_others",
    "list_of_speakers_enable_point_of_order_categories",
    "list_of_speakers_closing_disables_point_of_order",
    "list_of_speakers_enable_pro_contra_speech",
    "list_of_speakers_can_set_contribution_self",
    "list_of_speakers_speaker_note_for_everyone",
    "list_of_speakers_initially_closed",
    "list_of_speakers_default_structure_level_time",
    "list_of_speakers_enable_interposed_question",
    "list_of_speakers_intervention_time",
    "motions_default_workflow_id",
    "motions_default_amendment_workflow_id",
    "motions_preamble",
    "motions_default_line_numbering",
    "motions_line_length",
    "motions_reason_required",
    "motions_origin_motion_toggle_default",
    "motions_enable_origin_motion_display",
    "motions_enable_text_on_projector",
    "motions_enable_reason_on_projector",
    "motions_enable_sidebox_on_projector",
    "motions_create_enable_additional_submitter_text",
    "motions_hide_metadata_background",
    "motions_enable_recommendation_on_projector",
    "motions_show_referring_motions",
    "motions_show_sequential_number",
    "motions_recommendations_by",
    "motions_block_slide_columns",
    "motions_recommendation_text_mode",
    "motions_default_sorting",
    "motions_number_type",
    "motions_number_min_digits",
    "motions_number_with_blank",
    "motions_amendments_enabled",
    "motions_amendments_in_main_list",
    "motions_amendments_of_amendments",
    "motions_amendments_prefix",
    "motions_amendments_text_mode",
    "motions_amendments_multiple_paragraphs",
    "motions_supporters_min_amount",
    "motions_enable_editor",
    "motions_enable_working_group_speaker",
    "motions_export_title",
    "motions_export_preamble",
    "motions_export_submitter_recommendation",
    "motions_export_follow_recommendation",
    "motion_poll_ballot_paper_selection",
    "motion_poll_ballot_paper_number",
    "motion_poll_default_type",
    "motion_poll_default_method",
    "motion_poll_default_onehundred_percent_base",
    "motion_poll_default_group_ids",
    "motion_poll_default_backend",
    "motion_poll_projection_name_order_first",
    "motion_poll_projection_max_columns",
    "users_enable_presence_view",
    "users_enable_vote_weight",
    "users_enable_vote_delegations",
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
    "users_forbid_delegator_in_list_of_speakers",
    "users_forbid_delegator_as_submitter",
    "users_forbid_delegator_as_supporter",
    "users_forbid_delegator_to_vote",
    "assignments_export_title",
    "assignments_export_preamble",
    "assignment_poll_ballot_paper_selection",
    "assignment_poll_ballot_paper_number",
    "assignment_poll_add_candidates_to_list_of_speakers",
    "assignment_poll_enable_max_votes_per_option",
    "assignment_poll_sort_poll_result_by_votes",
    "assignment_poll_default_type",
    "assignment_poll_default_method",
    "assignment_poll_default_onehundred_percent_base",
    "assignment_poll_default_group_ids",
    "assignment_poll_default_backend",
    "topic_poll_default_group_ids",
    "poll_default_backend",
    "poll_default_live_voting_enabled",
]


@register_action("meeting.update")
class MeetingUpdate(
    CheckUniqueInContextMixin,
    EmailCheckMixin,
    EmailSenderCheckMixin,
    UpdateAction,
    GetMeetingIdFromIdMixin,
    MeetingCheckTimesMixin,
    ForbidAnonymousGroupMixin,
):
    model = Meeting()
    schema = DefaultSchema(Meeting()).get_update_schema(
        optional_properties=[
            *meeting_settings_keys,
            "external_id",
            "reference_projector_id",
            "organization_tag_ids",
            "jitsi_domain",
            "jitsi_room_name",
            "jitsi_room_password",
            "enable_anonymous",
            "custom_translations",
            "present_user_ids",
            *Meeting.all_default_projectors(),
        ],
        additional_optional_fields={
            "set_as_template": {"type": "boolean"},
        },
    )
    check_email_field = "users_email_replyto"

    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        if instance.get("external_id"):
            self.check_unique_in_context(
                "external_id",
                instance["external_id"],
                "The external id of the meeting is not unique in the organization scope. Send a differing external id with this request.",
                instance["id"],
            )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        # handle set_as_template
        set_as_template = instance.pop("set_as_template", None)
        db_meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["id"]),
            [
                "template_for_organization_id",
                "locked_from_inside",
                "admin_group_id",
                "language",
            ],
            lock_result=False,
        )
        Translator.set_translation_language(db_meeting["language"])
        lock_meeting = (
            instance.get("locked_from_inside")
            if instance.get("locked_from_inside") is not None
            else db_meeting.get("locked_from_inside")
        )
        if lock_meeting and (
            set_as_template
            if set_as_template is not None
            else db_meeting.get("template_for_organization_id")
        ):
            raise ActionException(
                "A meeting cannot be locked from the inside and a template at the same time."
            )
        self.check_locking(instance, set_as_template)
        organization = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["require_duplicate_from", "enable_anonymous"],
            lock_result=False,
        )
        if instance.get("enable_anonymous") and not organization.get(
            "enable_anonymous"
        ):
            raise ActionException(
                "Anonymous users can not be enabled in this organization."
            )
        if (
            organization.get("require_duplicate_from")
            and set_as_template is not None
            and not has_organization_management_level(
                self.datastore,
                self.user_id,
                OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            )
        ):
            raise ActionException(
                "A meeting cannot be set as a template by a committee manager if duplicate from is required."
            )

        if set_as_template is True:
            instance["template_for_organization_id"] = 1
        elif set_as_template is False:
            admin_group = self.datastore.get(
                fqid_from_collection_and_id("group", db_meeting["admin_group_id"]),
                ["meeting_user_ids"],
            )
            if not admin_group.get("meeting_user_ids"):
                raise ActionException(
                    "Can only remove meeting template status if it has at least one administrator."
                )
            instance["template_for_organization_id"] = None

        meeting_check = []
        if "reference_projector_id" in instance:
            if reference_projector_id := instance["reference_projector_id"]:
                reference_projector_fqid = fqid_from_collection_and_id(
                    "projector", reference_projector_id
                )
                projector = self.datastore.get(
                    reference_projector_fqid, ["is_internal"]
                )
                if projector.get("is_internal"):
                    raise ActionException(
                        "An internal projector cannot be set as reference projector."
                    )
                meeting_check.append(reference_projector_fqid)

        meeting_check.extend(
            [
                fqid_from_collection_and_id("projector", projector_id)
                for field in Meeting.all_default_projectors()
                for projector_id in instance.get(field, [])
            ]
        )

        if meeting_check:
            assert_belongs_to_meeting(self.datastore, meeting_check, instance["id"])
        if instance.get("jitsi_domain"):
            if instance["jitsi_domain"].strip().startswith("https://"):
                raise ActionException(
                    "It is not allowed to start jitsi_domain with 'https://'."
                )
            if instance["jitsi_domain"].strip().endswith("/"):
                raise ActionException("It is not allowed to end jitsi_domain with '/'.")

        self.check_start_and_end_time(instance)

        anonymous_group_id = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["id"]),
            ["anonymous_group_id"],
        ).get("anonymous_group_id")

        if instance.get("enable_anonymous") and not anonymous_group_id:
            group_result = self.execute_other_action(
                GroupCreate,
                [{"name": _("Public"), "weight": 0, "meeting_id": instance["id"]}],
            )
            instance["anonymous_group_id"] = anonymous_group_id = cast(
                list[dict[str, Any]], group_result
            )[0]["id"]
        self.check_anonymous_not_in_list_fields(
            instance,
            [
                "assignment_poll_default_group_ids",
                "topic_poll_default_group_ids",
                "motion_poll_default_group_ids",
            ],
            anonymous_group_id,
        )

        for field in ["start_time", "end_time"]:
            raw_value = instance.get(field)
            if isinstance(raw_value, int):
                instance[field] = datetime.fromtimestamp(raw_value)

        if (translations := instance.get("custom_translations")) is not None:
            instance["custom_translations"] = Jsonb(translations)

        instance = super().update_instance(instance)
        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
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
            self.datastore, self.user_id, Permissions.User.CAN_UPDATE, instance["id"]
        ):
            raise MissingPermission(Permissions.User.CAN_UPDATE)

        # group C check
        if (
            "reference_projector_id" in instance
            or any(field in instance for field in Meeting.all_default_projectors())
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
                    "external_id",
                    "enable_anonymous",
                    "custom_translations",
                ]
            ]
        ):
            if not is_admin(self.datastore, self.user_id, instance["id"]):
                raise PermissionDenied("Missing permission: Not admin of this meeting")

        # group E check
        if "organization_tag_ids" in instance:
            is_manager = has_committee_management_level(
                self.datastore,
                self.user_id,
                self.get_committee_id(instance["id"]),
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
                ]
            ]
        ):
            is_superadmin = has_organization_management_level(
                self.datastore, self.user_id, OrganizationManagementLevel.SUPERADMIN
            )
            if not is_superadmin:
                raise MissingPermission(OrganizationManagementLevel.SUPERADMIN)

    def get_committee_id(self, meeting_id: int) -> int:
        if not hasattr(self, "_committee_id"):
            self._committee_id = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, meeting_id),
                ["committee_id"],
                lock_result=False,
            )["committee_id"]
        return self._committee_id

    def check_locking(self, instance: dict[str, Any], set_as_template: bool) -> None:
        db_meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["id"]),
            ["template_for_organization_id", "locked_from_inside", "enable_anonymous"],
            lock_result=False,
        )
        lock_meeting = (
            instance.get("locked_from_inside")
            if instance.get("locked_from_inside") is not None
            else db_meeting.get("locked_from_inside")
        )
        if lock_meeting:
            if (
                set_as_template
                if set_as_template is not None
                else db_meeting.get("template_for_organization_id")
            ):
                raise ActionException(
                    "A meeting cannot be locked from the inside and a template at the same time."
                )
            if (
                instance.get("enable_anonymous")
                if instance.get("enable_anonymous") is not None
                else db_meeting.get("enable_anonymous")
            ):
                raise ActionException(
                    "A meeting cannot be locked from the inside and have anonymous enabled at the same time."
                )
