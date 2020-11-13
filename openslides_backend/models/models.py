# Code generated. DO NOT EDIT.

from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.patterns import Collection

MODELS_YML_CHECKSUM = "d5b4408aadf18c025ff717b615fd600d"


class Organisation(Model):
    collection = Collection("organisation")
    verbose_name = "organisation"

    id = fields.IntegerField()
    name = fields.CharField()
    description = fields.HTMLStrictField()
    legal_notice = fields.CharField()
    privacy_policy = fields.CharField()
    login_text = fields.CharField()
    theme = fields.CharField()
    custom_translations = fields.JSONField()
    reset_password_verbose_errors = fields.BooleanField()
    enable_electronic_voting = fields.BooleanField(read_only=True)
    committee_ids = fields.RelationListField(
        to=Collection("committee"), related_name="organisation_id"
    )
    role_ids = fields.RelationListField(
        to=Collection("role"), related_name="organisation_id"
    )
    superadmin_role_id = fields.RelationField(
        to=Collection("role"), related_name="superadmin_role_for_organisation_id"
    )
    resource_ids = fields.RelationListField(
        to=Collection("resource"), related_name="organisation_id"
    )


class User(Model):
    collection = Collection("user")
    verbose_name = "user"

    id = fields.IntegerField()
    username = fields.CharField()
    title = fields.CharField()
    first_name = fields.CharField()
    last_name = fields.CharField()
    is_active = fields.BooleanField()
    is_physical_person = fields.BooleanField(default=True)
    password = fields.CharField()
    default_password = fields.CharField()
    about_me = fields.HTMLStrictField()
    gender = fields.CharField()
    comment = fields.HTMLStrictField()
    number = fields.CharField()
    structure_level = fields.CharField()
    email = fields.CharField()
    last_email_send = fields.CharField()
    vote_weight = fields.DecimalField()
    is_demo_user = fields.BooleanField(read_only=True)
    role_id = fields.RelationField(to=Collection("role"), related_name="user_ids")
    is_present_in_meeting_ids = fields.RelationListField(
        to=Collection("meeting"), related_name="present_user_ids"
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="temporary_user_ids"
    )
    guest_meeting_ids = fields.RelationListField(
        to=Collection("meeting"), related_name="guest_ids"
    )
    committee_as_member_ids = fields.RelationListField(
        to=Collection("committee"), related_name="member_ids"
    )
    committee_as_manager_ids = fields.RelationListField(
        to=Collection("committee"), related_name="manager_ids"
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"), related_name="element_id", generic_relation=True
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
    )
    group__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=6,
        to=Collection("group"),
        related_name="user_ids",
    )
    speaker__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=8,
        to=Collection("speaker"),
        related_name="user_id",
    )
    personal_note__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=14,
        to=Collection("personal_note"),
        related_name="user_id",
    )
    supported_motion__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=17,
        to=Collection("motion"),
        related_name="supporter_ids",
    )
    submitted_motion__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=17,
        to=Collection("motion_submitter"),
        related_name="user_id",
    )
    motion_poll_voted__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=18,
        to=Collection("motion_poll"),
        related_name="voted_ids",
    )
    motion_vote__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=12,
        to=Collection("motion_vote"),
        related_name="user_id",
    )
    motion_delegated_vote__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=22,
        to=Collection("motion_vote"),
        related_name="delegated_user_id",
    )
    assignment_candidate__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=21,
        to=Collection("assignment_candidate"),
        related_name="user_id",
    )
    assignment_poll_voted__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=22,
        to=Collection("assignment_poll"),
        related_name="voted_ids",
    )
    assignment_option__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=18,
        to=Collection("assignment_option"),
        related_name="user_id",
    )
    assignment_vote__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=16,
        to=Collection("assignment_vote"),
        related_name="user_id",
    )
    assignment_delegated_vote__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=26,
        to=Collection("assignment_vote"),
        related_name="delegated_user_id",
    )
    vote_delegated__to_id = fields.TemplateRelationField(
        replacement="meeting_id",
        index=15,
        to=Collection("user"),
        related_name="vote_delegations_$_from_ids",
        structured_relation=["meeting_id"],
    )
    vote_delegations__from_ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=17,
        to=Collection("user"),
        related_name="vote_delegated_$_to_id",
        structured_relation=["meeting_id"],
    )


class Role(Model):
    collection = Collection("role")
    verbose_name = "role"

    id = fields.IntegerField()
    name = fields.CharField()
    permissions = fields.CharArrayField()
    organisation_id = fields.OrganisationField(
        to=Collection("organisation"), related_name="role_ids"
    )
    superadmin_role_for_organisation_id = fields.RelationField(
        to=Collection("organisation"), related_name="superadmin_role_id"
    )
    user_ids = fields.RelationListField(to=Collection("user"), related_name="role_id")


class Resource(Model):
    collection = Collection("resource")
    verbose_name = "resource"

    id = fields.IntegerField()
    token = fields.CharField()
    filesize = fields.IntegerField()
    mimetype = fields.CharField()
    organisation_id = fields.OrganisationField(
        to=Collection("organisation"), related_name="resource_ids"
    )


class Committee(Model):
    collection = Collection("committee")
    verbose_name = "committee"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    description = fields.HTMLStrictField()
    meeting_ids = fields.RelationListField(
        to=Collection("meeting"),
        related_name="committee_id",
        on_delete=fields.OnDelete.PROTECT,
    )
    template_meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="template_for_committee_id"
    )
    default_meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="default_meeting_for_committee_id"
    )
    member_ids = fields.RelationListField(
        to=Collection("user"), related_name="committee_as_member_ids"
    )
    manager_ids = fields.RelationListField(
        to=Collection("user"), related_name="committee_as_manager_ids"
    )
    forward_to_committee_ids = fields.RelationListField(
        to=Collection("committee"),
        related_name="receive_forwardings_from_committee_ids",
    )
    receive_forwardings_from_committee_ids = fields.RelationListField(
        to=Collection("committee"), related_name="forward_to_committee_ids"
    )
    organisation_id = fields.OrganisationField(
        to=Collection("organisation"), related_name="committee_ids", required=True
    )


class Meeting(Model):
    collection = Collection("meeting")
    verbose_name = "meeting"

    id = fields.IntegerField()
    welcome_title = fields.CharField()
    welcome_text = fields.HTMLPermissiveField()
    name = fields.CharField(constraints={"maxLength": 100})
    description = fields.CharField(constraints={"maxLength": 100})
    location = fields.CharField()
    start_time = fields.TimestampField()
    end_time = fields.TimestampField()
    jitsi_domain = fields.CharField(read_only=True)
    jitsi_room_name = fields.CharField(read_only=True)
    jitsi_room_password = fields.CharField(read_only=True)
    url_name = fields.CharField(constraints={"description": "For unique urls."})
    template_for_committee_id = fields.RelationField(
        to=Collection("committee"), related_name="template_meeting_id"
    )
    enable_anonymous = fields.BooleanField()
    conference_show = fields.BooleanField()
    conference_auto_connect = fields.BooleanField()
    conference_los_restriction = fields.BooleanField()
    conference_stream_url = fields.CharField()
    conference_stream_poster_url = fields.CharField()
    projector_default_countdown_time = fields.IntegerField()
    projector_countdown_warning_time = fields.IntegerField(constraints={"minimum": 0})
    export_csv_encoding = fields.CharField(
        constraints={"enum": ["utf-8", "iso-8859-15"]}
    )
    export_csv_separator = fields.CharField()
    export_pdf_pagenumber_alignment = fields.CharField(
        constraints={"enum": ["left", "right", "center"]}
    )
    export_pdf_fontsize = fields.IntegerField(constraints={"enum": [10, 11, 12]})
    export_pdf_pagesize = fields.CharField(constraints={"enum": ["A4", "A5"]})
    agenda_show_subtitles = fields.BooleanField()
    agenda_enable_numbering = fields.BooleanField()
    agenda_number_prefix = fields.CharField(constraints={"maxLength": 20})
    agenda_numeral_system = fields.CharField(constraints={"enum": ["arabic", "roman"]})
    agenda_item_creation = fields.CharField(
        constraints={"enum": ["always", "never", "default_yes", "default_no"]}
    )
    agenda_new_items_default_visibility = fields.IntegerField(
        constraints={"enum": [1, 2, 3]}
    )
    agenda_show_internal_items_on_projector = fields.BooleanField()
    list_of_speakers_amount_last_on_projector = fields.IntegerField(
        constraints={"minimum": 0}
    )
    list_of_speakers_amount_next_on_projector = fields.BooleanField()
    list_of_speakers_couple_countdown = fields.BooleanField()
    list_of_speakers_show_amount_of_speakers_on_slide = fields.BooleanField()
    list_of_speakers_present_users_only = fields.BooleanField()
    list_of_speakers_show_first_contribution = fields.BooleanField()
    motions_default_workflow_id = fields.RelationField(
        to=Collection("motion_workflow"),
        related_name="default_workflow_meeting_id",
        required=True,
    )
    motions_default_amendment_workflow_id = fields.RelationField(
        to=Collection("motion_workflow"),
        related_name="default_amendment_workflow_meeting_id",
        required=True,
    )
    motions_default_statute_amendment_workflow_id = fields.RelationField(
        to=Collection("motion_workflow"),
        related_name="default_statute_amendment_workflow_meeting_id",
        required=True,
    )
    motions_preamble = fields.CharField()
    motions_default_line_numbering = fields.CharField(
        constraints={"enum": ["outside", "inline", "none"]}
    )
    motions_line_length = fields.IntegerField(constraints={"minimium": 40})
    motions_reason_required = fields.BooleanField()
    motions_enable_text_on_projector = fields.BooleanField()
    motions_enable_reason_on_projector = fields.BooleanField()
    motions_enable_sidebox_on_projector = fields.BooleanField()
    motions_enable_recommendation_on_projector = fields.BooleanField()
    motions_show_referring_motions = fields.BooleanField()
    motions_show_sequential_number = fields.BooleanField()
    motions_recommendations_by = fields.CharField()
    motions_statute_recommendations_by = fields.CharField()
    motions_recommendation_text_mode = fields.CharField(
        constraints={"enum": ["original", "changed", "diff", "agreed"]}
    )
    motions_default_sorting = fields.CharField()
    motions_number_type = fields.CharField(
        constraints={"enum": ["per_category", "serially_numbered", "manually"]}
    )
    motions_number_min_digits = fields.IntegerField()
    motions_number_with_blank = fields.BooleanField()
    motions_statutes_enabled = fields.BooleanField()
    motions_amendments_enabled = fields.BooleanField()
    motions_amendments_in_main_list = fields.BooleanField()
    motions_amendments_of_amendments = fields.BooleanField()
    motions_amendments_prefix = fields.CharField()
    motions_amendments_text_mode = fields.CharField(
        constraints={"enum": ["freestyle", "fulltext", "paragraph"]}
    )
    motions_amendments_multiple_paragraphs = fields.BooleanField()
    motions_supporters_min_amount = fields.IntegerField(constraints={"minimum": 0})
    motions_supporters_enable_autoremove = fields.BooleanField()
    motions_export_title = fields.CharField()
    motions_export_preamble = fields.CharField()
    motions_export_submitter_recommendation = fields.BooleanField()
    motions_export_follow_recommendation = fields.BooleanField()
    motion_poll_ballot_paper_selection = fields.CharField(
        constraints={
            "enum": [
                "NUMBER_OF_DELEGATES",
                "NUMBER_OF_ALL_PARTICIPANTS",
                "CUSTOM_NUMBER",
            ]
        }
    )
    motion_poll_ballot_paper_number = fields.IntegerField()
    motion_poll_default_type = fields.CharField()
    motion_poll_default_100_percent_base = fields.CharField()
    motion_poll_default_majority_method = fields.CharField()
    motion_poll_default_group_ids = fields.RelationListField(
        to=Collection("group"), related_name="used_as_motion_poll_default_id"
    )
    users_sort_by = fields.CharField(
        constraints={"enum": ["first_name", "last_name", "number"]}
    )
    users_enable_presence_view = fields.BooleanField()
    users_enable_vote_weight = fields.BooleanField()
    users_allow_self_set_present = fields.BooleanField()
    users_pdf_welcometitle = fields.CharField()
    users_pdf_welcometext = fields.CharField()
    users_pdf_url = fields.CharField()
    users_pdf_wlan_ssid = fields.CharField()
    users_pdf_wlan_password = fields.CharField()
    users_pdf_wlan_encryption = fields.CharField(
        constraints={"enum": ["", "WEP", "WPA", "nopass"]}
    )
    users_email_sender = fields.CharField()
    users_email_replyto = fields.CharField()
    users_email_subject = fields.CharField()
    users_email_body = fields.CharField()
    assignemnts_export_title = fields.CharField()
    assignments_export_preamble = fields.CharField()
    assignment_poll_ballot_paper_selection = fields.CharField(
        constraints={
            "enum": [
                "NUMBER_OF_DELEGATES",
                "NUMBER_OF_ALL_PARTICIPANTS",
                "CUSTOM_NUMBER",
            ]
        }
    )
    assignment_poll_ballot_paper_number = fields.IntegerField()
    assignment_poll_add_candidates_to_list_of_speakers = fields.BooleanField()
    assignment_poll_sort_poll_result_by_votes = fields.BooleanField()
    assignment_poll_default_type = fields.CharField()
    assignment_poll_default_method = fields.CharField()
    assignment_poll_default_100_percent_base = fields.CharField()
    assignment_poll_default_majority_method = fields.CharField()
    assignment_poll_default_group_ids = fields.RelationListField(
        to=Collection("group"), related_name="used_as_assignment_poll_default_id"
    )
    projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    projectiondefault_ids = fields.RelationListField(
        to=Collection("projectiondefault"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    projector_message_ids = fields.RelationListField(
        to=Collection("projector_message"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    projector_countdown_ids = fields.RelationListField(
        to=Collection("projector_countdown"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    tag_ids = fields.RelationListField(
        to=Collection("tag"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    agenda_item_ids = fields.RelationListField(
        to=Collection("agenda_item"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    list_of_speakers_ids = fields.RelationListField(
        to=Collection("list_of_speakers"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    topic_ids = fields.RelationListField(
        to=Collection("topic"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    group_ids = fields.RelationListField(
        to=Collection("group"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    mediafile_ids = fields.RelationListField(
        to=Collection("mediafile"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_ids = fields.RelationListField(
        to=Collection("motion"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_comment_section_ids = fields.RelationListField(
        to=Collection("motion_comment_section"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_category_ids = fields.RelationListField(
        to=Collection("motion_category"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_block_ids = fields.RelationListField(
        to=Collection("motion_block"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_workflow_ids = fields.RelationListField(
        to=Collection("motion_workflow"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_statute_paragraph_ids = fields.RelationListField(
        to=Collection("motion_statute_paragraph"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_poll_ids = fields.RelationListField(
        to=Collection("motion_poll"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    assignment_ids = fields.RelationListField(
        to=Collection("assignment"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    assignment_poll_ids = fields.RelationListField(
        to=Collection("assignment_poll"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    personal_note_ids = fields.RelationListField(
        to=Collection("personal_note"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    speaker_ids = fields.RelationListField(
        to=Collection("speaker"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_option_ids = fields.RelationListField(
        to=Collection("motion_option"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_vote_ids = fields.RelationListField(
        to=Collection("motion_vote"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_comment_ids = fields.RelationListField(
        to=Collection("motion_comment"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_submitter_ids = fields.RelationListField(
        to=Collection("motion_submitter"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_change_recommendation_ids = fields.RelationListField(
        to=Collection("motion_change_recommendation"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_state_ids = fields.RelationListField(
        to=Collection("motion_state"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    assignment_candidate_ids = fields.RelationListField(
        to=Collection("assignment_candidate"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    assignment_option_ids = fields.RelationListField(
        to=Collection("assignment_option"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    assignment_vote_ids = fields.RelationListField(
        to=Collection("assignment_vote"),
        related_name="meeting_id",
        on_delete=fields.OnDelete.CASCADE,
    )
    logo__id = fields.TemplateRelationField(
        replacement="place",
        index=5,
        to=Collection("mediafile"),
        related_name="used_as_logo_$_in_meeting_id",
        structured_tag="place",
    )
    font__id = fields.TemplateRelationField(
        replacement="place",
        index=5,
        to=Collection("mediafile"),
        related_name="used_as_font_$_in_meeting_id",
        structured_tag="place",
    )
    committee_id = fields.RelationField(
        to=Collection("committee"), related_name="meeting_ids", required=True
    )
    default_meeting_for_committee_id = fields.RelationField(
        to=Collection("committee"), related_name="default_meeting_id"
    )
    present_user_ids = fields.RelationListField(
        to=Collection("user"), related_name="is_present_in_meeting_ids"
    )
    temporary_user_ids = fields.RelationListField(
        to=Collection("user"), related_name="meeting_id"
    )
    guest_ids = fields.RelationListField(
        to=Collection("user"), related_name="guest_meeting_ids"
    )
    user_ids = fields.NumberArrayField(
        read_only=True,
        constraints={
            "decription": "Calculated. All ids from temporary_user_ids, guest_ids and all users assigned to groups."
        },
    )
    reference_projector_id = fields.RelationField(
        to=Collection("projector"),
        related_name="used_as_reference_projector_meeting_id",
    )
    default_group_id = fields.RelationField(
        to=Collection("group"),
        related_name="default_group_for_meeting_id",
        required=True,
    )
    superadmin_group_id = fields.RelationField(
        to=Collection("group"), related_name="superadmin_group_for_meeting_id"
    )


class Group(Model):
    collection = Collection("group")
    verbose_name = "group"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    permissions = fields.CharArrayField()
    user_ids = fields.RelationListField(
        to=Collection("user"),
        related_name="group_$_ids",
        structured_relation=["meeting_id"],
    )
    default_group_for_meeting_id = fields.RelationField(
        to=Collection("meeting"),
        related_name="default_group_id",
        on_delete=fields.OnDelete.PROTECT,
    )
    superadmin_group_for_meeting_id = fields.RelationField(
        to=Collection("meeting"),
        related_name="superadmin_group_id",
        on_delete=fields.OnDelete.PROTECT,
    )
    mediafile_access_group_ids = fields.RelationListField(
        to=Collection("mediafile"),
        related_name="access_group_ids",
        equal_fields="meeting_id",
    )
    mediafile_inherited_access_group_ids = fields.RelationListField(
        to=Collection("mediafile"),
        related_name="inherited_access_group_ids",
        read_only=True,
        constraints={"description": "Calculated field."},
    )
    read_comment_section_ids = fields.RelationListField(
        to=Collection("motion_comment_section"),
        related_name="read_group_ids",
        equal_fields="meeting_id",
    )
    write_comment_section_ids = fields.RelationListField(
        to=Collection("motion_comment_section"),
        related_name="write_group_ids",
        equal_fields="meeting_id",
    )
    motion_poll_ids = fields.RelationListField(
        to=Collection("motion_poll"),
        related_name="entitled_group_ids",
        equal_fields="meeting_id",
    )
    assignment_poll_ids = fields.RelationListField(
        to=Collection("assignment_poll"),
        related_name="entitled_group_ids",
        equal_fields="meeting_id",
    )
    used_as_motion_poll_default_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_poll_default_group_ids"
    )
    used_as_assignment_poll_default_id = fields.RelationField(
        to=Collection("meeting"), related_name="assignment_poll_default_group_ids"
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="group_ids", required=True
    )


class PersonalNote(Model):
    collection = Collection("personal_note")
    verbose_name = "personal note"

    id = fields.IntegerField()
    note = fields.HTMLStrictField()
    star = fields.BooleanField()
    user_id = fields.RelationField(
        to=Collection("user"),
        related_name="personal_note_$_ids",
        structured_relation=["meeting_id"],
    )
    content_object_id = fields.GenericRelationField(
        to=[Collection("motion")],
        related_name="personal_note_ids",
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="personal_note_ids", required=True
    )


class Tag(Model):
    collection = Collection("tag")
    verbose_name = "tag"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    tagged_ids = fields.GenericRelationListField(
        to=[
            Collection("agenda_item"),
            Collection("assignment"),
            Collection("motion"),
            Collection("topic"),
        ],
        related_name="tag_ids",
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="tag_ids", required=True
    )


class AgendaItem(Model):
    collection = Collection("agenda_item")
    verbose_name = "agenda item"

    id = fields.IntegerField()
    item_number = fields.CharField()
    comment = fields.CharField()
    closed = fields.BooleanField()
    type = fields.IntegerField(default=1, constraints={"enum": [1, 2, 3]})
    duration = fields.IntegerField(
        constraints={"description": "Given in seconds", "minimum": 0}
    )
    is_internal = fields.BooleanField(
        read_only=True, constraints={"description": "Calculated by the server"}
    )
    is_hidden = fields.BooleanField(
        read_only=True, constraints={"description": "Calculated by the server"}
    )
    level = fields.IntegerField(
        read_only=True, constraints={"description": "Calculated by the server"}
    )
    weight = fields.IntegerField(default=10000)
    content_object_id = fields.GenericRelationField(
        to=[
            Collection("motion"),
            Collection("motion_block"),
            Collection("assignment"),
            Collection("topic"),
        ],
        related_name="agenda_item_id",
        required=True,
        equal_fields="meeting_id",
    )
    parent_id = fields.RelationField(
        to=Collection("agenda_item"),
        related_name="child_ids",
        equal_fields="meeting_id",
    )
    child_ids = fields.RelationListField(
        to=Collection("agenda_item"),
        related_name="parent_id",
        equal_fields="meeting_id",
    )
    tag_ids = fields.RelationListField(
        to=Collection("tag"),
        related_name="tagged_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="agenda_item_ids", required=True
    )

    AGENDA_ITEM = 1
    INTERNAL_ITEM = 2
    HIDDEN_ITEM = 3


class ListOfSpeakers(Model):
    collection = Collection("list_of_speakers")
    verbose_name = "list of speakers"

    id = fields.IntegerField()
    closed = fields.BooleanField()
    content_object_id = fields.GenericRelationField(
        to=[
            Collection("motion"),
            Collection("motion_block"),
            Collection("assignment"),
            Collection("topic"),
            Collection("mediafile"),
        ],
        related_name="list_of_speakers_id",
        required=True,
        equal_fields="meeting_id",
    )
    speaker_ids = fields.RelationListField(
        to=Collection("speaker"),
        related_name="list_of_speakers_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="list_of_speakers_ids", required=True
    )


class Speaker(Model):
    collection = Collection("speaker")
    verbose_name = "speaker"

    id = fields.IntegerField()
    begin_time = fields.TimestampField(read_only=True)
    end_time = fields.TimestampField(read_only=True)
    weight = fields.IntegerField(default=10000)
    marked = fields.BooleanField()
    list_of_speakers_id = fields.RelationField(
        to=Collection("list_of_speakers"),
        related_name="speaker_ids",
        required=True,
        equal_fields="meeting_id",
    )
    user_id = fields.RelationField(
        to=Collection("user"),
        related_name="speaker_$_ids",
        structured_relation=["meeting_id"],
        required=True,
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="speaker_ids", required=True
    )


class Topic(Model):
    collection = Collection("topic")
    verbose_name = "topic"

    id = fields.IntegerField()
    title = fields.CharField(required=True)
    text = fields.HTMLPermissiveField()
    attachment_ids = fields.RelationListField(
        to=Collection("mediafile"),
        related_name="attachment_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    agenda_item_id = fields.RelationField(
        to=Collection("agenda_item"),
        related_name="content_object_id",
        generic_relation=True,
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to=Collection("list_of_speakers"),
        related_name="content_object_id",
        generic_relation=True,
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    tag_ids = fields.RelationListField(
        to=Collection("tag"),
        related_name="tagged_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="topic_ids", required=True
    )


class Motion(Model):
    collection = Collection("motion")
    verbose_name = "motion"

    id = fields.IntegerField()
    number = fields.CharField()
    sequential_number = fields.IntegerField(
        read_only=True,
        constraints={
            "description": "The (positive) serial number of this motion. This number is auto-generated and read-only."
        },
    )
    title = fields.CharField(required=True)
    text = fields.HTMLStrictField()
    amendment_paragraph_ = fields.TemplateHTMLStrictField(
        replacement="paragraph_number",
        index=20,
    )
    modified_final_version = fields.HTMLStrictField()
    reason = fields.HTMLStrictField()
    category_weight = fields.IntegerField(default=10000)
    state_extension = fields.CharField()
    recommendation_extension = fields.CharField()
    sort_weight = fields.IntegerField(default=10000)
    created = fields.TimestampField(read_only=True)
    last_modified = fields.TimestampField(read_only=True)
    lead_motion_id = fields.RelationField(
        to=Collection("motion"), related_name="amendment_ids", equal_fields="meeting_id"
    )
    amendment_ids = fields.RelationListField(
        to=Collection("motion"),
        related_name="lead_motion_id",
        equal_fields="meeting_id",
    )
    sort_parent_id = fields.RelationField(
        to=Collection("motion"),
        related_name="sort_child_ids",
        equal_fields="meeting_id",
    )
    sort_child_ids = fields.RelationListField(
        to=Collection("motion"),
        related_name="sort_parent_id",
        equal_fields="meeting_id",
    )
    origin_id = fields.RelationField(
        to=Collection("motion"), related_name="derived_motion_ids"
    )
    derived_motion_ids = fields.RelationListField(
        to=Collection("motion"), related_name="origin_id"
    )
    forwarding_tree_motion_ids = fields.NumberArrayField()
    state_id = fields.RelationField(
        to=Collection("motion_state"),
        related_name="motion_ids",
        required=True,
        equal_fields="meeting_id",
    )
    recommendation_id = fields.RelationField(
        to=Collection("motion_state"),
        related_name="motion_recommendation_ids",
        equal_fields="meeting_id",
    )
    recommendation_extension_reference_ids = fields.GenericRelationListField(
        to=[Collection("motion")],
        related_name="referenced_in_motion_recommendation_extension_ids",
        equal_fields="meeting_id",
    )
    referenced_in_motion_recommendation_extension_ids = fields.RelationListField(
        to=Collection("motion"),
        related_name="recommendation_extension_reference_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    category_id = fields.RelationField(
        to=Collection("motion_category"),
        related_name="motion_ids",
        equal_fields="meeting_id",
    )
    block_id = fields.RelationField(
        to=Collection("motion_block"),
        related_name="motion_ids",
        equal_fields="meeting_id",
    )
    submitter_ids = fields.RelationListField(
        to=Collection("motion_submitter"),
        related_name="motion_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    supporter_ids = fields.RelationListField(
        to=Collection("user"),
        related_name="supported_motion_$_ids",
        structured_relation=["meeting_id"],
        equal_fields="meeting_id",
    )
    poll_ids = fields.RelationListField(
        to=Collection("motion_poll"),
        related_name="motion_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    change_recommendation_ids = fields.RelationListField(
        to=Collection("motion_change_recommendation"),
        related_name="motion_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    statute_paragraph_id = fields.RelationField(
        to=Collection("motion_statute_paragraph"),
        related_name="motion_ids",
        equal_fields="meeting_id",
    )
    comment_ids = fields.RelationListField(
        to=Collection("motion_comment"),
        related_name="motion_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    agenda_item_id = fields.RelationField(
        to=Collection("agenda_item"),
        related_name="content_object_id",
        generic_relation=True,
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to=Collection("list_of_speakers"),
        related_name="content_object_id",
        generic_relation=True,
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    tag_ids = fields.RelationListField(
        to=Collection("tag"),
        related_name="tagged_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    attachment_ids = fields.RelationListField(
        to=Collection("mediafile"),
        related_name="attachment_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    personal_note_ids = fields.RelationListField(
        to=Collection("personal_note"),
        related_name="content_object_id",
        generic_relation=True,
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_ids", required=True
    )


class MotionSubmitter(Model):
    collection = Collection("motion_submitter")
    verbose_name = "motion submitter"

    id = fields.IntegerField()
    weight = fields.IntegerField(default=10000)
    user_id = fields.RelationField(
        to=Collection("user"),
        related_name="submitted_motion_$_ids",
        structured_relation=["meeting_id"],
    )
    motion_id = fields.RelationField(
        to=Collection("motion"), related_name="submitter_ids", equal_fields="meeting_id"
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_submitter_ids", required=True
    )


class MotionComment(Model):
    collection = Collection("motion_comment")
    verbose_name = "motion comment"

    id = fields.IntegerField()
    comment = fields.HTMLStrictField()
    motion_id = fields.RelationField(
        to=Collection("motion"),
        related_name="comment_ids",
        required=True,
        equal_fields="meeting_id",
    )
    section_id = fields.RelationField(
        to=Collection("motion_comment_section"),
        related_name="comment_ids",
        required=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_comment_ids", required=True
    )


class MotionCommentSection(Model):
    collection = Collection("motion_comment_section")
    verbose_name = "motion comment section"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    weight = fields.IntegerField(default=10000)
    comment_ids = fields.RelationListField(
        to=Collection("motion_comment"),
        related_name="section_id",
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    read_group_ids = fields.RelationListField(
        to=Collection("group"),
        related_name="read_comment_section_ids",
        equal_fields="meeting_id",
    )
    write_group_ids = fields.RelationListField(
        to=Collection("group"),
        related_name="write_comment_section_ids",
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"),
        related_name="motion_comment_section_ids",
        required=True,
    )


class MotionCategory(Model):
    collection = Collection("motion_category")
    verbose_name = "motion category"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    prefix = fields.CharField(required=True)
    weight = fields.IntegerField(default=10000)
    level = fields.IntegerField(
        read_only=True, constraints={"description": "Calculated field."}
    )
    parent_id = fields.RelationField(
        to=Collection("motion_category"),
        related_name="child_ids",
        equal_fields="meeting_id",
    )
    child_ids = fields.RelationListField(
        to=Collection("motion_category"),
        related_name="parent_id",
        equal_fields="meeting_id",
    )
    motion_ids = fields.RelationListField(
        to=Collection("motion"), related_name="category_id", equal_fields="meeting_id"
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_category_ids", required=True
    )


class MotionBlock(Model):
    collection = Collection("motion_block")
    verbose_name = "motion block"

    id = fields.IntegerField()
    title = fields.CharField(required=True)
    internal = fields.BooleanField()
    motion_ids = fields.RelationListField(
        to=Collection("motion"), related_name="block_id", equal_fields="meeting_id"
    )
    agenda_item_id = fields.RelationField(
        to=Collection("agenda_item"),
        related_name="content_object_id",
        generic_relation=True,
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to=Collection("list_of_speakers"),
        related_name="content_object_id",
        generic_relation=True,
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_block_ids", required=True
    )


class MotionChangeRecommendation(Model):
    collection = Collection("motion_change_recommendation")
    verbose_name = "motion change recommendation"

    id = fields.IntegerField()
    rejected = fields.BooleanField()
    internal = fields.BooleanField()
    type = fields.IntegerField(default=0, constraints={"enum": [0, 1, 2, 3]})
    other_description = fields.CharField()
    line_from = fields.IntegerField(constraints={"minimum": 0})
    line_to = fields.IntegerField(constraints={"minimum": 0})
    text = fields.HTMLStrictField()
    creation_time = fields.TimestampField(read_only=True)
    motion_id = fields.RelationField(
        to=Collection("motion"),
        related_name="change_recommendation_ids",
        required=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"),
        related_name="motion_change_recommendation_ids",
        required=True,
    )


class MotionState(Model):
    collection = Collection("motion_state")
    verbose_name = "motion state"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    recommendation_label = fields.CharField()
    css_class = fields.CharField(
        default="lightblue",
        constraints={"enum": ["grey", "red", "green", "lightblue", "yellow"]},
    )
    restrictions = fields.CharArrayField(
        in_array_constraints={
            "enum": [
                "motions.can_see_internal",
                "motions.can_manage_metadata",
                "motions.can_manage",
                "is_submitter",
            ]
        }
    )
    allow_support = fields.BooleanField()
    allow_create_poll = fields.BooleanField()
    allow_submitter_edit = fields.BooleanField()
    set_number = fields.BooleanField()
    show_state_extension_field = fields.BooleanField()
    merge_amendment_into_final = fields.IntegerField(
        default=0, constraints={"enum": [-1, 0, 1]}
    )
    show_recommendation_extension_field = fields.BooleanField()
    next_state_ids = fields.RelationListField(
        to=Collection("motion_state"),
        related_name="previous_state_ids",
        equal_fields=["meeting_id", "workflow_id"],
    )
    previous_state_ids = fields.RelationListField(
        to=Collection("motion_state"),
        related_name="next_state_ids",
        equal_fields=["meeting_id", "workflow_id"],
    )
    motion_ids = fields.RelationListField(
        to=Collection("motion"),
        related_name="state_id",
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    motion_recommendation_ids = fields.RelationListField(
        to=Collection("motion"),
        related_name="recommendation_id",
        equal_fields="meeting_id",
    )
    workflow_id = fields.RelationField(
        to=Collection("motion_workflow"),
        related_name="state_ids",
        required=True,
        equal_fields="meeting_id",
    )
    first_state_of_workflow_id = fields.RelationField(
        to=Collection("motion_workflow"),
        related_name="first_state_id",
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_state_ids", required=True
    )


class MotionWorkflow(Model):
    collection = Collection("motion_workflow")
    verbose_name = "motion workflow"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    state_ids = fields.RelationListField(
        to=Collection("motion_state"),
        related_name="workflow_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    first_state_id = fields.RelationField(
        to=Collection("motion_state"),
        related_name="first_state_of_workflow_id",
        required=True,
        equal_fields="meeting_id",
    )
    default_workflow_meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motions_default_workflow_id"
    )
    default_amendment_workflow_meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motions_default_amendment_workflow_id"
    )
    default_statute_amendment_workflow_meeting_id = fields.RelationField(
        to=Collection("meeting"),
        related_name="motions_default_statute_amendment_workflow_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_workflow_ids", required=True
    )


class MotionStatuteParagraph(Model):
    collection = Collection("motion_statute_paragraph")
    verbose_name = "motion statute paragraph"

    id = fields.IntegerField()
    title = fields.CharField(required=True)
    text = fields.HTMLStrictField()
    weight = fields.IntegerField(default=10000)
    motion_ids = fields.RelationListField(
        to=Collection("motion"),
        related_name="statute_paragraph_id",
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"),
        related_name="motion_statute_paragraph_ids",
        required=True,
    )


class MotionPoll(Model):
    collection = Collection("motion_poll")
    verbose_name = "motion poll"

    id = fields.IntegerField()
    pollmethod = fields.CharField()
    state = fields.IntegerField()
    type = fields.CharField()
    title = fields.CharField()
    onehundred_percent_base = fields.CharField()
    majority_method = fields.CharField()
    votesvalid = fields.DecimalField()
    votesinvalid = fields.DecimalField()
    votescast = fields.DecimalField()
    user_has_voted = fields.BooleanField()
    motion_id = fields.RelationField(
        to=Collection("motion"), related_name="poll_ids", equal_fields="meeting_id"
    )
    option_ids = fields.RelationListField(
        to=Collection("motion_option"),
        related_name="poll_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    voted_ids = fields.RelationListField(
        to=Collection("user"),
        related_name="motion_poll_voted_$_ids",
        structured_relation=["meeting_id"],
    )
    entitled_group_ids = fields.RelationListField(
        to=Collection("group"),
        related_name="motion_poll_ids",
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_poll_ids"
    )


class MotionOption(Model):
    collection = Collection("motion_option")
    verbose_name = "motion option"

    id = fields.IntegerField()
    yes = fields.DecimalField()
    no = fields.DecimalField()
    abstain = fields.DecimalField()
    poll_id = fields.RelationField(
        to=Collection("motion_poll"),
        related_name="option_ids",
        equal_fields="meeting_id",
    )
    vote_ids = fields.RelationListField(
        to=Collection("motion_vote"),
        related_name="option_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_option_ids", required=True
    )


class MotionVote(Model):
    collection = Collection("motion_vote")
    verbose_name = "motion vote"

    id = fields.IntegerField()
    weight = fields.DecimalField()
    value = fields.CharField()
    option_id = fields.RelationField(
        to=Collection("motion_option"),
        related_name="vote_ids",
        equal_fields="meeting_id",
    )
    user_id = fields.RelationField(
        to=Collection("user"),
        related_name="motion_vote_$_ids",
        structured_relation=["meeting_id"],
    )
    delegated_user_id = fields.RelationField(
        to=Collection("user"),
        related_name="motion_delegated_vote_$_ids",
        structured_relation=["meeting_id"],
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="motion_vote_ids", required=True
    )


class Assignment(Model):
    collection = Collection("assignment")
    verbose_name = "assignment"

    id = fields.IntegerField()
    title = fields.CharField(required=True)
    description = fields.HTMLStrictField()
    open_posts = fields.IntegerField(default=0, constraints={"minimum": 0})
    phase = fields.IntegerField(default=0, constraints={"enum": [0, 1, 2]})
    default_poll_description = fields.CharField()
    number_poll_candidates = fields.BooleanField()
    candidate_ids = fields.RelationListField(
        to=Collection("assignment_candidate"),
        related_name="assignment_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    poll_ids = fields.RelationListField(
        to=Collection("assignment_poll"),
        related_name="assignment_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    agenda_item_id = fields.RelationField(
        to=Collection("agenda_item"),
        related_name="content_object_id",
        generic_relation=True,
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to=Collection("list_of_speakers"),
        related_name="content_object_id",
        generic_relation=True,
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    tag_ids = fields.RelationListField(
        to=Collection("tag"),
        related_name="tagged_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    attachment_ids = fields.RelationListField(
        to=Collection("mediafile"),
        related_name="attachment_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="assignment_ids", required=True
    )


class AssignmentCandidate(Model):
    collection = Collection("assignment_candidate")
    verbose_name = "assignment candidate"

    id = fields.IntegerField()
    weight = fields.IntegerField(default=10000)
    assignment_id = fields.RelationField(
        to=Collection("assignment"),
        related_name="candidate_ids",
        equal_fields="meeting_id",
    )
    user_id = fields.RelationField(
        to=Collection("user"),
        related_name="assignment_candidate_$_ids",
        structured_relation=["meeting_id"],
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="assignment_candidate_ids", required=True
    )


class AssignmentPoll(Model):
    collection = Collection("assignment_poll")
    verbose_name = "assignment poll"

    id = fields.IntegerField()
    description = fields.CharField()
    pollmethod = fields.CharField()
    votes_amount = fields.IntegerField()
    allow_multiple_votes_per_candidate = fields.BooleanField()
    global_abstain = fields.BooleanField()
    global_no = fields.BooleanField()
    amount_global_abstain = fields.DecimalField()
    amount_global_no = fields.DecimalField()
    state = fields.IntegerField()
    title = fields.CharField()
    type = fields.CharField()
    onehundred_percent_base = fields.CharField()
    majority_method = fields.CharField()
    votescast = fields.DecimalField()
    votesinvalid = fields.DecimalField()
    votesvalid = fields.DecimalField()
    user_has_voted = fields.BooleanField()
    assignment_id = fields.RelationField(
        to=Collection("assignment"), related_name="poll_ids", equal_fields="meeting_id"
    )
    voted_ids = fields.RelationListField(
        to=Collection("user"),
        related_name="assignment_poll_voted_$_ids",
        structured_relation=["meeting_id"],
    )
    entitled_group_ids = fields.RelationListField(
        to=Collection("group"),
        related_name="assignment_poll_ids",
        equal_fields="meeting_id",
    )
    option_ids = fields.RelationListField(
        to=Collection("assignment_option"),
        related_name="poll_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="assignment_poll_ids"
    )


class AssignmentOption(Model):
    collection = Collection("assignment_option")
    verbose_name = "assignment option"

    id = fields.IntegerField()
    yes = fields.DecimalField()
    no = fields.DecimalField()
    abstain = fields.DecimalField()
    weight = fields.IntegerField(default=10000)
    poll_id = fields.RelationField(
        to=Collection("assignment_poll"),
        related_name="option_ids",
        equal_fields="meeting_id",
    )
    user_id = fields.RelationField(
        to=Collection("user"),
        related_name="assignment_option_$_ids",
        structured_relation=["meeting_id"],
    )
    vote_ids = fields.RelationListField(
        to=Collection("assignment_vote"),
        related_name="option_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="assignment_option_ids", required=True
    )


class AssignmentVote(Model):
    collection = Collection("assignment_vote")
    verbose_name = "assignment vote"

    id = fields.IntegerField()
    value = fields.CharField()
    weight = fields.DecimalField()
    option_id = fields.RelationField(
        to=Collection("assignment_option"),
        related_name="vote_ids",
        equal_fields="meeting_id",
    )
    user_id = fields.RelationField(
        to=Collection("user"),
        related_name="assignment_vote_$_ids",
        structured_relation=["meeting_id"],
    )
    delegated_user_id = fields.RelationField(
        to=Collection("user"),
        related_name="assignment_delegated_vote_$_ids",
        structured_relation=["meeting_id"],
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="assignment_vote_ids", required=True
    )


class Mediafile(Model):
    collection = Collection("mediafile")
    verbose_name = "mediafile"

    id = fields.IntegerField()
    title = fields.CharField(
        constraints={"description": "Title and parent_id must be unique."}
    )
    is_directory = fields.BooleanField()
    filesize = fields.IntegerField(
        read_only=True,
        constraints={"description": "In bytes, not the human readable format anymore."},
    )
    filename = fields.CharField(
        required=True,
        constraints={
            "descriptin": "The uploaded filename. Will be used for downloading. Only writeable on create."
        },
    )
    mimetype = fields.CharField()
    pdf_information = fields.JSONField()
    create_timestamp = fields.TimestampField()
    is_public = fields.BooleanField(
        read_only=True,
        constraints={
            "description": "Calculated field. inherited_access_group_ids == [] can have two causes: cancelling access groups (=> is_public := false) or no access groups at all (=> is_public := true)"
        },
    )
    inherited_access_group_ids = fields.RelationListField(
        to=Collection("group"),
        related_name="mediafile_inherited_access_group_ids",
        read_only=True,
        constraints={"description": "Calculated field."},
    )
    access_group_ids = fields.RelationListField(
        to=Collection("group"),
        related_name="mediafile_access_group_ids",
        equal_fields="meeting_id",
    )
    parent_id = fields.RelationField(
        to=Collection("mediafile"), related_name="child_ids", equal_fields="meeting_id"
    )
    child_ids = fields.RelationListField(
        to=Collection("mediafile"), related_name="parent_id", equal_fields="meeting_id"
    )
    list_of_speakers_id = fields.RelationField(
        to=Collection("list_of_speakers"),
        related_name="content_object_id",
        generic_relation=True,
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    attachment_ids = fields.GenericRelationListField(
        to=[Collection("motion"), Collection("topic"), Collection("assignment")],
        related_name="attachment_ids",
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="mediafile_ids", required=True
    )
    used_as_logo__in_meeting_id = fields.TemplateRelationField(
        replacement="place",
        index=13,
        to=Collection("meeting"),
        related_name="logo_$_id",
        structured_tag="place",
    )
    used_as_font__in_meeting_id = fields.TemplateRelationField(
        replacement="place",
        index=13,
        to=Collection("meeting"),
        related_name="font_$_id",
        structured_tag="place",
    )


class Projector(Model):
    collection = Collection("projector")
    verbose_name = "projector"

    id = fields.IntegerField()
    name = fields.CharField()
    scale = fields.IntegerField()
    scroll = fields.IntegerField()
    width = fields.IntegerField()
    aspect_ratio_numerator = fields.IntegerField()
    aspect_ratio_denominator = fields.IntegerField()
    color = fields.CharField()
    background_color = fields.CharField()
    header_background_color = fields.CharField()
    header_font_color = fields.CharField()
    header_h1_color = fields.CharField()
    chyron_background_color = fields.CharField()
    chyron_font_color = fields.CharField()
    show_header_footer = fields.BooleanField()
    show_title = fields.BooleanField()
    show_logo = fields.BooleanField()
    current_projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="current_projector_id",
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    current_element_ids = fields.GenericRelationListField(
        to=[
            Collection("motion"),
            Collection("mediafile"),
            Collection("list_of_speakers"),
            Collection("motion_block"),
            Collection("assignment"),
            Collection("agenda_item"),
            Collection("topic"),
            Collection("user"),
            Collection("assignment_poll"),
            Collection("motion_poll"),
            Collection("projector_message"),
            Collection("projector_countdown"),
        ],
        related_name="current_projector_ids",
        equal_fields="meeting_id",
    )
    preview_projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="preview_projector_id",
        equal_fields="meeting_id",
    )
    history_projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="history_projector_id",
        equal_fields="meeting_id",
    )
    used_as_reference_projector_meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="reference_projector_id"
    )
    projectiondefault_ids = fields.RelationListField(
        to=Collection("projectiondefault"),
        related_name="projector_id",
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="projector_ids"
    )


class Projection(Model):
    collection = Collection("projection")
    verbose_name = "projection"

    id = fields.IntegerField()
    options = fields.JSONField()
    current_projector_id = fields.RelationField(
        to=Collection("projector"),
        related_name="current_projection_ids",
        equal_fields="meeting_id",
    )
    preview_projector_id = fields.RelationField(
        to=Collection("projector"),
        related_name="preview_projection_ids",
        equal_fields="meeting_id",
    )
    history_projector_id = fields.RelationField(
        to=Collection("projector"),
        related_name="history_projection_ids",
        equal_fields="meeting_id",
    )
    element_id = fields.GenericRelationField(
        to=[
            Collection("motion"),
            Collection("mediafile"),
            Collection("list_of_speakers"),
            Collection("motion_block"),
            Collection("assignment"),
            Collection("agenda_item"),
            Collection("topic"),
            Collection("user"),
            Collection("assignment_poll"),
            Collection("motion_poll"),
            Collection("projector_message"),
            Collection("projector_countdown"),
        ],
        related_name="projection_ids",
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="projection_ids", required=True
    )


class Projectiondefault(Model):
    collection = Collection("projectiondefault")
    verbose_name = "projectiondefault"

    id = fields.IntegerField()
    name = fields.CharField()
    display_name = fields.CharField()
    projector_id = fields.RelationField(
        to=Collection("projector"),
        related_name="projectiondefault_ids",
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="projectiondefault_ids"
    )


class ProjectorMessage(Model):
    collection = Collection("projector_message")
    verbose_name = "projector message"

    id = fields.IntegerField()
    message = fields.HTMLStrictField()
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="projector_message_ids"
    )


class ProjectorCountdown(Model):
    collection = Collection("projector_countdown")
    verbose_name = "projector countdown"

    id = fields.IntegerField()
    title = fields.CharField()
    description = fields.CharField()
    default_time = fields.IntegerField()
    countdown_time = fields.IntegerField()
    running = fields.BooleanField()
    projection_ids = fields.RelationListField(
        to=Collection("projection"),
        related_name="element_id",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=Collection("projector"),
        related_name="current_element_ids",
        generic_relation=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=Collection("meeting"), related_name="projector_countdown_ids"
    )
