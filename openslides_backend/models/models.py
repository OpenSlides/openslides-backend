# Code generated. DO NOT EDIT.

from . import fields
from .base import Model
from .mixins import AgendaItemModelMixin, MeetingModelMixin, PollModelMixin


class Organization(Model):
    collection = "organization"
    verbose_name = "organization"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField()
    description = fields.HTMLStrictField()
    legal_notice = fields.TextField()
    privacy_policy = fields.TextField()
    login_text = fields.TextField()
    reset_password_verbose_errors = fields.BooleanField()
    gender_ids = fields.RelationListField(to={"gender": "organization_id"})
    enable_electronic_voting = fields.BooleanField()
    enable_chat = fields.BooleanField()
    limit_of_meetings = fields.IntegerField(
        default=0,
        constraints={
            "description": "Maximum of active meetings for the whole organization. 0 means no limitation at all",
            "minimum": 0,
        },
    )
    limit_of_users = fields.IntegerField(
        default=0,
        constraints={
            "description": "Maximum of active users for the whole organization. 0 means no limitation at all",
            "minimum": 0,
        },
    )
    default_language = fields.CharField(
        default="en", constraints={"enum": ["en", "de", "it", "es", "ru", "cs", "fr"]}
    )
    require_duplicate_from = fields.BooleanField()
    enable_anonymous = fields.BooleanField()
    saml_enabled = fields.BooleanField()
    saml_login_button_text = fields.CharField(default="SAML login")
    saml_attr_mapping = fields.JSONField()
    saml_metadata_idp = fields.TextField()
    saml_metadata_sp = fields.TextField()
    saml_private_key = fields.TextField()
    committee_ids = fields.RelationListField(to={"committee": "organization_id"})
    active_meeting_ids = fields.RelationListField(
        to={"meeting": "is_active_in_organization_id"}
    )
    archived_meeting_ids = fields.RelationListField(
        to={"meeting": "is_archived_in_organization_id"}
    )
    template_meeting_ids = fields.RelationListField(
        to={"meeting": "template_for_organization_id"}
    )
    organization_tag_ids = fields.RelationListField(
        to={"organization_tag": "organization_id"}
    )
    theme_id = fields.RelationField(
        to={"theme": "theme_for_organization_id"}, required=True
    )
    theme_ids = fields.RelationListField(to={"theme": "organization_id"})
    mediafile_ids = fields.RelationListField(
        to={"mediafile": "owner_id"}, on_delete=fields.OnDelete.CASCADE
    )
    published_mediafile_ids = fields.RelationListField(
        to={"mediafile": "published_to_meetings_in_organization_id"}
    )
    user_ids = fields.RelationListField(to={"user": "organization_id"})
    users_email_sender = fields.CharField(default="OpenSlides")
    users_email_replyto = fields.CharField()
    users_email_subject = fields.CharField(default="OpenSlides access data")
    users_email_body = fields.TextField(
        default="Dear {name},\n\nthis is your personal OpenSlides login:\n\n{url}\nUsername: {username}\nPassword: {password}\n\n\nThis email was generated automatically."
    )
    url = fields.CharField(default="https://example.com")


class User(Model):
    collection = "user"
    verbose_name = "user"

    id = fields.IntegerField(required=True, constant=True)
    username = fields.CharField(required=True)
    member_number = fields.CharField()
    saml_id = fields.CharField(
        constraints={
            "minLength": 1,
            "description": "unique-key from IdP for SAML login",
        }
    )
    pronoun = fields.CharField(constraints={"maxLength": 32})
    title = fields.CharField()
    first_name = fields.CharField()
    last_name = fields.CharField()
    is_active = fields.BooleanField(default=True)
    is_physical_person = fields.BooleanField(default=True)
    password = fields.CharField()
    default_password = fields.CharField()
    can_change_own_password = fields.BooleanField(default=True)
    email = fields.CharField()
    default_vote_weight = fields.DecimalField(
        default="1.000000", constraints={"minimum": "0.000001"}
    )
    last_email_sent = fields.TimestampField()
    is_demo_user = fields.BooleanField()
    last_login = fields.TimestampField(read_only=True)
    external = fields.BooleanField()
    gender_id = fields.RelationField(to={"gender": "user_ids"})
    organization_management_level = fields.CharField(
        constraints={
            "description": "Hierarchical permission level for the whole organization.",
            "enum": ["superadmin", "can_manage_organization", "can_manage_users"],
        }
    )
    is_present_in_meeting_ids = fields.RelationListField(
        to={"meeting": "present_user_ids"}
    )
    committee_ids = fields.RelationListField(
        to={"committee": "user_ids"},
        read_only=True,
        constraints={"description": "Calculated field."},
    )
    committee_management_ids = fields.RelationListField(to={"committee": "manager_ids"})
    meeting_user_ids = fields.RelationListField(
        to={"meeting_user": "user_id"}, on_delete=fields.OnDelete.CASCADE
    )
    poll_voted_ids = fields.RelationListField(to={"poll": "voted_ids"})
    option_ids = fields.RelationListField(to={"option": "content_object_id"})
    vote_ids = fields.RelationListField(to={"vote": "user_id"})
    delegated_vote_ids = fields.RelationListField(to={"vote": "delegated_user_id"})
    poll_candidate_ids = fields.RelationListField(to={"poll_candidate": "user_id"})
    home_committee_id = fields.RelationField(to={"committee": "native_user_ids"})
    history_position_ids = fields.RelationListField(to={"history_position": "user_id"})
    history_entry_ids = fields.RelationListField(to={"history_entry": "model_id"})
    meeting_ids = fields.NumberArrayField(
        read_only=True,
        constraints={
            "description": "Calculated. All ids from meetings calculated via meeting_user and group_ids as integers."
        },
    )
    organization_id = fields.OrganizationField(
        to={"organization": "user_ids"}, required=True, constant=True
    )


class MeetingUser(Model):
    collection = "meeting_user"
    verbose_name = "meeting user"

    id = fields.IntegerField(required=True, constant=True)
    comment = fields.HTMLStrictField()
    number = fields.CharField()
    about_me = fields.HTMLStrictField()
    vote_weight = fields.DecimalField(constraints={"minimum": "0.000001"})
    locked_out = fields.BooleanField()
    user_id = fields.RelationField(
        to={"user": "meeting_user_ids"}, required=True, constant=True
    )
    meeting_id = fields.RelationField(
        to={"meeting": "meeting_user_ids"}, required=True, constant=True
    )
    personal_note_ids = fields.RelationListField(
        to={"personal_note": "meeting_user_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    speaker_ids = fields.RelationListField(
        to={"speaker": "meeting_user_id"}, equal_fields="meeting_id"
    )
    supported_motion_ids = fields.RelationListField(
        to={"motion": "supporter_meeting_user_ids"}, equal_fields="meeting_id"
    )
    motion_editor_ids = fields.RelationListField(
        to={"motion_editor": "meeting_user_id"}, equal_fields="meeting_id"
    )
    motion_working_group_speaker_ids = fields.RelationListField(
        to={"motion_working_group_speaker": "meeting_user_id"},
        equal_fields="meeting_id",
    )
    motion_submitter_ids = fields.RelationListField(
        to={"motion_submitter": "meeting_user_id"}, equal_fields="meeting_id"
    )
    assignment_candidate_ids = fields.RelationListField(
        to={"assignment_candidate": "meeting_user_id"}, equal_fields="meeting_id"
    )
    vote_delegated_to_id = fields.RelationField(
        to={"meeting_user": "vote_delegations_from_ids"}, equal_fields="meeting_id"
    )
    vote_delegations_from_ids = fields.RelationListField(
        to={"meeting_user": "vote_delegated_to_id"}, equal_fields="meeting_id"
    )
    chat_message_ids = fields.RelationListField(
        to={"chat_message": "meeting_user_id"}, equal_fields="meeting_id"
    )
    group_ids = fields.RelationListField(
        to={"group": "meeting_user_ids"}, required=True, equal_fields="meeting_id"
    )
    structure_level_ids = fields.RelationListField(
        to={"structure_level": "meeting_user_ids"}, equal_fields="meeting_id"
    )


class Gender(Model):
    collection = "gender"
    verbose_name = "gender"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True, constraints={"description": "unique"})
    organization_id = fields.OrganizationField(
        to={"organization": "gender_ids"}, required=True
    )
    user_ids = fields.RelationListField(to={"user": "gender_id"})


class OrganizationTag(Model):
    collection = "organization_tag"
    verbose_name = "organization tag"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    color = fields.ColorField(required=True)
    tagged_ids = fields.GenericRelationListField(
        to={"committee": "organization_tag_ids", "meeting": "organization_tag_ids"}
    )
    organization_id = fields.OrganizationField(
        to={"organization": "organization_tag_ids"}, required=True
    )


class Theme(Model):
    collection = "theme"
    verbose_name = "theme"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    accent_100 = fields.ColorField()
    accent_200 = fields.ColorField()
    accent_300 = fields.ColorField()
    accent_400 = fields.ColorField()
    accent_50 = fields.ColorField()
    accent_500 = fields.ColorField(default="#2196f3")
    accent_600 = fields.ColorField()
    accent_700 = fields.ColorField()
    accent_800 = fields.ColorField()
    accent_900 = fields.ColorField()
    accent_a100 = fields.ColorField()
    accent_a200 = fields.ColorField()
    accent_a400 = fields.ColorField()
    accent_a700 = fields.ColorField()
    primary_100 = fields.ColorField()
    primary_200 = fields.ColorField()
    primary_300 = fields.ColorField()
    primary_400 = fields.ColorField()
    primary_50 = fields.ColorField()
    primary_500 = fields.ColorField(default="#317796")
    primary_600 = fields.ColorField()
    primary_700 = fields.ColorField()
    primary_800 = fields.ColorField()
    primary_900 = fields.ColorField()
    primary_a100 = fields.ColorField()
    primary_a200 = fields.ColorField()
    primary_a400 = fields.ColorField()
    primary_a700 = fields.ColorField()
    warn_100 = fields.ColorField()
    warn_200 = fields.ColorField()
    warn_300 = fields.ColorField()
    warn_400 = fields.ColorField()
    warn_50 = fields.ColorField()
    warn_500 = fields.ColorField(default="#f06400")
    warn_600 = fields.ColorField()
    warn_700 = fields.ColorField()
    warn_800 = fields.ColorField()
    warn_900 = fields.ColorField()
    warn_a100 = fields.ColorField()
    warn_a200 = fields.ColorField()
    warn_a400 = fields.ColorField()
    warn_a700 = fields.ColorField()
    headbar = fields.ColorField()
    yes = fields.ColorField()
    no = fields.ColorField()
    abstain = fields.ColorField()
    theme_for_organization_id = fields.RelationField(to={"organization": "theme_id"})
    organization_id = fields.OrganizationField(
        to={"organization": "theme_ids"}, required=True, constant=True
    )


class Committee(Model):
    collection = "committee"
    verbose_name = "committee"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    description = fields.HTMLStrictField()
    external_id = fields.CharField(constraints={"description": "unique"})
    meeting_ids = fields.RelationListField(
        to={"meeting": "committee_id"}, on_delete=fields.OnDelete.PROTECT
    )
    default_meeting_id = fields.RelationField(
        to={"meeting": "default_meeting_for_committee_id"}
    )
    user_ids = fields.RelationListField(
        to={"user": "committee_ids"},
        read_only=True,
        constraints={"description": "Calculated field."},
    )
    manager_ids = fields.RelationListField(to={"user": "committee_management_ids"})
    parent_id = fields.RelationField(to={"committee": "child_ids"})
    child_ids = fields.RelationListField(to={"committee": "parent_id"})
    all_parent_ids = fields.RelationListField(to={"committee": "all_child_ids"})
    all_child_ids = fields.RelationListField(to={"committee": "all_parent_ids"})
    native_user_ids = fields.RelationListField(to={"user": "home_committee_id"})
    forward_to_committee_ids = fields.RelationListField(
        to={"committee": "receive_forwardings_from_committee_ids"}
    )
    receive_forwardings_from_committee_ids = fields.RelationListField(
        to={"committee": "forward_to_committee_ids"}
    )
    organization_tag_ids = fields.RelationListField(
        to={"organization_tag": "tagged_ids"}
    )
    organization_id = fields.OrganizationField(
        to={"organization": "committee_ids"}, required=True, constant=True
    )


class Meeting(Model, MeetingModelMixin):
    collection = "meeting"
    verbose_name = "meeting"

    id = fields.IntegerField(required=True, constant=True)
    external_id = fields.CharField(constraints={"description": "unique in committee"})
    welcome_title = fields.CharField(default="Welcome to OpenSlides")
    welcome_text = fields.HTMLPermissiveField(default="Space for your welcome text.")
    name = fields.CharField(
        required=True, default="OpenSlides", constraints={"maxLength": 100}
    )
    is_active_in_organization_id = fields.RelationField(
        to={"organization": "active_meeting_ids"},
        constraints={"description": "Backrelation and boolean flag at once"},
    )
    is_archived_in_organization_id = fields.RelationField(
        to={"organization": "archived_meeting_ids"},
        constraints={"description": "Backrelation and boolean flag at once"},
    )
    description = fields.CharField(constraints={"maxLength": 100})
    location = fields.CharField()
    start_time = fields.TimestampField()
    end_time = fields.TimestampField()
    locked_from_inside = fields.BooleanField()
    imported_at = fields.TimestampField()
    language = fields.CharField(
        constant=True,
        default="en",
        constraints={"enum": ["en", "de", "it", "es", "ru", "cs", "fr"]},
    )
    jitsi_domain = fields.CharField()
    jitsi_room_name = fields.CharField()
    jitsi_room_password = fields.CharField()
    template_for_organization_id = fields.RelationField(
        to={"organization": "template_meeting_ids"}
    )
    enable_anonymous = fields.BooleanField(default=False)
    custom_translations = fields.JSONField()
    conference_show = fields.BooleanField(default=False)
    conference_auto_connect = fields.BooleanField(default=False)
    conference_los_restriction = fields.BooleanField(default=True)
    conference_stream_url = fields.CharField()
    conference_stream_poster_url = fields.CharField()
    conference_open_microphone = fields.BooleanField(default=False)
    conference_open_video = fields.BooleanField(default=False)
    conference_auto_connect_next_speakers = fields.IntegerField(default=0)
    conference_enable_helpdesk = fields.BooleanField(default=False)
    applause_enable = fields.BooleanField(default=False)
    applause_type = fields.CharField(
        default="applause-type-bar",
        constraints={"enum": ["applause-type-bar", "applause-type-particles"]},
    )
    applause_show_level = fields.BooleanField(default=False)
    applause_min_amount = fields.IntegerField(default=1, constraints={"minimum": 0})
    applause_max_amount = fields.IntegerField(default=0, constraints={"minimum": 0})
    applause_timeout = fields.IntegerField(default=5, constraints={"minimum": 0})
    applause_particle_image_url = fields.CharField()
    projector_countdown_default_time = fields.IntegerField(required=True, default=60)
    projector_countdown_warning_time = fields.IntegerField(
        required=True, default=0, constraints={"minimum": 0}
    )
    export_csv_encoding = fields.CharField(
        default="utf-8", constraints={"enum": ["utf-8", "iso-8859-15"]}
    )
    export_csv_separator = fields.CharField(default=";")
    export_pdf_pagenumber_alignment = fields.CharField(
        default="center", constraints={"enum": ["left", "right", "center"]}
    )
    export_pdf_fontsize = fields.IntegerField(
        default=10, constraints={"enum": [10, 11, 12]}
    )
    export_pdf_line_height = fields.FloatField(
        default=1.25, constraints={"minimum": 1.0}
    )
    export_pdf_page_margin_left = fields.IntegerField(
        default=20, constraints={"minimum": 0}
    )
    export_pdf_page_margin_top = fields.IntegerField(
        default=25, constraints={"minimum": 0}
    )
    export_pdf_page_margin_right = fields.IntegerField(
        default=20, constraints={"minimum": 0}
    )
    export_pdf_page_margin_bottom = fields.IntegerField(
        default=20, constraints={"minimum": 0}
    )
    export_pdf_pagesize = fields.CharField(
        default="A4", constraints={"enum": ["A4", "A5"]}
    )
    agenda_show_subtitles = fields.BooleanField(default=False)
    agenda_enable_numbering = fields.BooleanField(default=True)
    agenda_number_prefix = fields.CharField(constraints={"maxLength": 20})
    agenda_numeral_system = fields.CharField(
        default="arabic", constraints={"enum": ["arabic", "roman"]}
    )
    agenda_item_creation = fields.CharField(
        default="default_no",
        constraints={"enum": ["always", "never", "default_yes", "default_no"]},
    )
    agenda_new_items_default_visibility = fields.CharField(
        default="internal", constraints={"enum": ["common", "internal", "hidden"]}
    )
    agenda_show_internal_items_on_projector = fields.BooleanField(default=False)
    agenda_show_topic_navigation_on_detail_view = fields.BooleanField(default=False)
    list_of_speakers_amount_last_on_projector = fields.IntegerField(
        default=0, constraints={"minimum": -1}
    )
    list_of_speakers_amount_next_on_projector = fields.IntegerField(
        default=-1, constraints={"minimum": -1}
    )
    list_of_speakers_couple_countdown = fields.BooleanField(default=True)
    list_of_speakers_show_amount_of_speakers_on_slide = fields.BooleanField(
        default=True
    )
    list_of_speakers_present_users_only = fields.BooleanField(default=False)
    list_of_speakers_show_first_contribution = fields.BooleanField(default=False)
    list_of_speakers_hide_contribution_count = fields.BooleanField(default=False)
    list_of_speakers_allow_multiple_speakers = fields.BooleanField(default=False)
    list_of_speakers_enable_point_of_order_speakers = fields.BooleanField(default=True)
    list_of_speakers_can_create_point_of_order_for_others = fields.BooleanField(
        default=False
    )
    list_of_speakers_enable_point_of_order_categories = fields.BooleanField(
        default=False
    )
    list_of_speakers_closing_disables_point_of_order = fields.BooleanField(
        default=False
    )
    list_of_speakers_enable_pro_contra_speech = fields.BooleanField(default=False)
    list_of_speakers_can_set_contribution_self = fields.BooleanField(default=False)
    list_of_speakers_speaker_note_for_everyone = fields.BooleanField(default=True)
    list_of_speakers_initially_closed = fields.BooleanField(default=False)
    list_of_speakers_default_structure_level_time = fields.IntegerField(
        constraints={
            "minimum": 0,
            "description": "0 disables structure level countdowns.",
        }
    )
    list_of_speakers_enable_interposed_question = fields.BooleanField()
    list_of_speakers_intervention_time = fields.IntegerField(
        constraints={"description": "0 disables intervention speakers."}
    )
    motions_default_workflow_id = fields.RelationField(
        to={"motion_workflow": "default_workflow_meeting_id"}, required=True
    )
    motions_default_amendment_workflow_id = fields.RelationField(
        to={"motion_workflow": "default_amendment_workflow_meeting_id"}, required=True
    )
    motions_preamble = fields.TextField(default="The assembly may decide:")
    motions_default_line_numbering = fields.CharField(
        default="outside", constraints={"enum": ["outside", "inline", "none"]}
    )
    motions_line_length = fields.IntegerField(default=85, constraints={"minimum": 40})
    motions_reason_required = fields.BooleanField(default=False)
    motions_origin_motion_toggle_default = fields.BooleanField(default=False)
    motions_enable_origin_motion_display = fields.BooleanField(default=False)
    motions_enable_text_on_projector = fields.BooleanField(default=True)
    motions_enable_reason_on_projector = fields.BooleanField(default=False)
    motions_enable_sidebox_on_projector = fields.BooleanField(default=False)
    motions_enable_recommendation_on_projector = fields.BooleanField(default=True)
    motions_hide_metadata_background = fields.BooleanField(default=False)
    motions_show_referring_motions = fields.BooleanField(default=True)
    motions_show_sequential_number = fields.BooleanField(default=True)
    motions_create_enable_additional_submitter_text = fields.BooleanField()
    motions_recommendations_by = fields.CharField()
    motions_block_slide_columns = fields.IntegerField(constraints={"minimum": 1})
    motions_recommendation_text_mode = fields.CharField(
        default="diff", constraints={"enum": ["original", "changed", "diff", "agreed"]}
    )
    motions_default_sorting = fields.CharField(
        default="number", constraints={"enum": ["number", "weight"]}
    )
    motions_number_type = fields.CharField(
        default="per_category",
        constraints={"enum": ["per_category", "serially_numbered", "manually"]},
    )
    motions_number_min_digits = fields.IntegerField(default=2)
    motions_number_with_blank = fields.BooleanField(default=False)
    motions_amendments_enabled = fields.BooleanField(default=True)
    motions_amendments_in_main_list = fields.BooleanField(default=True)
    motions_amendments_of_amendments = fields.BooleanField(default=False)
    motions_amendments_prefix = fields.CharField(default="-Ä")
    motions_amendments_text_mode = fields.CharField(
        default="paragraph",
        constraints={"enum": ["freestyle", "fulltext", "paragraph"]},
    )
    motions_amendments_multiple_paragraphs = fields.BooleanField(default=True)
    motions_supporters_min_amount = fields.IntegerField(
        default=0, constraints={"minimum": 0}
    )
    motions_enable_editor = fields.BooleanField()
    motions_enable_working_group_speaker = fields.BooleanField()
    motions_export_title = fields.CharField(default="Motions")
    motions_export_preamble = fields.TextField()
    motions_export_submitter_recommendation = fields.BooleanField(default=True)
    motions_export_follow_recommendation = fields.BooleanField(default=False)
    motions_enable_restricted_editor_for_manager = fields.BooleanField()
    motions_enable_restricted_editor_for_non_manager = fields.BooleanField()
    motion_poll_ballot_paper_selection = fields.CharField(
        default="CUSTOM_NUMBER",
        constraints={
            "enum": [
                "NUMBER_OF_DELEGATES",
                "NUMBER_OF_ALL_PARTICIPANTS",
                "CUSTOM_NUMBER",
            ]
        },
    )
    motion_poll_ballot_paper_number = fields.IntegerField(default=8)
    motion_poll_default_type = fields.CharField(default="pseudoanonymous")
    motion_poll_default_method = fields.CharField(default="YNA")
    motion_poll_default_onehundred_percent_base = fields.CharField(
        default="YNA",
        constraints={
            "enum": [
                "Y",
                "YN",
                "YNA",
                "N",
                "valid",
                "cast",
                "entitled",
                "entitled_present",
                "disabled",
            ]
        },
    )
    motion_poll_default_group_ids = fields.RelationListField(
        to={"group": "used_as_motion_poll_default_id"}
    )
    motion_poll_default_backend = fields.CharField(
        default="fast", constraints={"enum": ["long", "fast"]}
    )
    motion_poll_projection_name_order_first = fields.CharField(
        required=True,
        default="last_name",
        constraints={"enum": ["first_name", "last_name"]},
    )
    motion_poll_projection_max_columns = fields.IntegerField(required=True, default=6)
    poll_candidate_list_ids = fields.RelationListField(
        to={"poll_candidate_list": "meeting_id"}
    )
    poll_candidate_ids = fields.RelationListField(to={"poll_candidate": "meeting_id"})
    meeting_user_ids = fields.RelationListField(
        to={"meeting_user": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    users_enable_presence_view = fields.BooleanField(default=False)
    users_enable_vote_weight = fields.BooleanField(default=False)
    users_allow_self_set_present = fields.BooleanField(default=True)
    users_pdf_welcometitle = fields.CharField(default="Welcome to OpenSlides")
    users_pdf_welcometext = fields.TextField(
        default="[Place for your welcome and help text.]"
    )
    users_pdf_wlan_ssid = fields.CharField()
    users_pdf_wlan_password = fields.CharField()
    users_pdf_wlan_encryption = fields.CharField(
        default="WPA", constraints={"enum": ["", "WEP", "WPA", "nopass"]}
    )
    users_email_sender = fields.CharField(default="OpenSlides")
    users_email_replyto = fields.CharField()
    users_email_subject = fields.CharField(default="OpenSlides access data")
    users_email_body = fields.TextField(
        default="Dear {name},\n\nthis is your personal OpenSlides login:\n\n{url}\nUsername: {username}\nPassword: {password}\n\n\nThis email was generated automatically."
    )
    users_enable_vote_delegations = fields.BooleanField()
    users_forbid_delegator_in_list_of_speakers = fields.BooleanField()
    users_forbid_delegator_as_submitter = fields.BooleanField()
    users_forbid_delegator_as_supporter = fields.BooleanField()
    users_forbid_delegator_to_vote = fields.BooleanField()
    assignments_export_title = fields.CharField(default="Elections")
    assignments_export_preamble = fields.TextField()
    assignment_poll_ballot_paper_selection = fields.CharField(
        default="CUSTOM_NUMBER",
        constraints={
            "enum": [
                "NUMBER_OF_DELEGATES",
                "NUMBER_OF_ALL_PARTICIPANTS",
                "CUSTOM_NUMBER",
            ]
        },
    )
    assignment_poll_ballot_paper_number = fields.IntegerField(default=8)
    assignment_poll_add_candidates_to_list_of_speakers = fields.BooleanField(
        default=False
    )
    assignment_poll_enable_max_votes_per_option = fields.BooleanField(default=False)
    assignment_poll_sort_poll_result_by_votes = fields.BooleanField(default=True)
    assignment_poll_default_type = fields.CharField(default="pseudoanonymous")
    assignment_poll_default_method = fields.CharField(default="Y")
    assignment_poll_default_onehundred_percent_base = fields.CharField(
        default="valid",
        constraints={
            "enum": [
                "Y",
                "YN",
                "YNA",
                "N",
                "valid",
                "cast",
                "entitled",
                "entitled_present",
                "disabled",
            ]
        },
    )
    assignment_poll_default_group_ids = fields.RelationListField(
        to={"group": "used_as_assignment_poll_default_id"}
    )
    assignment_poll_default_backend = fields.CharField(
        default="fast", constraints={"enum": ["long", "fast"]}
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
    poll_default_type = fields.CharField(default="analog")
    poll_default_method = fields.CharField()
    poll_default_onehundred_percent_base = fields.CharField(
        default="YNA",
        constraints={
            "enum": [
                "Y",
                "YN",
                "YNA",
                "N",
                "valid",
                "cast",
                "entitled",
                "entitled_present",
                "disabled",
            ]
        },
    )
    poll_default_group_ids = fields.RelationListField(
        to={"group": "used_as_poll_default_id"}
    )
    poll_default_backend = fields.CharField(
        default="fast", constraints={"enum": ["long", "fast"]}
    )
    poll_default_live_voting_enabled = fields.BooleanField(
        default=False,
        constraints={
            "description": "Defines default 'poll.live_voting_enabled' option suggested to user. Is not used in the validations."
        },
    )
    poll_couple_countdown = fields.BooleanField(default=True)
    topic_poll_default_group_ids = fields.RelationListField(
        to={"group": "used_as_topic_poll_default_id"}
    )
    projector_ids = fields.RelationListField(
        to={"projector": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    all_projection_ids = fields.RelationListField(
        to={"projection": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    projector_message_ids = fields.RelationListField(
        to={"projector_message": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    projector_countdown_ids = fields.RelationListField(
        to={"projector_countdown": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    tag_ids = fields.RelationListField(
        to={"tag": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    agenda_item_ids = fields.RelationListField(
        to={"agenda_item": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    list_of_speakers_ids = fields.RelationListField(
        to={"list_of_speakers": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    structure_level_list_of_speakers_ids = fields.RelationListField(
        to={"structure_level_list_of_speakers": "meeting_id"},
        on_delete=fields.OnDelete.CASCADE,
    )
    point_of_order_category_ids = fields.RelationListField(
        to={"point_of_order_category": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    speaker_ids = fields.RelationListField(
        to={"speaker": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    topic_ids = fields.RelationListField(
        to={"topic": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    group_ids = fields.RelationListField(
        to={"group": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    meeting_mediafile_ids = fields.RelationListField(
        to={"meeting_mediafile": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    mediafile_ids = fields.RelationListField(
        to={"mediafile": "owner_id"}, on_delete=fields.OnDelete.CASCADE
    )
    motion_ids = fields.RelationListField(
        to={"motion": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    forwarded_motion_ids = fields.RelationListField(
        to={"motion": "origin_meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    motion_comment_section_ids = fields.RelationListField(
        to={"motion_comment_section": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    motion_category_ids = fields.RelationListField(
        to={"motion_category": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    motion_block_ids = fields.RelationListField(
        to={"motion_block": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    motion_workflow_ids = fields.RelationListField(
        to={"motion_workflow": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    motion_comment_ids = fields.RelationListField(
        to={"motion_comment": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    motion_submitter_ids = fields.RelationListField(
        to={"motion_submitter": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    motion_editor_ids = fields.RelationListField(
        to={"motion_editor": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    motion_working_group_speaker_ids = fields.RelationListField(
        to={"motion_working_group_speaker": "meeting_id"},
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_change_recommendation_ids = fields.RelationListField(
        to={"motion_change_recommendation": "meeting_id"},
        on_delete=fields.OnDelete.CASCADE,
    )
    motion_state_ids = fields.RelationListField(
        to={"motion_state": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    poll_ids = fields.RelationListField(
        to={"poll": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    option_ids = fields.RelationListField(
        to={"option": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    vote_ids = fields.RelationListField(
        to={"vote": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    assignment_ids = fields.RelationListField(
        to={"assignment": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    assignment_candidate_ids = fields.RelationListField(
        to={"assignment_candidate": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    personal_note_ids = fields.RelationListField(
        to={"personal_note": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    chat_group_ids = fields.RelationListField(
        to={"chat_group": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    chat_message_ids = fields.RelationListField(
        to={"chat_message": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    structure_level_ids = fields.RelationListField(
        to={"structure_level": "meeting_id"}, on_delete=fields.OnDelete.CASCADE
    )
    logo_projector_main_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_logo_projector_main_in_meeting_id"}
    )
    logo_projector_header_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_logo_projector_header_in_meeting_id"}
    )
    logo_web_header_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_logo_web_header_in_meeting_id"}
    )
    logo_pdf_header_l_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_logo_pdf_header_l_in_meeting_id"}
    )
    logo_pdf_header_r_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_logo_pdf_header_r_in_meeting_id"}
    )
    logo_pdf_footer_l_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_logo_pdf_footer_l_in_meeting_id"}
    )
    logo_pdf_footer_r_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_logo_pdf_footer_r_in_meeting_id"}
    )
    logo_pdf_ballot_paper_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_logo_pdf_ballot_paper_in_meeting_id"}
    )
    font_regular_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_font_regular_in_meeting_id"}
    )
    font_italic_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_font_italic_in_meeting_id"}
    )
    font_bold_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_font_bold_in_meeting_id"}
    )
    font_bold_italic_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_font_bold_italic_in_meeting_id"}
    )
    font_monospace_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_font_monospace_in_meeting_id"}
    )
    font_chyron_speaker_name_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_font_chyron_speaker_name_in_meeting_id"}
    )
    font_projector_h1_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_font_projector_h1_in_meeting_id"}
    )
    font_projector_h2_id = fields.RelationField(
        to={"meeting_mediafile": "used_as_font_projector_h2_in_meeting_id"}
    )
    committee_id = fields.RelationField(
        to={"committee": "meeting_ids"}, required=True, constant=True
    )
    default_meeting_for_committee_id = fields.RelationField(
        to={"committee": "default_meeting_id"}
    )
    organization_tag_ids = fields.RelationListField(
        to={"organization_tag": "tagged_ids"}
    )
    present_user_ids = fields.RelationListField(
        to={"user": "is_present_in_meeting_ids"}
    )
    user_ids = fields.NumberArrayField(
        read_only=True,
        constraints={
            "description": "Calculated. All user ids from all users assigned to groups of this meeting."
        },
    )
    reference_projector_id = fields.RelationField(
        to={"projector": "used_as_reference_projector_meeting_id"}, required=True
    )
    list_of_speakers_countdown_id = fields.RelationField(
        to={"projector_countdown": "used_as_list_of_speakers_countdown_meeting_id"}
    )
    poll_countdown_id = fields.RelationField(
        to={"projector_countdown": "used_as_poll_countdown_meeting_id"}
    )
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"}, on_delete=fields.OnDelete.CASCADE
    )
    default_projector_agenda_item_list_ids = fields.RelationListField(
        to={
            "projector": "used_as_default_projector_for_agenda_item_list_in_meeting_id"
        },
        required=True,
    )
    default_projector_topic_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_topic_in_meeting_id"},
        required=True,
    )
    default_projector_list_of_speakers_ids = fields.RelationListField(
        to={
            "projector": "used_as_default_projector_for_list_of_speakers_in_meeting_id"
        },
        required=True,
    )
    default_projector_current_los_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_current_los_in_meeting_id"},
        required=True,
    )
    default_projector_motion_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_motion_in_meeting_id"},
        required=True,
    )
    default_projector_amendment_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_amendment_in_meeting_id"},
        required=True,
    )
    default_projector_motion_block_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_motion_block_in_meeting_id"},
        required=True,
    )
    default_projector_assignment_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_assignment_in_meeting_id"},
        required=True,
    )
    default_projector_mediafile_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_mediafile_in_meeting_id"},
        required=True,
    )
    default_projector_message_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_message_in_meeting_id"},
        required=True,
    )
    default_projector_countdown_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_countdown_in_meeting_id"},
        required=True,
    )
    default_projector_assignment_poll_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_assignment_poll_in_meeting_id"},
        required=True,
    )
    default_projector_motion_poll_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_motion_poll_in_meeting_id"},
        required=True,
    )
    default_projector_poll_ids = fields.RelationListField(
        to={"projector": "used_as_default_projector_for_poll_in_meeting_id"},
        required=True,
    )
    default_group_id = fields.RelationField(
        to={"group": "default_group_for_meeting_id"}, required=True
    )
    admin_group_id = fields.RelationField(to={"group": "admin_group_for_meeting_id"})
    anonymous_group_id = fields.RelationField(
        to={"group": "anonymous_group_for_meeting_id"}
    )
    relevant_history_entry_ids = fields.RelationListField(
        to={"history_entry": "meeting_id"}
    )


class StructureLevel(Model):
    collection = "structure_level"
    verbose_name = "structure level"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    color = fields.ColorField()
    default_time = fields.IntegerField(constraints={"minimum": 0})
    meeting_user_ids = fields.RelationListField(
        to={"meeting_user": "structure_level_ids"}, equal_fields="meeting_id"
    )
    structure_level_list_of_speakers_ids = fields.RelationListField(
        to={"structure_level_list_of_speakers": "structure_level_id"},
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "structure_level_ids"}, required=True
    )


class Group(Model):
    collection = "group"
    verbose_name = "group"

    id = fields.IntegerField(required=True, constant=True)
    external_id = fields.CharField(constraints={"description": "unique in meeting"})
    name = fields.CharField(required=True)
    permissions = fields.CharArrayField(
        in_array_constraints={
            "enum": [
                "agenda_item.can_manage",
                "agenda_item.can_see",
                "agenda_item.can_see_internal",
                "assignment.can_manage",
                "assignment.can_manage_polls",
                "assignment.can_nominate_other",
                "assignment.can_nominate_self",
                "assignment.can_see",
                "chat.can_manage",
                "list_of_speakers.can_be_speaker",
                "list_of_speakers.can_manage",
                "list_of_speakers.can_see",
                "list_of_speakers.can_manage_moderator_notes",
                "list_of_speakers.can_see_moderator_notes",
                "mediafile.can_manage",
                "mediafile.can_see",
                "meeting.can_manage_logos_and_fonts",
                "meeting.can_manage_settings",
                "meeting.can_see_autopilot",
                "meeting.can_see_frontpage",
                "meeting.can_see_history",
                "meeting.can_see_livestream",
                "motion.can_create",
                "motion.can_create_amendments",
                "motion.can_forward",
                "motion.can_manage",
                "motion.can_manage_metadata",
                "motion.can_manage_polls",
                "motion.can_see",
                "motion.can_see_internal",
                "motion.can_see_origin",
                "motion.can_support",
                "poll.can_manage",
                "poll.can_see_progress",
                "projector.can_manage",
                "projector.can_see",
                "tag.can_manage",
                "user.can_manage",
                "user.can_manage_presence",
                "user.can_see_sensitive_data",
                "user.can_see",
                "user.can_update",
                "user.can_edit_own_delegation",
            ]
        }
    )
    weight = fields.IntegerField()
    meeting_user_ids = fields.RelationListField(
        to={"meeting_user": "group_ids"}, equal_fields="meeting_id"
    )
    default_group_for_meeting_id = fields.RelationField(
        to={"meeting": "default_group_id"}, on_delete=fields.OnDelete.PROTECT
    )
    admin_group_for_meeting_id = fields.RelationField(
        to={"meeting": "admin_group_id"}, on_delete=fields.OnDelete.PROTECT
    )
    anonymous_group_for_meeting_id = fields.RelationField(
        to={"meeting": "anonymous_group_id"}, on_delete=fields.OnDelete.PROTECT
    )
    meeting_mediafile_access_group_ids = fields.RelationListField(
        to={"meeting_mediafile": "access_group_ids"}, equal_fields="meeting_id"
    )
    meeting_mediafile_inherited_access_group_ids = fields.RelationListField(
        to={"meeting_mediafile": "inherited_access_group_ids"},
        read_only=True,
        constraints={"description": "Calculated field."},
    )
    read_comment_section_ids = fields.RelationListField(
        to={"motion_comment_section": "read_group_ids"}, equal_fields="meeting_id"
    )
    write_comment_section_ids = fields.RelationListField(
        to={"motion_comment_section": "write_group_ids"}, equal_fields="meeting_id"
    )
    read_chat_group_ids = fields.RelationListField(
        to={"chat_group": "read_group_ids"}, equal_fields="meeting_id"
    )
    write_chat_group_ids = fields.RelationListField(
        to={"chat_group": "write_group_ids"}, equal_fields="meeting_id"
    )
    poll_ids = fields.RelationListField(
        to={"poll": "entitled_group_ids"}, equal_fields="meeting_id"
    )
    used_as_motion_poll_default_id = fields.RelationField(
        to={"meeting": "motion_poll_default_group_ids"}
    )
    used_as_assignment_poll_default_id = fields.RelationField(
        to={"meeting": "assignment_poll_default_group_ids"}
    )
    used_as_topic_poll_default_id = fields.RelationField(
        to={"meeting": "topic_poll_default_group_ids"}
    )
    used_as_poll_default_id = fields.RelationField(
        to={"meeting": "poll_default_group_ids"}
    )
    meeting_id = fields.RelationField(
        to={"meeting": "group_ids"}, required=True, constant=True
    )


class PersonalNote(Model):
    collection = "personal_note"
    verbose_name = "personal note"

    id = fields.IntegerField(required=True, constant=True)
    note = fields.HTMLStrictField()
    star = fields.BooleanField()
    meeting_user_id = fields.RelationField(
        to={"meeting_user": "personal_note_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    content_object_id = fields.GenericRelationField(
        to={"motion": "personal_note_ids"}, constant=True, equal_fields="meeting_id"
    )
    meeting_id = fields.RelationField(
        to={"meeting": "personal_note_ids"}, required=True, constant=True
    )


class Tag(Model):
    collection = "tag"
    verbose_name = "tag"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    tagged_ids = fields.GenericRelationListField(
        to={"agenda_item": "tag_ids", "assignment": "tag_ids", "motion": "tag_ids"},
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "tag_ids"}, required=True, constant=True
    )


class AgendaItem(Model, AgendaItemModelMixin):
    collection = "agenda_item"
    verbose_name = "agenda item"

    id = fields.IntegerField(required=True, constant=True)
    item_number = fields.CharField()
    comment = fields.CharField()
    closed = fields.BooleanField(default=False)
    type = fields.CharField(
        default="common", constraints={"enum": ["common", "internal", "hidden"]}
    )
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
    weight = fields.IntegerField()
    content_object_id = fields.GenericRelationField(
        to={
            "motion": "agenda_item_id",
            "motion_block": "agenda_item_id",
            "assignment": "agenda_item_id",
            "topic": "agenda_item_id",
        },
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    parent_id = fields.RelationField(
        to={"agenda_item": "child_ids"}, equal_fields="meeting_id"
    )
    child_ids = fields.RelationListField(
        to={"agenda_item": "parent_id"}, equal_fields="meeting_id"
    )
    tag_ids = fields.RelationListField(
        to={"tag": "tagged_ids"}, equal_fields="meeting_id"
    )
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "agenda_item_ids"}, required=True, constant=True
    )


class ListOfSpeakers(Model):
    collection = "list_of_speakers"
    verbose_name = "list of speakers"

    id = fields.IntegerField(required=True, constant=True)
    closed = fields.BooleanField(default=False)
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only."
        },
    )
    moderator_notes = fields.HTMLStrictField()
    content_object_id = fields.GenericRelationField(
        to={
            "motion": "list_of_speakers_id",
            "motion_block": "list_of_speakers_id",
            "assignment": "list_of_speakers_id",
            "topic": "list_of_speakers_id",
            "meeting_mediafile": "list_of_speakers_id",
        },
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    speaker_ids = fields.RelationListField(
        to={"speaker": "list_of_speakers_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    structure_level_list_of_speakers_ids = fields.RelationListField(
        to={"structure_level_list_of_speakers": "list_of_speakers_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "list_of_speakers_ids"}, required=True, constant=True
    )


class StructureLevelListOfSpeakers(Model):
    collection = "structure_level_list_of_speakers"
    verbose_name = "structure level list of speakers"

    id = fields.IntegerField(required=True, constant=True)
    structure_level_id = fields.RelationField(
        to={"structure_level": "structure_level_list_of_speakers_ids"},
        required=True,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to={"list_of_speakers": "structure_level_list_of_speakers_ids"},
        required=True,
        equal_fields="meeting_id",
    )
    speaker_ids = fields.RelationListField(
        to={"speaker": "structure_level_list_of_speakers_id"}, equal_fields="meeting_id"
    )
    initial_time = fields.IntegerField(
        required=True,
        constraints={
            "minimum": 1,
            "description": "The initial time of this structure_level for this LoS",
        },
    )
    additional_time = fields.FloatField(
        constraints={
            "description": "The summed added time of this structure_level for this LoS"
        }
    )
    remaining_time = fields.FloatField(
        required=True,
        constraints={
            "description": "The currently remaining time of this structure_level for this LoS"
        },
    )
    current_start_time = fields.TimestampField(
        constraints={
            "description": "The current start time of a speaker for this structure_level. Is only set if a currently speaking speaker exists"
        }
    )
    meeting_id = fields.RelationField(
        to={"meeting": "structure_level_list_of_speakers_ids"}, required=True
    )


class PointOfOrderCategory(Model):
    collection = "point_of_order_category"
    verbose_name = "point of order category"

    id = fields.IntegerField(required=True, constant=True)
    text = fields.CharField(required=True)
    rank = fields.IntegerField(required=True)
    meeting_id = fields.RelationField(
        to={"meeting": "point_of_order_category_ids"}, required=True, constant=True
    )
    speaker_ids = fields.RelationListField(
        to={"speaker": "point_of_order_category_id"}, equal_fields="meeting_id"
    )


class Speaker(Model):
    collection = "speaker"
    verbose_name = "speaker"

    id = fields.IntegerField(required=True, constant=True)
    begin_time = fields.TimestampField()
    end_time = fields.TimestampField()
    pause_time = fields.TimestampField(read_only=True)
    unpause_time = fields.TimestampField()
    total_pause = fields.IntegerField()
    weight = fields.IntegerField(default=10000)
    speech_state = fields.CharField(
        constraints={
            "enum": [
                "contribution",
                "pro",
                "contra",
                "intervention",
                "interposed_question",
            ]
        }
    )
    answer = fields.BooleanField()
    note = fields.CharField(constraints={"maxLength": 250})
    point_of_order = fields.BooleanField(constant=True)
    list_of_speakers_id = fields.RelationField(
        to={"list_of_speakers": "speaker_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    structure_level_list_of_speakers_id = fields.RelationField(
        to={"structure_level_list_of_speakers": "speaker_ids"},
        equal_fields="meeting_id",
    )
    meeting_user_id = fields.RelationField(
        to={"meeting_user": "speaker_ids"}, equal_fields="meeting_id"
    )
    point_of_order_category_id = fields.RelationField(
        to={"point_of_order_category": "speaker_ids"}, equal_fields="meeting_id"
    )
    meeting_id = fields.RelationField(
        to={"meeting": "speaker_ids"}, required=True, constant=True
    )


class Topic(Model):
    collection = "topic"
    verbose_name = "topic"

    id = fields.IntegerField(required=True, constant=True)
    title = fields.CharField(required=True)
    text = fields.HTMLPermissiveField()
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only."
        },
    )
    attachment_meeting_mediafile_ids = fields.RelationListField(
        to={"meeting_mediafile": "attachment_ids"}, equal_fields="meeting_id"
    )
    agenda_item_id = fields.RelationField(
        to={"agenda_item": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to={"list_of_speakers": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    poll_ids = fields.RelationListField(
        to={"poll": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "topic_ids"}, required=True, constant=True
    )


class Motion(Model):
    collection = "motion"
    verbose_name = "motion"

    id = fields.IntegerField(required=True, constant=True)
    number = fields.CharField()
    number_value = fields.IntegerField(
        read_only=True,
        constraints={
            "description": "The number value of this motion. This number is auto-generated and read-only."
        },
    )
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only."
        },
    )
    title = fields.CharField(required=True)
    text = fields.HTMLStrictField()
    text_hash = fields.CharField()
    amendment_paragraphs = fields.JSONField()
    modified_final_version = fields.HTMLStrictField()
    reason = fields.HTMLStrictField()
    category_weight = fields.IntegerField(default=10000)
    state_extension = fields.CharField()
    recommendation_extension = fields.CharField()
    sort_weight = fields.IntegerField(default=10000)
    created = fields.TimestampField()
    last_modified = fields.TimestampField(read_only=True)
    workflow_timestamp = fields.TimestampField()
    start_line_number = fields.IntegerField(default=1, constraints={"minimum": 1})
    forwarded = fields.TimestampField(read_only=True)
    additional_submitter = fields.CharField()
    marked_forwarded = fields.BooleanField(
        constraints={
            "description": "Forwarded amendments can be marked as such. This is just optional, however. Forwarded amendments can also have this field set to false."
        }
    )
    lead_motion_id = fields.RelationField(
        to={"motion": "amendment_ids"}, equal_fields="meeting_id"
    )
    amendment_ids = fields.RelationListField(
        to={"motion": "lead_motion_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    sort_parent_id = fields.RelationField(
        to={"motion": "sort_child_ids"}, equal_fields="meeting_id"
    )
    sort_child_ids = fields.RelationListField(
        to={"motion": "sort_parent_id"}, equal_fields="meeting_id"
    )
    origin_id = fields.RelationField(to={"motion": "derived_motion_ids"})
    origin_meeting_id = fields.RelationField(to={"meeting": "forwarded_motion_ids"})
    derived_motion_ids = fields.RelationListField(to={"motion": "origin_id"})
    all_origin_ids = fields.RelationListField(to={"motion": "all_derived_motion_ids"})
    all_derived_motion_ids = fields.RelationListField(to={"motion": "all_origin_ids"})
    identical_motion_ids = fields.RelationListField(
        to={"motion": "identical_motion_ids"}, equal_fields="meeting_id"
    )
    state_id = fields.RelationField(
        to={"motion_state": "motion_ids"}, required=True, equal_fields="meeting_id"
    )
    recommendation_id = fields.RelationField(
        to={"motion_state": "motion_recommendation_ids"}, equal_fields="meeting_id"
    )
    state_extension_reference_ids = fields.GenericRelationListField(
        to={"motion": "referenced_in_motion_state_extension_ids"},
        equal_fields="meeting_id",
    )
    referenced_in_motion_state_extension_ids = fields.RelationListField(
        to={"motion": "state_extension_reference_ids"}, equal_fields="meeting_id"
    )
    recommendation_extension_reference_ids = fields.GenericRelationListField(
        to={"motion": "referenced_in_motion_recommendation_extension_ids"},
        equal_fields="meeting_id",
    )
    referenced_in_motion_recommendation_extension_ids = fields.RelationListField(
        to={"motion": "recommendation_extension_reference_ids"},
        equal_fields="meeting_id",
    )
    category_id = fields.RelationField(
        to={"motion_category": "motion_ids"}, equal_fields="meeting_id"
    )
    block_id = fields.RelationField(
        to={"motion_block": "motion_ids"}, equal_fields="meeting_id"
    )
    submitter_ids = fields.RelationListField(
        to={"motion_submitter": "motion_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    supporter_meeting_user_ids = fields.RelationListField(
        to={"meeting_user": "supported_motion_ids"}, equal_fields="meeting_id"
    )
    editor_ids = fields.RelationListField(
        to={"motion_editor": "motion_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    working_group_speaker_ids = fields.RelationListField(
        to={"motion_working_group_speaker": "motion_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    poll_ids = fields.RelationListField(
        to={"poll": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    option_ids = fields.RelationListField(
        to={"option": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    change_recommendation_ids = fields.RelationListField(
        to={"motion_change_recommendation": "motion_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    comment_ids = fields.RelationListField(
        to={"motion_comment": "motion_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    agenda_item_id = fields.RelationField(
        to={"agenda_item": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to={"list_of_speakers": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    tag_ids = fields.RelationListField(
        to={"tag": "tagged_ids"}, equal_fields="meeting_id"
    )
    attachment_meeting_mediafile_ids = fields.RelationListField(
        to={"meeting_mediafile": "attachment_ids"}, equal_fields="meeting_id"
    )
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    personal_note_ids = fields.RelationListField(
        to={"personal_note": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_ids"}, required=True, constant=True
    )
    history_entry_ids = fields.RelationListField(to={"history_entry": "model_id"})


class MotionSubmitter(Model):
    collection = "motion_submitter"
    verbose_name = "motion submitter"

    id = fields.IntegerField(required=True, constant=True)
    weight = fields.IntegerField()
    meeting_user_id = fields.RelationField(to={"meeting_user": "motion_submitter_ids"})
    motion_id = fields.RelationField(
        to={"motion": "submitter_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_submitter_ids"}, required=True, constant=True
    )


class MotionEditor(Model):
    collection = "motion_editor"
    verbose_name = "motion editor"

    id = fields.IntegerField(required=True, constant=True)
    weight = fields.IntegerField()
    meeting_user_id = fields.RelationField(to={"meeting_user": "motion_editor_ids"})
    motion_id = fields.RelationField(
        to={"motion": "editor_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_editor_ids"}, required=True, constant=True
    )


class MotionWorkingGroupSpeaker(Model):
    collection = "motion_working_group_speaker"
    verbose_name = "motion working group speaker"

    id = fields.IntegerField(required=True, constant=True)
    weight = fields.IntegerField()
    meeting_user_id = fields.RelationField(
        to={"meeting_user": "motion_working_group_speaker_ids"}
    )
    motion_id = fields.RelationField(
        to={"motion": "working_group_speaker_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_working_group_speaker_ids"}, required=True, constant=True
    )


class MotionComment(Model):
    collection = "motion_comment"
    verbose_name = "motion comment"

    id = fields.IntegerField(required=True, constant=True)
    comment = fields.HTMLStrictField()
    motion_id = fields.RelationField(
        to={"motion": "comment_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    section_id = fields.RelationField(
        to={"motion_comment_section": "comment_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_comment_ids"}, required=True, constant=True
    )


class MotionCommentSection(Model):
    collection = "motion_comment_section"
    verbose_name = "motion comment section"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    weight = fields.IntegerField(default=10000)
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only."
        },
    )
    submitter_can_write = fields.BooleanField()
    comment_ids = fields.RelationListField(
        to={"motion_comment": "section_id"},
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    read_group_ids = fields.RelationListField(
        to={"group": "read_comment_section_ids"}, equal_fields="meeting_id"
    )
    write_group_ids = fields.RelationListField(
        to={"group": "write_comment_section_ids"}, equal_fields="meeting_id"
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_comment_section_ids"}, required=True, constant=True
    )


class MotionCategory(Model):
    collection = "motion_category"
    verbose_name = "motion category"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    prefix = fields.CharField()
    weight = fields.IntegerField(default=10000)
    level = fields.IntegerField(
        read_only=True, constraints={"description": "Calculated field."}
    )
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only."
        },
    )
    parent_id = fields.RelationField(
        to={"motion_category": "child_ids"}, equal_fields="meeting_id"
    )
    child_ids = fields.RelationListField(
        to={"motion_category": "parent_id"}, equal_fields="meeting_id"
    )
    motion_ids = fields.RelationListField(
        to={"motion": "category_id"}, equal_fields="meeting_id"
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_category_ids"}, required=True, constant=True
    )


class MotionBlock(Model):
    collection = "motion_block"
    verbose_name = "motion block"

    id = fields.IntegerField(required=True, constant=True)
    title = fields.CharField(required=True)
    internal = fields.BooleanField()
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only."
        },
    )
    motion_ids = fields.RelationListField(
        to={"motion": "block_id"}, equal_fields="meeting_id"
    )
    agenda_item_id = fields.RelationField(
        to={"agenda_item": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to={"list_of_speakers": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        equal_fields="meeting_id",
    )
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_block_ids"}, required=True, constant=True
    )


class MotionChangeRecommendation(Model):
    collection = "motion_change_recommendation"
    verbose_name = "motion change recommendation"

    id = fields.IntegerField(required=True, constant=True)
    rejected = fields.BooleanField(default=False)
    internal = fields.BooleanField(default=False)
    type = fields.CharField(
        default="replacement",
        constraints={"enum": ["replacement", "insertion", "deletion", "other"]},
    )
    other_description = fields.CharField()
    line_from = fields.IntegerField(constraints={"minimum": 0})
    line_to = fields.IntegerField(constraints={"minimum": 0})
    text = fields.HTMLStrictField()
    creation_time = fields.TimestampField(read_only=True)
    motion_id = fields.RelationField(
        to={"motion": "change_recommendation_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_change_recommendation_ids"}, required=True, constant=True
    )


class MotionState(Model):
    collection = "motion_state"
    verbose_name = "motion state"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    weight = fields.IntegerField(required=True)
    recommendation_label = fields.CharField()
    is_internal = fields.BooleanField()
    css_class = fields.CharField(
        required=True,
        default="lightblue",
        constraints={"enum": ["grey", "red", "green", "lightblue", "yellow"]},
    )
    restrictions = fields.CharArrayField(
        default=[],
        in_array_constraints={
            "enum": [
                "motion.can_see_internal",
                "motion.can_manage_metadata",
                "motion.can_manage",
                "is_submitter",
            ]
        },
    )
    allow_support = fields.BooleanField(default=False)
    allow_create_poll = fields.BooleanField(default=False)
    allow_submitter_edit = fields.BooleanField(default=False)
    set_number = fields.BooleanField(default=True)
    show_state_extension_field = fields.BooleanField(default=False)
    show_recommendation_extension_field = fields.BooleanField(default=False)
    merge_amendment_into_final = fields.CharField(
        default="undefined",
        constraints={"enum": ["do_not_merge", "undefined", "do_merge"]},
    )
    allow_motion_forwarding = fields.BooleanField(default=False)
    allow_amendment_forwarding = fields.BooleanField()
    set_workflow_timestamp = fields.BooleanField(default=False)
    state_button_label = fields.CharField()
    submitter_withdraw_state_id = fields.RelationField(
        to={"motion_state": "submitter_withdraw_back_ids"},
        equal_fields=["meeting_id", "workflow_id"],
    )
    submitter_withdraw_back_ids = fields.RelationListField(
        to={"motion_state": "submitter_withdraw_state_id"},
        equal_fields=["meeting_id", "workflow_id"],
    )
    next_state_ids = fields.RelationListField(
        to={"motion_state": "previous_state_ids"},
        equal_fields=["meeting_id", "workflow_id"],
    )
    previous_state_ids = fields.RelationListField(
        to={"motion_state": "next_state_ids"},
        equal_fields=["meeting_id", "workflow_id"],
    )
    motion_ids = fields.RelationListField(
        to={"motion": "state_id"},
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    motion_recommendation_ids = fields.RelationListField(
        to={"motion": "recommendation_id"}, equal_fields="meeting_id"
    )
    workflow_id = fields.RelationField(
        to={"motion_workflow": "state_ids"}, required=True, equal_fields="meeting_id"
    )
    first_state_of_workflow_id = fields.RelationField(
        to={"motion_workflow": "first_state_id"},
        on_delete=fields.OnDelete.PROTECT,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_state_ids"}, required=True, constant=True
    )


class MotionWorkflow(Model):
    collection = "motion_workflow"
    verbose_name = "motion workflow"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only."
        },
    )
    state_ids = fields.RelationListField(
        to={"motion_state": "workflow_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    first_state_id = fields.RelationField(
        to={"motion_state": "first_state_of_workflow_id"},
        required=True,
        equal_fields="meeting_id",
    )
    default_workflow_meeting_id = fields.RelationField(
        to={"meeting": "motions_default_workflow_id"}
    )
    default_amendment_workflow_meeting_id = fields.RelationField(
        to={"meeting": "motions_default_amendment_workflow_id"}
    )
    meeting_id = fields.RelationField(
        to={"meeting": "motion_workflow_ids"}, required=True, constant=True
    )


class Poll(Model, PollModelMixin):
    collection = "poll"
    verbose_name = "poll"

    id = fields.IntegerField(required=True, constant=True)
    description = fields.TextField()
    title = fields.CharField(required=True)
    type = fields.CharField(
        required=True,
        constraints={"enum": ["analog", "named", "pseudoanonymous", "cryptographic"]},
    )
    backend = fields.CharField(
        required=True, default="fast", constraints={"enum": ["long", "fast"]}
    )
    is_pseudoanonymized = fields.BooleanField()
    pollmethod = fields.CharField(
        required=True, constraints={"enum": ["Y", "YN", "YNA", "N"]}
    )
    state = fields.CharField(
        default="created",
        constraints={"enum": ["created", "started", "finished", "published"]},
    )
    min_votes_amount = fields.IntegerField(default=1, constraints={"minimum": 1})
    max_votes_amount = fields.IntegerField(default=1, constraints={"minimum": 1})
    max_votes_per_option = fields.IntegerField(default=1, constraints={"minimum": 1})
    global_yes = fields.BooleanField(default=False)
    global_no = fields.BooleanField(default=False)
    global_abstain = fields.BooleanField(default=False)
    onehundred_percent_base = fields.CharField(
        required=True,
        default="disabled",
        constraints={
            "enum": [
                "Y",
                "YN",
                "YNA",
                "N",
                "valid",
                "cast",
                "entitled",
                "entitled_present",
                "disabled",
            ]
        },
    )
    votesvalid = fields.DecimalField()
    votesinvalid = fields.DecimalField()
    votescast = fields.DecimalField()
    entitled_users_at_stop = fields.JSONField()
    live_voting_enabled = fields.BooleanField(
        default=False,
        constraints={
            "description": "If true, the vote service sends the votes of the users to the autoupdate service."
        },
    )
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only."
        },
    )
    crypt_key = fields.CharField(
        read_only=True,
        constraints={"description": "base64 public key to cryptographic votes."},
    )
    crypt_signature = fields.CharField(
        read_only=True,
        constraints={"description": "base64 signature of cryptographic_key."},
    )
    votes_raw = fields.TextField(
        read_only=True, constraints={"description": "original form of decrypted votes."}
    )
    votes_signature = fields.CharField(
        read_only=True,
        constraints={"description": "base64 signature of votes_raw field."},
    )
    content_object_id = fields.GenericRelationField(
        to={"motion": "poll_ids", "assignment": "poll_ids", "topic": "poll_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    option_ids = fields.RelationListField(
        to={"option": "poll_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    global_option_id = fields.RelationField(
        to={"option": "used_as_global_option_in_poll_id"},
        on_delete=fields.OnDelete.CASCADE,
        constant=True,
        equal_fields="meeting_id",
    )
    voted_ids = fields.RelationListField(to={"user": "poll_voted_ids"})
    entitled_group_ids = fields.RelationListField(
        to={"group": "poll_ids"}, equal_fields="meeting_id"
    )
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "poll_ids"}, required=True, constant=True
    )


class Option(Model):
    collection = "option"
    verbose_name = "option"

    id = fields.IntegerField(required=True, constant=True)
    weight = fields.IntegerField(default=10000)
    text = fields.HTMLStrictField()
    yes = fields.DecimalField()
    no = fields.DecimalField()
    abstain = fields.DecimalField()
    poll_id = fields.RelationField(
        to={"poll": "option_ids"}, constant=True, equal_fields="meeting_id"
    )
    used_as_global_option_in_poll_id = fields.RelationField(
        to={"poll": "global_option_id"}, constant=True, equal_fields="meeting_id"
    )
    vote_ids = fields.RelationListField(
        to={"vote": "option_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    content_object_id = fields.GenericRelationField(
        to={
            "poll_candidate_list": "option_id",
            "user": "option_ids",
            "motion": "option_ids",
        },
        constant=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "option_ids"}, required=True, constant=True
    )


class Vote(Model):
    collection = "vote"
    verbose_name = "vote"

    id = fields.IntegerField(required=True, constant=True)
    weight = fields.DecimalField(constant=True)
    value = fields.CharField(constant=True)
    user_token = fields.CharField(required=True, constant=True)
    option_id = fields.RelationField(
        to={"option": "vote_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    user_id = fields.RelationField(to={"user": "vote_ids"})
    delegated_user_id = fields.RelationField(to={"user": "delegated_vote_ids"})
    meeting_id = fields.RelationField(
        to={"meeting": "vote_ids"}, required=True, constant=True
    )


class Assignment(Model):
    collection = "assignment"
    verbose_name = "assignment"

    id = fields.IntegerField(required=True, constant=True)
    title = fields.CharField(required=True)
    description = fields.HTMLStrictField()
    open_posts = fields.IntegerField(default=0, constraints={"minimum": 0})
    phase = fields.CharField(
        default="search", constraints={"enum": ["search", "voting", "finished"]}
    )
    default_poll_description = fields.TextField()
    number_poll_candidates = fields.BooleanField()
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only."
        },
    )
    candidate_ids = fields.RelationListField(
        to={"assignment_candidate": "assignment_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    poll_ids = fields.RelationListField(
        to={"poll": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    agenda_item_id = fields.RelationField(
        to={"agenda_item": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    list_of_speakers_id = fields.RelationField(
        to={"list_of_speakers": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    tag_ids = fields.RelationListField(
        to={"tag": "tagged_ids"}, equal_fields="meeting_id"
    )
    attachment_meeting_mediafile_ids = fields.RelationListField(
        to={"meeting_mediafile": "attachment_ids"}, equal_fields="meeting_id"
    )
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "assignment_ids"}, required=True, constant=True
    )
    history_entry_ids = fields.RelationListField(to={"history_entry": "model_id"})


class AssignmentCandidate(Model):
    collection = "assignment_candidate"
    verbose_name = "assignment candidate"

    id = fields.IntegerField(required=True, constant=True)
    weight = fields.IntegerField(default=10000)
    assignment_id = fields.RelationField(
        to={"assignment": "candidate_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    meeting_user_id = fields.RelationField(
        to={"meeting_user": "assignment_candidate_ids"}, constant=True
    )
    meeting_id = fields.RelationField(
        to={"meeting": "assignment_candidate_ids"}, required=True, constant=True
    )


class PollCandidateList(Model):
    collection = "poll_candidate_list"
    verbose_name = "poll candidate list"

    id = fields.IntegerField(required=True, constant=True)
    poll_candidate_ids = fields.RelationListField(
        to={"poll_candidate": "poll_candidate_list_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "poll_candidate_list_ids"}, required=True, constant=True
    )
    option_id = fields.RelationField(
        to={"option": "content_object_id"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )


class PollCandidate(Model):
    collection = "poll_candidate"
    verbose_name = "poll candidate"

    id = fields.IntegerField(required=True, constant=True)
    poll_candidate_list_id = fields.RelationField(
        to={"poll_candidate_list": "poll_candidate_ids"},
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    user_id = fields.RelationField(to={"user": "poll_candidate_ids"}, constant=True)
    weight = fields.IntegerField(required=True)
    meeting_id = fields.RelationField(
        to={"meeting": "poll_candidate_ids"}, required=True, constant=True
    )


class Mediafile(Model):
    collection = "mediafile"
    verbose_name = "mediafile"

    id = fields.IntegerField(required=True, constant=True)
    title = fields.CharField(
        constraints={"description": "Title and parent_id must be unique."}
    )
    is_directory = fields.BooleanField()
    filesize = fields.IntegerField(
        read_only=True,
        constraints={"description": "In bytes, not the human readable format anymore."},
    )
    filename = fields.CharField(
        constraints={
            "description": "The uploaded filename. Will be used for downloading. Only writeable on create."
        }
    )
    mimetype = fields.CharField()
    pdf_information = fields.JSONField()
    create_timestamp = fields.TimestampField()
    token = fields.CharField()
    published_to_meetings_in_organization_id = fields.RelationField(
        to={"organization": "published_mediafile_ids"}
    )
    parent_id = fields.RelationField(
        to={"mediafile": "child_ids"}, equal_fields="owner_id"
    )
    child_ids = fields.RelationListField(
        to={"mediafile": "parent_id"}, equal_fields="owner_id"
    )
    owner_id = fields.GenericRelationField(
        to={"organization": "mediafile_ids", "meeting": "mediafile_ids"},
        required=True,
        constant=True,
    )
    meeting_mediafile_ids = fields.RelationListField(
        to={"meeting_mediafile": "mediafile_id"}, on_delete=fields.OnDelete.CASCADE
    )


class MeetingMediafile(Model):
    collection = "meeting_mediafile"
    verbose_name = "meeting mediafile"

    id = fields.IntegerField(required=True, constant=True)
    mediafile_id = fields.RelationField(
        to={"mediafile": "meeting_mediafile_ids"}, required=True
    )
    meeting_id = fields.RelationField(
        to={"meeting": "meeting_mediafile_ids"}, required=True
    )
    is_public = fields.BooleanField(
        required=True,
        constraints={
            "description": "Calculated in actions. Used to discern whether the (meeting-)mediafile can be seen by everyone, because, in the case of inherited_access_group_ids == [], it would otherwise not be clear. inherited_access_group_ids == [] can have two causes: cancelling access groups (=> is_public := false) or no access groups at all (=> is_public := true)"
        },
    )
    inherited_access_group_ids = fields.RelationListField(
        to={"group": "meeting_mediafile_inherited_access_group_ids"},
        constraints={
            "description": "Calculated in actions. Shows what access group permissions are actually relevant. Calculated as the intersection of this meeting_mediafiles access_group_ids and the related mediafiles potential parent mediafiles inherited_access_group_ids. If the parent has no meeting_mediafile for this meeting, its inherited access group is assumed to be the meetings admin group. If there is no parent, the inherited_access_group_ids is equal to the access_group_ids. If the access_group_ids are empty, the interpretations is that every group has access rights, therefore the parent inherited_access_group_ids are used as-is."
        },
    )
    access_group_ids = fields.RelationListField(
        to={"group": "meeting_mediafile_access_group_ids"}
    )
    list_of_speakers_id = fields.RelationField(
        to={"list_of_speakers": "content_object_id"}, on_delete=fields.OnDelete.CASCADE
    )
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"}, on_delete=fields.OnDelete.CASCADE
    )
    attachment_ids = fields.GenericRelationListField(
        to={
            "motion": "attachment_meeting_mediafile_ids",
            "topic": "attachment_meeting_mediafile_ids",
            "assignment": "attachment_meeting_mediafile_ids",
        }
    )
    used_as_logo_projector_main_in_meeting_id = fields.RelationField(
        to={"meeting": "logo_projector_main_id"}
    )
    used_as_logo_projector_header_in_meeting_id = fields.RelationField(
        to={"meeting": "logo_projector_header_id"}
    )
    used_as_logo_web_header_in_meeting_id = fields.RelationField(
        to={"meeting": "logo_web_header_id"}
    )
    used_as_logo_pdf_header_l_in_meeting_id = fields.RelationField(
        to={"meeting": "logo_pdf_header_l_id"}
    )
    used_as_logo_pdf_header_r_in_meeting_id = fields.RelationField(
        to={"meeting": "logo_pdf_header_r_id"}
    )
    used_as_logo_pdf_footer_l_in_meeting_id = fields.RelationField(
        to={"meeting": "logo_pdf_footer_l_id"}
    )
    used_as_logo_pdf_footer_r_in_meeting_id = fields.RelationField(
        to={"meeting": "logo_pdf_footer_r_id"}
    )
    used_as_logo_pdf_ballot_paper_in_meeting_id = fields.RelationField(
        to={"meeting": "logo_pdf_ballot_paper_id"}
    )
    used_as_font_regular_in_meeting_id = fields.RelationField(
        to={"meeting": "font_regular_id"}
    )
    used_as_font_italic_in_meeting_id = fields.RelationField(
        to={"meeting": "font_italic_id"}
    )
    used_as_font_bold_in_meeting_id = fields.RelationField(
        to={"meeting": "font_bold_id"}
    )
    used_as_font_bold_italic_in_meeting_id = fields.RelationField(
        to={"meeting": "font_bold_italic_id"}
    )
    used_as_font_monospace_in_meeting_id = fields.RelationField(
        to={"meeting": "font_monospace_id"}
    )
    used_as_font_chyron_speaker_name_in_meeting_id = fields.RelationField(
        to={"meeting": "font_chyron_speaker_name_id"}
    )
    used_as_font_projector_h1_in_meeting_id = fields.RelationField(
        to={"meeting": "font_projector_h1_id"}
    )
    used_as_font_projector_h2_in_meeting_id = fields.RelationField(
        to={"meeting": "font_projector_h2_id"}
    )


class Projector(Model):
    collection = "projector"
    verbose_name = "projector"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField()
    is_internal = fields.BooleanField(default=False)
    scale = fields.IntegerField(default=0)
    scroll = fields.IntegerField(default=0, constraints={"minimum": 0})
    width = fields.IntegerField(default=1200, constraints={"minimum": 1})
    aspect_ratio_numerator = fields.IntegerField(default=16, constraints={"minimum": 1})
    aspect_ratio_denominator = fields.IntegerField(
        default=9, constraints={"minimum": 1}
    )
    color = fields.ColorField(default="#000000")
    background_color = fields.ColorField(default="#ffffff")
    header_background_color = fields.ColorField(default="#317796")
    header_font_color = fields.ColorField(default="#f5f5f5")
    header_h1_color = fields.ColorField(default="#317796")
    chyron_background_color = fields.ColorField(default="#317796")
    chyron_background_color_2 = fields.ColorField(default="#134768")
    chyron_font_color = fields.ColorField(default="#ffffff")
    chyron_font_color_2 = fields.ColorField(default="#ffffff")
    show_header_footer = fields.BooleanField(default=True)
    show_title = fields.BooleanField(default=True)
    show_logo = fields.BooleanField(default=True)
    show_clock = fields.BooleanField(default=True)
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only."
        },
    )
    current_projection_ids = fields.RelationListField(
        to={"projection": "current_projector_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    preview_projection_ids = fields.RelationListField(
        to={"projection": "preview_projector_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    history_projection_ids = fields.RelationListField(
        to={"projection": "history_projector_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    used_as_reference_projector_meeting_id = fields.RelationField(
        to={"meeting": "reference_projector_id"}
    )
    used_as_default_projector_for_agenda_item_list_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_agenda_item_list_ids"}
    )
    used_as_default_projector_for_topic_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_topic_ids"}
    )
    used_as_default_projector_for_list_of_speakers_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_list_of_speakers_ids"}
    )
    used_as_default_projector_for_current_los_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_current_los_ids"}
    )
    used_as_default_projector_for_motion_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_motion_ids"}
    )
    used_as_default_projector_for_amendment_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_amendment_ids"}
    )
    used_as_default_projector_for_motion_block_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_motion_block_ids"}
    )
    used_as_default_projector_for_assignment_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_assignment_ids"}
    )
    used_as_default_projector_for_mediafile_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_mediafile_ids"}
    )
    used_as_default_projector_for_message_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_message_ids"}
    )
    used_as_default_projector_for_countdown_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_countdown_ids"}
    )
    used_as_default_projector_for_assignment_poll_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_assignment_poll_ids"}
    )
    used_as_default_projector_for_motion_poll_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_motion_poll_ids"}
    )
    used_as_default_projector_for_poll_in_meeting_id = fields.RelationField(
        to={"meeting": "default_projector_poll_ids"}
    )
    meeting_id = fields.RelationField(
        to={"meeting": "projector_ids"}, required=True, constant=True
    )


class Projection(Model):
    collection = "projection"
    verbose_name = "projection"

    id = fields.IntegerField(required=True, constant=True)
    options = fields.JSONField()
    stable = fields.BooleanField(default=False)
    weight = fields.IntegerField()
    type = fields.CharField()
    current_projector_id = fields.RelationField(
        to={"projector": "current_projection_ids"}, equal_fields="meeting_id"
    )
    preview_projector_id = fields.RelationField(
        to={"projector": "preview_projection_ids"}, equal_fields="meeting_id"
    )
    history_projector_id = fields.RelationField(
        to={"projector": "history_projection_ids"}, equal_fields="meeting_id"
    )
    content_object_id = fields.GenericRelationField(
        to={
            "projector_countdown": "projection_ids",
            "projector_message": "projection_ids",
            "poll": "projection_ids",
            "topic": "projection_ids",
            "agenda_item": "projection_ids",
            "assignment": "projection_ids",
            "motion_block": "projection_ids",
            "list_of_speakers": "projection_ids",
            "meeting_mediafile": "projection_ids",
            "motion": "projection_ids",
            "meeting": "projection_ids",
        },
        required=True,
        constant=True,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "all_projection_ids"}, required=True, constant=True
    )


class ProjectorMessage(Model):
    collection = "projector_message"
    verbose_name = "projector message"

    id = fields.IntegerField(required=True, constant=True)
    message = fields.HTMLStrictField()
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    meeting_id = fields.RelationField(
        to={"meeting": "projector_message_ids"}, required=True, constant=True
    )


class ProjectorCountdown(Model):
    collection = "projector_countdown"
    verbose_name = "projector countdown"

    id = fields.IntegerField(required=True, constant=True)
    title = fields.CharField(required=True)
    description = fields.CharField(default="")
    default_time = fields.IntegerField()
    countdown_time = fields.FloatField(default=60)
    running = fields.BooleanField(default=False)
    projection_ids = fields.RelationListField(
        to={"projection": "content_object_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    used_as_list_of_speakers_countdown_meeting_id = fields.RelationField(
        to={"meeting": "list_of_speakers_countdown_id"}
    )
    used_as_poll_countdown_meeting_id = fields.RelationField(
        to={"meeting": "poll_countdown_id"}
    )
    meeting_id = fields.RelationField(
        to={"meeting": "projector_countdown_ids"}, required=True, constant=True
    )


class ChatGroup(Model):
    collection = "chat_group"
    verbose_name = "chat group"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    weight = fields.IntegerField(default=10000)
    chat_message_ids = fields.RelationListField(
        to={"chat_message": "chat_group_id"},
        on_delete=fields.OnDelete.CASCADE,
        equal_fields="meeting_id",
    )
    read_group_ids = fields.RelationListField(
        to={"group": "read_chat_group_ids"}, equal_fields="meeting_id"
    )
    write_group_ids = fields.RelationListField(
        to={"group": "write_chat_group_ids"}, equal_fields="meeting_id"
    )
    meeting_id = fields.RelationField(
        to={"meeting": "chat_group_ids"}, required=True, constant=True
    )


class ChatMessage(Model):
    collection = "chat_message"
    verbose_name = "chat message"

    id = fields.IntegerField(required=True, constant=True)
    content = fields.HTMLStrictField(required=True)
    created = fields.TimestampField(required=True)
    meeting_user_id = fields.RelationField(
        to={"meeting_user": "chat_message_ids"}, constant=True
    )
    chat_group_id = fields.RelationField(
        to={"chat_group": "chat_message_ids"}, required=True, constant=True
    )
    meeting_id = fields.RelationField(
        to={"meeting": "chat_message_ids"}, required=True, constant=True
    )


class ActionWorker(Model):
    collection = "action_worker"
    verbose_name = "action worker"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(required=True)
    state = fields.CharField(
        required=True, constraints={"enum": ["running", "end", "aborted"]}
    )
    created = fields.TimestampField(required=True)
    timestamp = fields.TimestampField(required=True)
    result = fields.JSONField()
    user_id = fields.IntegerField(
        required=True,
        constant=True,
        constraints={
            "description": "Id of the calling user. If the action is called via internal route, the value will be -1."
        },
    )


class ImportPreview(Model):
    collection = "import_preview"
    verbose_name = "import preview"

    id = fields.IntegerField(required=True, constant=True)
    name = fields.CharField(
        required=True,
        constraints={
            "enum": ["account", "participant", "topic", "committee", "motion"]
        },
    )
    state = fields.CharField(
        required=True, constraints={"enum": ["warning", "error", "done"]}
    )
    created = fields.TimestampField(required=True)
    result = fields.JSONField()


class HistoryPosition(Model):
    collection = "history_position"
    verbose_name = "history position"

    id = fields.IntegerField(required=True, constant=True)
    timestamp = fields.TimestampField(read_only=True)
    original_user_id = fields.IntegerField(constant=True)
    user_id = fields.RelationField(to={"user": "history_position_ids"})
    entry_ids = fields.RelationListField(
        to={"history_entry": "position_id"}, on_delete=fields.OnDelete.CASCADE
    )


class HistoryEntry(Model):
    collection = "history_entry"
    verbose_name = "history entry"

    id = fields.IntegerField(required=True, constant=True)
    entries = fields.CharArrayField()
    original_model_id = fields.CharField(constant=True)
    model_id = fields.GenericRelationField(
        to={
            "user": "history_entry_ids",
            "motion": "history_entry_ids",
            "assignment": "history_entry_ids",
        }
    )
    position_id = fields.RelationField(
        to={"history_position": "entry_ids"}, required=True, constant=True
    )
    meeting_id = fields.RelationField(to={"meeting": "relevant_history_entry_ids"})
