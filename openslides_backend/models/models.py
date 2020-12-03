# Code generated. DO NOT EDIT.

from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.patterns import Collection

MODELS_YML_CHECKSUM = "d8c1f7bc06c503e4595fb6f951ab5090"


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
        to=[
            {
                "collection": Collection("committee"),
                "field": {"name": "organisation_id"},
            }
        ]
    )
    role_ids = fields.RelationListField(
        to=[{"collection": Collection("role"), "field": {"name": "organisation_id"}}]
    )
    superadmin_role_id = fields.RelationField(
        to=[
            {
                "collection": Collection("role"),
                "field": {"name": "superadmin_role_for_organisation_id"},
            }
        ]
    )
    resource_ids = fields.RelationListField(
        to=[
            {"collection": Collection("resource"), "field": {"name": "organisation_id"}}
        ]
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
    role_id = fields.RelationField(
        to=[{"collection": Collection("role"), "field": {"name": "user_ids"}}]
    )
    is_present_in_meeting_ids = fields.RelationListField(
        to=[
            {"collection": Collection("meeting"), "field": {"name": "present_user_ids"}}
        ]
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "temporary_user_ids"},
            }
        ]
    )
    guest_meeting_ids = fields.RelationListField(
        to=[{"collection": Collection("meeting"), "field": {"name": "guest_ids"}}]
    )
    committee_as_member_ids = fields.RelationListField(
        to=[{"collection": Collection("committee"), "field": {"name": "member_ids"}}]
    )
    committee_as_manager_ids = fields.RelationListField(
        to=[{"collection": Collection("committee"), "field": {"name": "manager_ids"}}]
    )
    group__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=6,
        to=[{"collection": Collection("group"), "field": {"name": "user_ids"}}],
    )
    speaker__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=8,
        to=[{"collection": Collection("speaker"), "field": {"name": "user_id"}}],
    )
    personal_note__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=14,
        to=[{"collection": Collection("personal_note"), "field": {"name": "user_id"}}],
    )
    supported_motion__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=17,
        to=[{"collection": Collection("motion"), "field": {"name": "supporter_ids"}}],
    )
    submitted_motion__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=17,
        to=[
            {"collection": Collection("motion_submitter"), "field": {"name": "user_id"}}
        ],
    )
    poll_voted__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=11,
        to=[{"collection": Collection("poll"), "field": {"name": "voted_ids"}}],
    )
    option__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=7,
        to=[
            {
                "collection": Collection("option"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
    )
    vote__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=5,
        to=[{"collection": Collection("vote"), "field": {"name": "user_id"}}],
    )
    vote_delegated_vote__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=20,
        to=[{"collection": Collection("vote"), "field": {"name": "delegated_user_id"}}],
    )
    assignment_candidate__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=21,
        to=[
            {
                "collection": Collection("assignment_candidate"),
                "field": {"name": "user_id"},
            }
        ],
    )
    projection__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=11,
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
    )
    current_projector__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=18,
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
    )
    vote_delegated__to_id = fields.TemplateRelationField(
        replacement="meeting_id",
        index=15,
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "vote_delegations_$_from_ids",
                    "structured_relation": "['meeting_id']",
                },
            }
        ],
    )
    vote_delegations__from_ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=17,
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "vote_delegated_$_to_id",
                    "structured_relation": "['meeting_id']",
                },
            }
        ],
    )


class Role(Model):
    collection = Collection("role")
    verbose_name = "role"

    id = fields.IntegerField()
    name = fields.CharField()
    permissions = fields.CharArrayField()
    organisation_id = fields.OrganisationField(
        to=[{"collection": Collection("organisation"), "field": {"name": "role_ids"}}]
    )
    superadmin_role_for_organisation_id = fields.RelationField(
        to=[
            {
                "collection": Collection("organisation"),
                "field": {"name": "superadmin_role_id"},
            }
        ]
    )
    user_ids = fields.RelationListField(
        to=[{"collection": Collection("user"), "field": {"name": "role_id"}}]
    )


class Resource(Model):
    collection = Collection("resource")
    verbose_name = "resource"

    id = fields.IntegerField()
    token = fields.CharField()
    filesize = fields.IntegerField()
    mimetype = fields.CharField()
    organisation_id = fields.OrganisationField(
        to=[
            {
                "collection": Collection("organisation"),
                "field": {"name": "resource_ids"},
            }
        ]
    )


class Committee(Model):
    collection = Collection("committee")
    verbose_name = "committee"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    description = fields.HTMLStrictField()
    meeting_ids = fields.RelationListField(
        to=[{"collection": Collection("meeting"), "field": {"name": "committee_id"}}],
        on_delete=fields.OnDelete.PROTECT,
    )
    template_meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "template_for_committee_id"},
            }
        ]
    )
    default_meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "default_meeting_for_committee_id"},
            }
        ]
    )
    member_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("user"),
                "field": {"name": "committee_as_member_ids"},
            }
        ]
    )
    manager_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("user"),
                "field": {"name": "committee_as_manager_ids"},
            }
        ]
    )
    forward_to_committee_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("committee"),
                "field": {"name": "receive_forwardings_from_committee_ids"},
            }
        ]
    )
    receive_forwardings_from_committee_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("committee"),
                "field": {"name": "forward_to_committee_ids"},
            }
        ]
    )
    organisation_id = fields.OrganisationField(
        to=[
            {
                "collection": Collection("organisation"),
                "field": {"name": "committee_ids"},
            }
        ],
        required=True,
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
        to=[
            {
                "collection": Collection("committee"),
                "field": {"name": "template_meeting_id"},
            }
        ]
    )
    enable_anonymous = fields.BooleanField()
    conference_show = fields.BooleanField()
    conference_auto_connect = fields.BooleanField()
    conference_los_restriction = fields.BooleanField()
    conference_stream_url = fields.CharField()
    conference_stream_poster_url = fields.CharField()
    conference_open_microphone = fields.BooleanField()
    conference_open_video = fields.BooleanField()
    conference_auto_connect_next_speakers = fields.BooleanField()
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
    list_of_speakers_enable_point_of_order_speakers = fields.BooleanField()
    motions_default_workflow_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion_workflow"),
                "field": {"name": "default_workflow_meeting_id"},
            }
        ],
        required=True,
    )
    motions_default_amendment_workflow_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion_workflow"),
                "field": {"name": "default_amendment_workflow_meeting_id"},
            }
        ],
        required=True,
    )
    motions_default_statute_amendment_workflow_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion_workflow"),
                "field": {"name": "default_statute_amendment_workflow_meeting_id"},
            }
        ],
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
        to=[
            {
                "collection": Collection("group"),
                "field": {"name": "used_as_motion_poll_default_id"},
            }
        ]
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
        to=[
            {
                "collection": Collection("group"),
                "field": {"name": "used_as_assignment_poll_default_id"},
            }
        ]
    )
    poll_ballot_paper_selection = fields.CharField(
        constraints={
            "enum": [
                "NUMBER_OF_DELEGATES",
                "NUMBER_OF_ALL_PARTICIPANTS",
                "CUSTOM_NUMBER",
            ]
        }
    )
    poll_ballot_paper_number = fields.IntegerField()
    poll_sort_poll_result_by_votes = fields.BooleanField()
    poll_default_type = fields.CharField()
    poll_default_method = fields.CharField()
    poll_default_100_percent_base = fields.CharField()
    poll_default_majority_method = fields.CharField()
    poll_default_group_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("group"),
                "field": {"name": "used_as_poll_default_id"},
            }
        ]
    )
    projector_ids = fields.RelationListField(
        to=[{"collection": Collection("projector"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    projection_ids = fields.RelationListField(
        to=[{"collection": Collection("projection"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    projectiondefault_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projectiondefault"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    projector_message_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector_message"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    projector_countdown_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector_countdown"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    tag_ids = fields.RelationListField(
        to=[{"collection": Collection("tag"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    agenda_item_ids = fields.RelationListField(
        to=[{"collection": Collection("agenda_item"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    list_of_speakers_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("list_of_speakers"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    speaker_ids = fields.RelationListField(
        to=[{"collection": Collection("speaker"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    topic_ids = fields.RelationListField(
        to=[{"collection": Collection("topic"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    group_ids = fields.RelationListField(
        to=[{"collection": Collection("group"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    mediafile_ids = fields.RelationListField(
        to=[{"collection": Collection("mediafile"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_ids = fields.RelationListField(
        to=[{"collection": Collection("motion"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_comment_section_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_comment_section"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_category_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_category"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_block_ids = fields.RelationListField(
        to=[
            {"collection": Collection("motion_block"), "field": {"name": "meeting_id"}}
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_workflow_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_workflow"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_statute_paragraph_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_statute_paragraph"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_comment_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_comment"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_submitter_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_submitter"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_change_recommendation_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_change_recommendation"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_state_ids = fields.RelationListField(
        to=[
            {"collection": Collection("motion_state"), "field": {"name": "meeting_id"}}
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    poll_ids = fields.RelationListField(
        to=[{"collection": Collection("poll"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    option_ids = fields.RelationListField(
        to=[{"collection": Collection("option"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    vote_ids = fields.RelationListField(
        to=[{"collection": Collection("vote"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    assignment_ids = fields.RelationListField(
        to=[{"collection": Collection("assignment"), "field": {"name": "meeting_id"}}],
        on_delete=fields.OnDelete.CASCADE,
    )
    assignment_candidate_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("assignment_candidate"),
                "field": {"name": "meeting_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    personal_note_ids = fields.RelationListField(
        to=[
            {"collection": Collection("personal_note"), "field": {"name": "meeting_id"}}
        ],
        on_delete=fields.OnDelete.CASCADE,
    )
    logo__id = fields.TemplateRelationField(
        replacement="place",
        index=5,
        to=[
            {
                "collection": Collection("mediafile"),
                "field": {
                    "name": "used_as_logo_$_in_meeting_id",
                    "structured_tag": "place",
                },
            }
        ],
    )
    font__id = fields.TemplateRelationField(
        replacement="place",
        index=5,
        to=[
            {
                "collection": Collection("mediafile"),
                "field": {
                    "name": "used_as_font_$_in_meeting_id",
                    "structured_tag": "place",
                },
            }
        ],
    )
    committee_id = fields.RelationField(
        to=[{"collection": Collection("committee"), "field": {"name": "meeting_ids"}}],
        required=True,
    )
    default_meeting_for_committee_id = fields.RelationField(
        to=[
            {
                "collection": Collection("committee"),
                "field": {"name": "default_meeting_id"},
            }
        ]
    )
    present_user_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("user"),
                "field": {"name": "is_present_in_meeting_ids"},
            }
        ]
    )
    temporary_user_ids = fields.RelationListField(
        to=[{"collection": Collection("user"), "field": {"name": "meeting_id"}}]
    )
    guest_ids = fields.RelationListField(
        to=[{"collection": Collection("user"), "field": {"name": "guest_meeting_ids"}}]
    )
    user_ids = fields.NumberArrayField(
        read_only=True,
        constraints={
            "decription": "Calculated. All ids from temporary_user_ids, guest_ids and all users assigned to groups."
        },
    )
    reference_projector_id = fields.RelationField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {"name": "used_as_reference_projector_meeting_id"},
            }
        ]
    )
    default_group_id = fields.RelationField(
        to=[
            {
                "collection": Collection("group"),
                "field": {"name": "default_group_for_meeting_id"},
            }
        ],
        required=True,
    )
    superadmin_group_id = fields.RelationField(
        to=[
            {
                "collection": Collection("group"),
                "field": {"name": "superadmin_group_for_meeting_id"},
            }
        ]
    )


class Group(Model):
    collection = Collection("group")
    verbose_name = "group"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    permissions = fields.CharArrayField()
    user_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "group_$_ids",
                    "structured_relation": "['meeting_id']",
                },
            }
        ]
    )
    default_group_for_meeting_id = fields.RelationField(
        to=[
            {"collection": Collection("meeting"), "field": {"name": "default_group_id"}}
        ],
        on_delete=fields.OnDelete.PROTECT,
    )
    superadmin_group_for_meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "superadmin_group_id"},
            }
        ],
        on_delete=fields.OnDelete.PROTECT,
    )
    mediafile_access_group_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("mediafile"),
                "field": {"name": "access_group_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    mediafile_inherited_access_group_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("mediafile"),
                "field": {"name": "inherited_access_group_ids"},
            }
        ],
        read_only=True,
        constraints={"description": "Calculated field."},
    )
    read_comment_section_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_comment_section"),
                "field": {"name": "read_group_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    write_comment_section_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_comment_section"),
                "field": {"name": "write_group_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    poll_ids = fields.RelationListField(
        to=[
            {"collection": Collection("poll"), "field": {"name": "entitled_group_ids"}}
        ],
        equal_fields="meeting_id",
    )
    used_as_motion_poll_default_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motion_poll_default_group_ids"},
            }
        ]
    )
    used_as_assignment_poll_default_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "assignment_poll_default_group_ids"},
            }
        ]
    )
    used_as_poll_default_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "poll_default_group_ids"},
            }
        ]
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "group_ids"}}],
        required=True,
    )


class PersonalNote(Model):
    collection = Collection("personal_note")
    verbose_name = "personal note"

    id = fields.IntegerField()
    note = fields.HTMLStrictField()
    star = fields.BooleanField()
    user_id = fields.RelationField(
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "personal_note_$_ids",
                    "structured_relation": "['meeting_id']",
                },
            }
        ]
    )
    content_object_id = fields.GenericRelationField(
        to=[
            {"collection": Collection("motion"), "field": {"name": "personal_note_ids"}}
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "personal_note_ids"},
            }
        ],
        required=True,
    )


class Tag(Model):
    collection = Collection("tag")
    verbose_name = "tag"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    tagged_ids = fields.GenericRelationListField(
        to=[
            {"collection": Collection("agenda_item"), "field": {"name": "tag_ids"}},
            {"collection": Collection("assignment"), "field": {"name": "tag_ids"}},
            {"collection": Collection("motion"), "field": {"name": "tag_ids"}},
            {"collection": Collection("topic"), "field": {"name": "tag_ids"}},
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "tag_ids"}}],
        required=True,
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
            {"collection": Collection("motion"), "field": {"name": "agenda_item_id"}},
            {
                "collection": Collection("motion_block"),
                "field": {"name": "agenda_item_id"},
            },
            {
                "collection": Collection("assignment"),
                "field": {"name": "agenda_item_id"},
            },
            {"collection": Collection("topic"), "field": {"name": "agenda_item_id"}},
        ],
        required=True,
        equal_fields="meeting_id",
    )
    parent_id = fields.RelationField(
        to=[{"collection": Collection("agenda_item"), "field": {"name": "child_ids"}}],
        equal_fields="meeting_id",
    )
    child_ids = fields.RelationListField(
        to=[{"collection": Collection("agenda_item"), "field": {"name": "parent_id"}}],
        equal_fields="meeting_id",
    )
    tag_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("tag"),
                "field": {
                    "name": "tagged_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {"collection": Collection("meeting"), "field": {"name": "agenda_item_ids"}}
        ],
        required=True,
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
            {
                "collection": Collection("motion"),
                "field": {"name": "list_of_speakers_id"},
            },
            {
                "collection": Collection("motion_block"),
                "field": {"name": "list_of_speakers_id"},
            },
            {
                "collection": Collection("assignment"),
                "field": {"name": "list_of_speakers_id"},
            },
            {
                "collection": Collection("topic"),
                "field": {"name": "list_of_speakers_id"},
            },
            {
                "collection": Collection("mediafile"),
                "field": {"name": "list_of_speakers_id"},
            },
        ],
        required=True,
        equal_fields="meeting_id",
    )
    speaker_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("speaker"),
                "field": {"name": "list_of_speakers_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "list_of_speakers_ids"},
            }
        ],
        required=True,
    )


class Speaker(Model):
    collection = Collection("speaker")
    verbose_name = "speaker"

    id = fields.IntegerField()
    begin_time = fields.TimestampField(read_only=True)
    end_time = fields.TimestampField(read_only=True)
    weight = fields.IntegerField(default=10000)
    marked = fields.BooleanField()
    point_of_order = fields.BooleanField()
    list_of_speakers_id = fields.RelationField(
        to=[
            {
                "collection": Collection("list_of_speakers"),
                "field": {"name": "speaker_ids"},
            }
        ],
        required=True,
        equal_fields="meeting_id",
    )
    user_id = fields.RelationField(
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "speaker_$_ids",
                    "structured_relation": "['meeting_id']",
                },
            }
        ],
        required=True,
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "speaker_ids"}}],
        required=True,
    )


class Topic(Model):
    collection = Collection("topic")
    verbose_name = "topic"

    id = fields.IntegerField()
    title = fields.CharField(required=True)
    text = fields.HTMLPermissiveField()
    attachment_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("mediafile"),
                "field": {
                    "name": "attachment_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    agenda_item_id = fields.RelationField(
        to=[
            {
                "collection": Collection("agenda_item"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to=[
            {
                "collection": Collection("list_of_speakers"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    option_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("option"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    tag_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("tag"),
                "field": {
                    "name": "tagged_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "topic_ids"}}],
        required=True,
    )


class Motion(Model):
    collection = Collection("motion")
    verbose_name = "motion"

    id = fields.IntegerField()
    number = fields.CharField()
    number_value = fields.IntegerField()
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
        to=[{"collection": Collection("motion"), "field": {"name": "amendment_ids"}}],
        equal_fields="meeting_id",
    )
    amendment_ids = fields.RelationListField(
        to=[{"collection": Collection("motion"), "field": {"name": "lead_motion_id"}}],
        equal_fields="meeting_id",
    )
    sort_parent_id = fields.RelationField(
        to=[{"collection": Collection("motion"), "field": {"name": "sort_child_ids"}}],
        equal_fields="meeting_id",
    )
    sort_child_ids = fields.RelationListField(
        to=[{"collection": Collection("motion"), "field": {"name": "sort_parent_id"}}],
        equal_fields="meeting_id",
    )
    origin_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion"),
                "field": {"name": "derived_motion_ids"},
            }
        ]
    )
    derived_motion_ids = fields.RelationListField(
        to=[{"collection": Collection("motion"), "field": {"name": "origin_id"}}]
    )
    forwarding_tree_motion_ids = fields.NumberArrayField()
    state_id = fields.RelationField(
        to=[
            {"collection": Collection("motion_state"), "field": {"name": "motion_ids"}}
        ],
        required=True,
        equal_fields="meeting_id",
    )
    recommendation_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion_state"),
                "field": {"name": "motion_recommendation_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    recommendation_extension_reference_ids = fields.GenericRelationListField(
        to=[
            {
                "collection": Collection("motion"),
                "field": {"name": "referenced_in_motion_recommendation_extension_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    referenced_in_motion_recommendation_extension_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion"),
                "field": {
                    "name": "recommendation_extension_reference_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    category_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion_category"),
                "field": {"name": "motion_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    block_id = fields.RelationField(
        to=[
            {"collection": Collection("motion_block"), "field": {"name": "motion_ids"}}
        ],
        equal_fields="meeting_id",
    )
    submitter_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_submitter"),
                "field": {"name": "motion_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    supporter_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "supported_motion_$_ids",
                    "structured_relation": "['meeting_id']",
                },
            }
        ],
        equal_fields="meeting_id",
    )
    poll_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("poll"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    option_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("option"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    change_recommendation_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_change_recommendation"),
                "field": {"name": "motion_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    statute_paragraph_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion_statute_paragraph"),
                "field": {"name": "motion_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    comment_ids = fields.RelationListField(
        to=[
            {"collection": Collection("motion_comment"), "field": {"name": "motion_id"}}
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    agenda_item_id = fields.RelationField(
        to=[
            {
                "collection": Collection("agenda_item"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to=[
            {
                "collection": Collection("list_of_speakers"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    tag_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("tag"),
                "field": {
                    "name": "tagged_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    attachment_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("mediafile"),
                "field": {
                    "name": "attachment_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    personal_note_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("personal_note"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "motion_ids"}}],
        required=True,
    )


class MotionSubmitter(Model):
    collection = Collection("motion_submitter")
    verbose_name = "motion submitter"

    id = fields.IntegerField()
    weight = fields.IntegerField(default=10000)
    user_id = fields.RelationField(
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "submitted_motion_$_ids",
                    "structured_relation": "['meeting_id']",
                },
            }
        ]
    )
    motion_id = fields.RelationField(
        to=[{"collection": Collection("motion"), "field": {"name": "submitter_ids"}}],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motion_submitter_ids"},
            }
        ],
        required=True,
    )


class MotionComment(Model):
    collection = Collection("motion_comment")
    verbose_name = "motion comment"

    id = fields.IntegerField()
    comment = fields.HTMLStrictField()
    motion_id = fields.RelationField(
        to=[{"collection": Collection("motion"), "field": {"name": "comment_ids"}}],
        required=True,
        equal_fields="meeting_id",
    )
    section_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion_comment_section"),
                "field": {"name": "comment_ids"},
            }
        ],
        required=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motion_comment_ids"},
            }
        ],
        required=True,
    )


class MotionCommentSection(Model):
    collection = Collection("motion_comment_section")
    verbose_name = "motion comment section"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    weight = fields.IntegerField(default=10000)
    comment_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_comment"),
                "field": {"name": "section_id"},
            }
        ],
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    read_group_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("group"),
                "field": {"name": "read_comment_section_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    write_group_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("group"),
                "field": {"name": "write_comment_section_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motion_comment_section_ids"},
            }
        ],
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
        to=[
            {
                "collection": Collection("motion_category"),
                "field": {"name": "child_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    child_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_category"),
                "field": {"name": "parent_id"},
            }
        ],
        equal_fields="meeting_id",
    )
    motion_ids = fields.RelationListField(
        to=[{"collection": Collection("motion"), "field": {"name": "category_id"}}],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motion_category_ids"},
            }
        ],
        required=True,
    )


class MotionBlock(Model):
    collection = Collection("motion_block")
    verbose_name = "motion block"

    id = fields.IntegerField()
    title = fields.CharField(required=True)
    internal = fields.BooleanField()
    motion_ids = fields.RelationListField(
        to=[{"collection": Collection("motion"), "field": {"name": "block_id"}}],
        equal_fields="meeting_id",
    )
    agenda_item_id = fields.RelationField(
        to=[
            {
                "collection": Collection("agenda_item"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to=[
            {
                "collection": Collection("list_of_speakers"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {"collection": Collection("meeting"), "field": {"name": "motion_block_ids"}}
        ],
        required=True,
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
        to=[
            {
                "collection": Collection("motion"),
                "field": {"name": "change_recommendation_ids"},
            }
        ],
        required=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motion_change_recommendation_ids"},
            }
        ],
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
        to=[
            {
                "collection": Collection("motion_state"),
                "field": {"name": "previous_state_ids"},
            }
        ],
        equal_fields=["meeting_id", "workflow_id"],
    )
    previous_state_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion_state"),
                "field": {"name": "next_state_ids"},
            }
        ],
        equal_fields=["meeting_id", "workflow_id"],
    )
    motion_ids = fields.RelationListField(
        to=[{"collection": Collection("motion"), "field": {"name": "state_id"}}],
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    motion_recommendation_ids = fields.RelationListField(
        to=[
            {"collection": Collection("motion"), "field": {"name": "recommendation_id"}}
        ],
        equal_fields="meeting_id",
    )
    workflow_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion_workflow"),
                "field": {"name": "state_ids"},
            }
        ],
        required=True,
        equal_fields="meeting_id",
    )
    first_state_of_workflow_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion_workflow"),
                "field": {"name": "first_state_id"},
            }
        ],
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {"collection": Collection("meeting"), "field": {"name": "motion_state_ids"}}
        ],
        required=True,
    )


class MotionWorkflow(Model):
    collection = Collection("motion_workflow")
    verbose_name = "motion workflow"

    id = fields.IntegerField()
    name = fields.CharField(required=True)
    state_ids = fields.RelationListField(
        to=[
            {"collection": Collection("motion_state"), "field": {"name": "workflow_id"}}
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    first_state_id = fields.RelationField(
        to=[
            {
                "collection": Collection("motion_state"),
                "field": {"name": "first_state_of_workflow_id"},
            }
        ],
        required=True,
        equal_fields="meeting_id",
    )
    default_workflow_meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motions_default_workflow_id"},
            }
        ]
    )
    default_amendment_workflow_meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motions_default_amendment_workflow_id"},
            }
        ]
    )
    default_statute_amendment_workflow_meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motions_default_statute_amendment_workflow_id"},
            }
        ]
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motion_workflow_ids"},
            }
        ],
        required=True,
    )


class MotionStatuteParagraph(Model):
    collection = Collection("motion_statute_paragraph")
    verbose_name = "motion statute paragraph"

    id = fields.IntegerField()
    title = fields.CharField(required=True)
    text = fields.HTMLStrictField()
    weight = fields.IntegerField(default=10000)
    motion_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("motion"),
                "field": {"name": "statute_paragraph_id"},
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "motion_statute_paragraph_ids"},
            }
        ],
        required=True,
    )


class Poll(Model):
    collection = Collection("poll")
    verbose_name = "poll"

    id = fields.IntegerField()
    description = fields.CharField()
    title = fields.CharField(required=True)
    type = fields.CharField(
        required=True, constraints={"enum": ["analog", "named", "pseudoanonymous"]}
    )
    pollmethod = fields.CharField(
        required=True, constraints={"enum": ["Y", "YN", "YNA", "N"]}
    )
    state = fields.IntegerField(default=1, constraints={"enum": [1, 2, 3, 4]})
    min_votes_amount = fields.IntegerField(default=1)
    max_votes_amount = fields.IntegerField(default=1)
    allow_multiple_votes_per_candidate = fields.BooleanField(default=False)
    global_yes = fields.BooleanField(default=False)
    global_no = fields.BooleanField(default=False)
    global_abstain = fields.BooleanField(default=False)
    onehundred_percent_base = fields.CharField(
        required=True,
        constraints={"enum": ["Y", "YN", "YNA", "valid", "cast", "disabled"]},
    )
    majority_method = fields.CharField(
        required=True,
        constraints={"enum": ["simple", "two_thirds", "three_quarters", "disabled"]},
    )
    amount_global_yes = fields.DecimalField()
    amount_global_no = fields.DecimalField()
    amount_global_abstain = fields.DecimalField()
    votesvalid = fields.DecimalField()
    votesinvalid = fields.DecimalField()
    votescast = fields.DecimalField()
    user_has_voted = fields.BooleanField()
    user_has_voted_for_delegations = fields.NumberArrayField()
    content_object_id = fields.GenericRelationField(
        to=[
            {"collection": Collection("motion"), "field": {"name": "poll_ids"}},
            {"collection": Collection("assignment"), "field": {"name": "poll_ids"}},
        ],
        equal_fields="meeting_id",
    )
    option_ids = fields.RelationListField(
        to=[{"collection": Collection("option"), "field": {"name": "poll_id"}}],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    voted_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "poll_voted_$_ids",
                    "structured_relation": "['meeting_id']",
                },
            }
        ]
    )
    entitled_group_ids = fields.RelationListField(
        to=[{"collection": Collection("group"), "field": {"name": "poll_ids"}}],
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "poll_ids"}}]
    )


class Option(Model):
    collection = Collection("option")
    verbose_name = "option"

    id = fields.IntegerField()
    weight = fields.IntegerField(default=10000)
    text = fields.HTMLStrictField()
    yes = fields.DecimalField()
    no = fields.DecimalField()
    abstain = fields.DecimalField()
    poll_id = fields.RelationField(
        to=[{"collection": Collection("poll"), "field": {"name": "option_ids"}}],
        required=True,
        equal_fields="meeting_id",
    )
    vote_ids = fields.RelationListField(
        to=[{"collection": Collection("vote"), "field": {"name": "option_id"}}],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    content_object_id = fields.GenericRelationField(
        to=[
            {"collection": Collection("motion"), "field": {"name": "option_ids"}},
            {"collection": Collection("topic"), "field": {"name": "option_ids"}},
            {
                "collection": Collection("user"),
                "field": {
                    "name": "option_$_ids",
                    "type": "structured-relation",
                    "replacement": "meeting_id",
                    "structured_relation": "['meeting_id']",
                },
            },
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "option_ids"}}],
        required=True,
    )


class Vote(Model):
    collection = Collection("vote")
    verbose_name = "vote"

    id = fields.IntegerField()
    weight = fields.DecimalField()
    value = fields.CharField()
    option_id = fields.RelationField(
        to=[{"collection": Collection("option"), "field": {"name": "vote_ids"}}],
        required=True,
        equal_fields="meeting_id",
    )
    user_id = fields.RelationField(
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "vote_$_ids",
                    "structured_relation": "['meeting_id']",
                },
            }
        ]
    )
    delegated_user_id = fields.RelationField(
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "vote_delegated_vote_$_ids",
                    "structured_relation": "['meeting_id']",
                },
            }
        ]
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "vote_ids"}}],
        required=True,
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
        to=[
            {
                "collection": Collection("assignment_candidate"),
                "field": {"name": "assignment_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    poll_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("poll"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    agenda_item_id = fields.RelationField(
        to=[
            {
                "collection": Collection("agenda_item"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to=[
            {
                "collection": Collection("list_of_speakers"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    tag_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("tag"),
                "field": {
                    "name": "tagged_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    attachment_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("mediafile"),
                "field": {
                    "name": "attachment_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "assignment_ids"}}],
        required=True,
    )


class AssignmentCandidate(Model):
    collection = Collection("assignment_candidate")
    verbose_name = "assignment candidate"

    id = fields.IntegerField()
    weight = fields.IntegerField(default=10000)
    assignment_id = fields.RelationField(
        to=[
            {"collection": Collection("assignment"), "field": {"name": "candidate_ids"}}
        ],
        equal_fields="meeting_id",
    )
    user_id = fields.RelationField(
        to=[
            {
                "collection": Collection("user"),
                "field": {
                    "name": "assignment_candidate_$_ids",
                    "structured_relation": "['meeting_id']",
                },
            }
        ]
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "assignment_candidate_ids"},
            }
        ],
        required=True,
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
        to=[
            {
                "collection": Collection("group"),
                "field": {"name": "mediafile_inherited_access_group_ids"},
            }
        ],
        read_only=True,
        constraints={"description": "Calculated field."},
    )
    access_group_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("group"),
                "field": {"name": "mediafile_access_group_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    parent_id = fields.RelationField(
        to=[{"collection": Collection("mediafile"), "field": {"name": "child_ids"}}],
        equal_fields="meeting_id",
    )
    child_ids = fields.RelationListField(
        to=[{"collection": Collection("mediafile"), "field": {"name": "parent_id"}}],
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to=[
            {
                "collection": Collection("list_of_speakers"),
                "field": {
                    "name": "content_object_id",
                    "generic_relation": True,
                },
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    attachment_ids = fields.GenericRelationListField(
        to=[
            {"collection": Collection("motion"), "field": {"name": "attachment_ids"}},
            {"collection": Collection("topic"), "field": {"name": "attachment_ids"}},
            {
                "collection": Collection("assignment"),
                "field": {"name": "attachment_ids"},
            },
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "mediafile_ids"}}],
        required=True,
    )
    used_as_logo__in_meeting_id = fields.TemplateRelationField(
        replacement="place",
        index=13,
        to=[
            {
                "collection": Collection("meeting"),
                "field": {
                    "name": "logo_$_id",
                    "structured_tag": "place",
                },
            }
        ],
    )
    used_as_font__in_meeting_id = fields.TemplateRelationField(
        replacement="place",
        index=13,
        to=[
            {
                "collection": Collection("meeting"),
                "field": {
                    "name": "font_$_id",
                    "structured_tag": "place",
                },
            }
        ],
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
        to=[
            {
                "collection": Collection("projection"),
                "field": {"name": "current_projector_id"},
            }
        ],
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    current_element_ids = fields.GenericRelationListField(
        to=[
            {
                "collection": Collection("motion"),
                "field": {"name": "current_projector_ids"},
            },
            {
                "collection": Collection("mediafile"),
                "field": {"name": "current_projector_ids"},
            },
            {
                "collection": Collection("list_of_speakers"),
                "field": {"name": "current_projector_ids"},
            },
            {
                "collection": Collection("motion_block"),
                "field": {"name": "current_projector_ids"},
            },
            {
                "collection": Collection("assignment"),
                "field": {"name": "current_projector_ids"},
            },
            {
                "collection": Collection("agenda_item"),
                "field": {"name": "current_projector_ids"},
            },
            {
                "collection": Collection("topic"),
                "field": {"name": "current_projector_ids"},
            },
            {
                "collection": Collection("poll"),
                "field": {"name": "current_projector_ids"},
            },
            {
                "collection": Collection("projector_message"),
                "field": {"name": "current_projector_ids"},
            },
            {
                "collection": Collection("projector_countdown"),
                "field": {"name": "current_projector_ids"},
            },
            {
                "collection": Collection("user"),
                "field": {
                    "name": "current_projector_$_ids",
                    "type": "structured-relation",
                    "replacement": "meeting_id",
                    "structured_relation": "['meeting_id']",
                },
            },
        ],
        equal_fields="meeting_id",
    )
    preview_projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {"name": "preview_projector_id"},
            }
        ],
        equal_fields="meeting_id",
    )
    history_projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {"name": "history_projector_id"},
            }
        ],
        equal_fields="meeting_id",
    )
    used_as_reference_projector_meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "reference_projector_id"},
            }
        ]
    )
    projectiondefault_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projectiondefault"),
                "field": {"name": "projector_id"},
            }
        ],
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "projector_ids"}}]
    )


class Projection(Model):
    collection = Collection("projection")
    verbose_name = "projection"

    id = fields.IntegerField()
    options = fields.JSONField()
    current_projector_id = fields.RelationField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {"name": "current_projection_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    preview_projector_id = fields.RelationField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {"name": "preview_projection_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    history_projector_id = fields.RelationField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {"name": "history_projection_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    element_id = fields.GenericRelationField(
        to=[
            {"collection": Collection("motion"), "field": {"name": "projection_ids"}},
            {
                "collection": Collection("mediafile"),
                "field": {"name": "projection_ids"},
            },
            {
                "collection": Collection("list_of_speakers"),
                "field": {"name": "projection_ids"},
            },
            {
                "collection": Collection("motion_block"),
                "field": {"name": "projection_ids"},
            },
            {
                "collection": Collection("assignment"),
                "field": {"name": "projection_ids"},
            },
            {
                "collection": Collection("agenda_item"),
                "field": {"name": "projection_ids"},
            },
            {"collection": Collection("topic"), "field": {"name": "projection_ids"}},
            {"collection": Collection("poll"), "field": {"name": "projection_ids"}},
            {
                "collection": Collection("projector_message"),
                "field": {"name": "projection_ids"},
            },
            {
                "collection": Collection("projector_countdown"),
                "field": {"name": "projection_ids"},
            },
            {
                "collection": Collection("user"),
                "field": {
                    "name": "projection_$_ids",
                    "type": "structured-relation",
                    "replacement": "meeting_id",
                    "structured_relation": "['meeting_id']",
                },
            },
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[{"collection": Collection("meeting"), "field": {"name": "projection_ids"}}],
        required=True,
    )


class Projectiondefault(Model):
    collection = Collection("projectiondefault")
    verbose_name = "projectiondefault"

    id = fields.IntegerField()
    name = fields.CharField()
    display_name = fields.CharField()
    projector_id = fields.RelationField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {"name": "projectiondefault_ids"},
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "projectiondefault_ids"},
            }
        ]
    )


class ProjectorMessage(Model):
    collection = Collection("projector_message")
    verbose_name = "projector message"

    id = fields.IntegerField()
    message = fields.HTMLStrictField()
    projection_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "projector_message_ids"},
            }
        ]
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
        to=[
            {
                "collection": Collection("projection"),
                "field": {
                    "name": "element_id",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    current_projector_ids = fields.RelationListField(
        to=[
            {
                "collection": Collection("projector"),
                "field": {
                    "name": "current_element_ids",
                    "generic_relation": True,
                },
            }
        ],
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to=[
            {
                "collection": Collection("meeting"),
                "field": {"name": "projector_countdown_ids"},
            }
        ]
    )
