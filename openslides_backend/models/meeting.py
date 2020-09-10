from typing import Iterable

from ..shared.patterns import Collection
from . import fields
from .base import Model


class Meeting(Model):
    """
    Model for meetings.

    There are the following reverse relation fields:
        TODO
    """

    # TODO: Add reverse relation fields to docstring.

    collection = Collection("meeting")
    verbose_name = "meeting"

    def get_settings_keys(self) -> Iterable[str]:
        return [
            "name",
            "description",
            "date",
            "location",
            "start_time",
            "end_time",
            "custom_translations",  # TODO
            "url_name",
            "is_template",
            "enable_anonymous",
            "conference_show",
            "conference_auto_connect",
            "conference_los_restriction",
            "conference_stream_url",
            "projector_default_countdown_time",
            "projector_countdown_warning_time",
            "export_csv_separator",
            "export_csv_encoding",
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
            "motions_identifier_type",
            "motions_identifier_min_digits",
            "motions_identifier_with_blank",
            "motions_statutes_enabled",
            "motions_amendments_enabled",
            "motions_amendments_in_main_list",
            "motions_amendments_of_amendments",
            "motions_amendments_prefix",
            "motions_amendments_text_mode",
            "motions_amendments_multiple_paragraphs",
            "motions_supporters_min_amount",
            "motions_supporters_enable_autoremove",
            "motion_poll_default_type",
            "motion_poll_default_100_percent_base",
            "motion_poll_default_majority_method",
            "motion_poll_default_group_ids",
            "motion_poll_ballot_paper_selection",
            "motion_poll_ballot_paper_number",
            "motions_export_title",
            "motions_export_preamble",
            "motions_export_submitter_recommendation",
            "motions_export_follow_recommendation",
            "assignment_poll_default_type",
            "assignment_poll_default_method",
            "assignment_poll_default_100_percent_base",
            "assignment_poll_default_majority_method",
            "assignment_poll_default_group_ids",
            "assignment_poll_add_candidates_to_list_of_speakers",
            "assignment_poll_sort_poll_result_by_votes",
            "assignment_poll_ballot_paper_selection",
            "assignment_poll_ballot_paper_number",
            "assignments_export_title",
            "assignments_export_preamble",
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
        ]

    id = fields.IdField(description="The id of this meeting.")
    committee_id = fields.RequiredForeignKeyField(
        description="The id of the committee of this meeting.",
        to=Collection("committee"),
        related_name="meeting_ids",
    )

    welcome_title = fields.CharField()
    welcome_text = fields.TextField()

    name = fields.CharField(maxLength=100)
    description = fields.CharField(maxLength=100)

    date = fields.TextField()
    location = fields.TextField()
    start_time = fields.TimestampField()
    end_time = fields.TimestampField()
    custom_translations = fields.ArrayField()

    url_name = fields.TextField()
    is_template = fields.BooleanField()
    enable_anonymous = fields.BooleanField()

    conference_show = fields.BooleanField()
    conference_auto_connect = fields.BooleanField()
    conference_los_restriction = fields.BooleanField()
    conference_stream_url = fields.TextField()

    projector_default_countdown_time = fields.IntegerField()
    projector_countdown_warning_time = fields.IntegerField(minimum=0)

    export_csv_separator = fields.TextField()
    export_csv_encoding = fields.TextField(enum=["utf-8", "iso-8859-15"])
    export_pdf_pagenumber_alignment = fields.TextField(enum=["left", "right", "center"])
    export_pdf_fontsize = fields.IntegerField(enum=[10, 11, 12])
    export_pdf_pagesize = fields.TextField(enum=["A4", "A5"])

    agenda_show_subtitles = fields.BooleanField()
    agenda_enable_numbering = fields.BooleanField()
    agenda_number_prefix = fields.TextField(maxLength=20)
    agenda_numeral_system = fields.TextField(enum=["arabic", "roman"])
    agenda_item_creation = fields.TextField(
        enum=["always", "never", "default_yes", "default_no"]
    )
    agenda_new_items_default_visibility = fields.IntegerField(enum=[1, 2, 3])
    agenda_show_internal_items_on_projector = fields.BooleanField()

    list_of_speakers_amount_last_on_projector = fields.IntegerField(minimum=0)
    list_of_speakers_amount_next_on_projector = fields.IntegerField(minimum=-1)
    list_of_speakers_couple_countdown = fields.BooleanField()
    list_of_speakers_show_amount_of_speakers_on_slide = fields.BooleanField()
    list_of_speakers_present_users_only = fields.BooleanField()
    list_of_speakers_show_first_contribution = fields.BooleanField()

    motions_default_workflow_id = fields.RequiredOneToOneField(
        to=Collection("motion_workflow"), related_name="default_workflow_meeting_id",
    )
    motions_default_amendment_workflow_id = fields.RequiredOneToOneField(
        to=Collection("motion_workflow"),
        related_name="default_amendment_workflow_meeting_id",
    )
    motions_default_statute_amendment_workflow_id = fields.RequiredOneToOneField(
        to=Collection("motion_workflow"),
        related_name="default_statute_amendment_workflow_meeting_id",
    )
    motions_preamble = fields.TextField()
    motions_default_line_numbering = fields.TextField(
        enum=["outside", "inline", "none"]
    )
    motions_line_length = fields.IntegerField(minimum=40)
    motions_reason_required = fields.BooleanField()
    motions_enable_text_on_projector = fields.BooleanField()
    motions_enable_reason_on_projector = fields.BooleanField()
    motions_enable_sidebox_on_projector = fields.BooleanField()
    motions_enable_recommendation_on_projector = fields.BooleanField()
    motions_show_referring_motions = fields.BooleanField()
    motions_show_sequential_number = fields.BooleanField()
    motions_recommendations_by = fields.TextField()
    motions_statute_recommendations_by = fields.TextField()
    motions_recommendation_text_mode = fields.TextField(
        enum=["original", "changed", "diff", "agreed"]
    )
    motions_default_sorting = fields.TextField(enum=["weight", "identifier"])
    motions_identifier_type = fields.TextField(
        enum=["per_category", "serially_numbered", "manually"]
    )
    motions_identifier_min_digits = fields.PositiveIntegerField()
    motions_identifier_with_blank = fields.BooleanField()
    motions_statutes_enabled = fields.BooleanField()
    motions_amendments_enabled = fields.BooleanField()
    motions_amendments_in_main_list = fields.BooleanField()
    motions_amendments_of_amendments = fields.BooleanField()
    motions_amendments_prefix = fields.TextField()
    motions_amendments_text_mode = fields.TextField(
        enum=["freestyle", "fulltext", "paragraph"]
    )
    motions_amendments_multiple_paragraphs = fields.BooleanField()
    motions_supporters_min_amount = fields.IntegerField(minimum=0)
    motions_supporters_enable_autoremove = fields.BooleanField()

    motion_poll_default_type = fields.TextField()  # TODO: PollType enum
    motion_poll_default_100_percent_base = fields.TextField()  # TODO: PercentBase enum
    motion_poll_default_majority_method = (
        fields.TextField()
    )  # TODO: MajorityMethod enum
    # motion_poll_default_group_ids = fields.ManyToOneArrayField(
    #     to=Collection("group"), related_name="used_as_motion_poll_default_id"
    # )
    motion_poll_ballot_paper_selection = fields.TextField(
        enum=["NUMBER_OF_DELEGATES", "NUMBER_OF_ALL_PARTICIPANTS", "CUSTOM_NUMBER"]
    )
    motion_poll_ballot_paper_number = fields.PositiveIntegerField()

    motions_export_title = fields.TextField()
    motions_export_preamble = fields.TextField()
    motions_export_submitter_recommendation = fields.BooleanField()
    motions_export_follow_recommendation = fields.BooleanField()

    assignment_poll_default_type = fields.TextField()  # TODO: PollType enum
    assignment_poll_default_method = fields.TextField()  # TODO: PollMethod enum
    assignment_poll_default_100_percent_base = (
        fields.TextField()
    )  # TODO: PercentBase enum
    assignment_poll_default_majority_method = (
        fields.TextField()
    )  # TODO: MajorityMethod enum
    # assignment_poll_default_group_ids = fields.ManyToOneArrayField(
    #     to=Collection("group"), related_name="used_as_assignment_poll_default_id"
    # )
    assignment_poll_add_candidates_to_list_of_speakers = fields.BooleanField()
    assignment_poll_sort_poll_result_by_votes = fields.BooleanField()

    assignment_poll_ballot_paper_selection = fields.TextField(
        enum=["NUMBER_OF_DELEGATES", "NUMBER_OF_ALL_PARTICIPANTS", "CUSTOM_NUMBER"]
    )
    assignment_poll_ballot_paper_number = fields.PositiveIntegerField()

    assignments_export_title = fields.TextField()
    assignments_export_preamble = fields.TextField()

    users_sort_by = fields.TextField(enum=["first_name", "last_name", "number"])
    users_enable_presence_view = fields.BooleanField()
    users_enable_vote_weight = fields.BooleanField()
    users_allow_self_set_present = fields.BooleanField()
    users_pdf_welcometitle = fields.TextField()
    users_pdf_welcometext = fields.TextField()
    users_pdf_url = fields.TextField()
    users_pdf_wlan_ssid = fields.TextField()
    users_pdf_wlan_password = fields.TextField()
    users_pdf_wlan_encryption = fields.TextField(enum=["", "WEP", "WPA", "nopass"])

    users_email_sender = fields.TextField()
    users_email_replyto = fields.TextField()
    users_email_subject = fields.TextField()
    users_email_body = fields.TextField()
