
-- schema.sql for initial database setup OpenSlides
-- Code generated. DO NOT EDIT.

-- MODELS_YML_CHECKSUM = 'f1842d0f88bf29f159ecd509881e486d'

CREATE TABLE IF NOT EXISTS organizationT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(50),
    description text,
    legal_notice text,
    privacy_policy text,
    login_text text,
    reset_password_verbose_errors boolean,
    enable_electronic_voting boolean,
    enable_chat boolean,
    limit_of_meetings integer DEFAULT '0',
    limit_of_users integer DEFAULT '0',
    theme_id integer NOT NULL,
    users_email_sender varchar(256) DEFAULT 'OpenSlides',
    users_email_replyto varchar(256),
    users_email_subject varchar(256) DEFAULT 'OpenSlides access data',
    users_email_body text DEFAULT 'Dear {name},

this is your personal OpenSlides login:

{url}
Username: {username}
Password: {password}


This email was generated automatically.',
    url varchar(256) DEFAULT 'https://example.com'
);


CREATE TABLE IF NOT EXISTS userT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    username varchar(256) NOT NULL,
    pronoun varchar(256),
    title varchar(256),
    first_name varchar(256),
    last_name varchar(256),
    is_active boolean,
    is_physical_person boolean DEFAULT 'True',
    password varchar(256),
    default_password varchar(256),
    can_change_own_password boolean DEFAULT 'True',
    gender varchar(256),
    email varchar(256),
    default_number varchar(256),
    default_structure_level varchar(256),
    default_vote_weight decimal(6) DEFAULT '1.000000',
    last_email_send timestamptz,
    is_demo_user boolean,
    last_login timestamptz,
    organization_management_level varchar(256)
);


CREATE TABLE IF NOT EXISTS committee_to_user (
    user_id integer NOT NULL,
    committee_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS group_to_user (
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS poll_to_user (
    user_id integer NOT NULL,
    poll_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS presence_user_in_meeting (
    meeting_id integer NOT NULL,
    user_id integer NOT NULL,
    begin timestamptz NOT NULL
);


CREATE TABLE IF NOT EXISTS meeting_user (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    comment text,
    number varchar(256),
    structure_level varchar(256),
    about_me text,
    vote_weight decimal(6),
    user_id integer NOT NULL,
    meeting_id integer NOT NULL,
    speaker_ids integer[],
    supported_motion_ids integer[],
    motion_submitter_ids integer[],
    assignment_candidate_ids integer[],
    vote_delegated_to_id integer,
    vote_delegations_from_ids integer[],
    chat_message_ids integer[],
    group_ids integer[]
);


CREATE TABLE IF NOT EXISTS organization_tag (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    color integer CHECK (color >= 0 and color <= 16777215) NOT NULL,
    tagged_ids varchar(256)[]
);


CREATE TABLE IF NOT EXISTS organization_tag_to_committee_meeting (
    organization_tag_id integer NOT NULL,
    meeting_id integer,
    committee_id integer
);


CREATE TABLE IF NOT EXISTS theme (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    accent_100 integer CHECK (accent_100 >= 0 and accent_100 <= 16777215),
    accent_200 integer CHECK (accent_200 >= 0 and accent_200 <= 16777215),
    accent_300 integer CHECK (accent_300 >= 0 and accent_300 <= 16777215),
    accent_400 integer CHECK (accent_400 >= 0 and accent_400 <= 16777215),
    accent_50 integer CHECK (accent_50 >= 0 and accent_50 <= 16777215),
    accent_500 integer CHECK (accent_500 >= 0 and accent_500 <= 16777215) NOT NULL,
    accent_600 integer CHECK (accent_600 >= 0 and accent_600 <= 16777215),
    accent_700 integer CHECK (accent_700 >= 0 and accent_700 <= 16777215),
    accent_800 integer CHECK (accent_800 >= 0 and accent_800 <= 16777215),
    accent_900 integer CHECK (accent_900 >= 0 and accent_900 <= 16777215),
    accent_a100 integer CHECK (accent_a100 >= 0 and accent_a100 <= 16777215),
    accent_a200 integer CHECK (accent_a200 >= 0 and accent_a200 <= 16777215),
    accent_a400 integer CHECK (accent_a400 >= 0 and accent_a400 <= 16777215),
    accent_a700 integer CHECK (accent_a700 >= 0 and accent_a700 <= 16777215),
    primary_100 integer CHECK (primary_100 >= 0 and primary_100 <= 16777215),
    primary_200 integer CHECK (primary_200 >= 0 and primary_200 <= 16777215),
    primary_300 integer CHECK (primary_300 >= 0 and primary_300 <= 16777215),
    primary_400 integer CHECK (primary_400 >= 0 and primary_400 <= 16777215),
    primary_50 integer CHECK (primary_50 >= 0 and primary_50 <= 16777215),
    primary_500 integer CHECK (primary_500 >= 0 and primary_500 <= 16777215) NOT NULL,
    primary_600 integer CHECK (primary_600 >= 0 and primary_600 <= 16777215),
    primary_700 integer CHECK (primary_700 >= 0 and primary_700 <= 16777215),
    primary_800 integer CHECK (primary_800 >= 0 and primary_800 <= 16777215),
    primary_900 integer CHECK (primary_900 >= 0 and primary_900 <= 16777215),
    primary_a100 integer CHECK (primary_a100 >= 0 and primary_a100 <= 16777215),
    primary_a200 integer CHECK (primary_a200 >= 0 and primary_a200 <= 16777215),
    primary_a400 integer CHECK (primary_a400 >= 0 and primary_a400 <= 16777215),
    primary_a700 integer CHECK (primary_a700 >= 0 and primary_a700 <= 16777215),
    warn_100 integer CHECK (warn_100 >= 0 and warn_100 <= 16777215),
    warn_200 integer CHECK (warn_200 >= 0 and warn_200 <= 16777215),
    warn_300 integer CHECK (warn_300 >= 0 and warn_300 <= 16777215),
    warn_400 integer CHECK (warn_400 >= 0 and warn_400 <= 16777215),
    warn_50 integer CHECK (warn_50 >= 0 and warn_50 <= 16777215),
    warn_500 integer CHECK (warn_500 >= 0 and warn_500 <= 16777215) NOT NULL,
    warn_600 integer CHECK (warn_600 >= 0 and warn_600 <= 16777215),
    warn_700 integer CHECK (warn_700 >= 0 and warn_700 <= 16777215),
    warn_800 integer CHECK (warn_800 >= 0 and warn_800 <= 16777215),
    warn_900 integer CHECK (warn_900 >= 0 and warn_900 <= 16777215),
    warn_a100 integer CHECK (warn_a100 >= 0 and warn_a100 <= 16777215),
    warn_a200 integer CHECK (warn_a200 >= 0 and warn_a200 <= 16777215),
    warn_a400 integer CHECK (warn_a400 >= 0 and warn_a400 <= 16777215),
    warn_a700 integer CHECK (warn_a700 >= 0 and warn_a700 <= 16777215),
    headbar integer CHECK (headbar >= 0 and headbar <= 16777215),
    yes integer CHECK (yes >= 0 and yes <= 16777215),
    no integer CHECK (no >= 0 and no <= 16777215),
    abstain integer CHECK (abstain >= 0 and abstain <= 16777215)
);


CREATE TABLE IF NOT EXISTS committeeT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    description text,
    default_meeting_id integer,
    forwarding_user_id integer
);


CREATE TABLE IF NOT EXISTS forwarding_committee_to_committee (
    forwarding_committee_id integer NOT NULL,
    receiving_committee_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS meetingT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    welcome_title varchar(256) DEFAULT 'Welcome to OpenSlides',
    welcome_text text DEFAULT 'Space for your welcome text.',
    name varchar(100) NOT NULL DEFAULT 'OpenSlides',
    state varchar(256) DEFAULT 'active',
    description varchar(100) DEFAULT 'Presentation and assembly system',
    location varchar(256),
    start_time timestamptz,
    end_time timestamptz,
    imported_at timestamptz,
    jitsi_domain varchar(256),
    jitsi_room_name varchar(256),
    jitsi_room_password varchar(256),
    template_for_organization boolean DEFAULT 'False',
    enable_anonymous boolean DEFAULT 'False',
    custom_translations jsonb,
    conference_show boolean DEFAULT 'False',
    conference_auto_connect boolean DEFAULT 'False',
    conference_los_restriction boolean DEFAULT 'True',
    conference_stream_url varchar(256),
    conference_stream_poster_url varchar(256),
    conference_open_microphone boolean DEFAULT 'False',
    conference_open_video boolean DEFAULT 'False',
    conference_auto_connect_next_speakers integer DEFAULT '0',
    conference_enable_helpdesk boolean DEFAULT 'False',
    applause_enable boolean DEFAULT 'False',
    applause_type varchar(256) DEFAULT 'applause-type-bar',
    applause_show_level boolean DEFAULT 'False',
    applause_min_amount integer DEFAULT '1',
    applause_max_amount integer DEFAULT '0',
    applause_timeout integer DEFAULT '5',
    applause_particle_image_url varchar(256),
    projector_countdown_default_time integer NOT NULL DEFAULT '60',
    projector_countdown_warning_time integer NOT NULL DEFAULT '0',
    export_csv_encoding varchar(256) DEFAULT 'utf-8',
    export_csv_separator varchar(256) DEFAULT ';',
    export_pdf_pagenumber_alignment varchar(256) DEFAULT 'center',
    export_pdf_fontsize integer DEFAULT '10',
    export_pdf_line_height real DEFAULT '1.25',
    export_pdf_page_margin_left integer DEFAULT '20',
    export_pdf_page_margin_top integer DEFAULT '25',
    export_pdf_page_margin_right integer DEFAULT '20',
    export_pdf_page_margin_bottom integer DEFAULT '20',
    export_pdf_pagesize varchar(256) DEFAULT 'A4',
    agenda_show_subtitles boolean DEFAULT 'False',
    agenda_enable_numbering boolean DEFAULT 'True',
    agenda_number_prefix varchar(20),
    agenda_numeral_system varchar(256) DEFAULT 'arabic',
    agenda_item_creation varchar(256) DEFAULT 'default_no',
    agenda_new_items_default_visibility varchar(256) DEFAULT 'internal',
    agenda_show_internal_items_on_projector boolean DEFAULT 'False',
    list_of_speakers_amount_last_on_projector integer DEFAULT '0',
    list_of_speakers_amount_next_on_projector integer DEFAULT '-1',
    list_of_speakers_couple_countdown boolean DEFAULT 'True',
    list_of_speakers_show_amount_of_speakers_on_slide boolean DEFAULT 'True',
    list_of_speakers_present_users_only boolean DEFAULT 'False',
    list_of_speakers_show_first_contribution boolean DEFAULT 'False',
    list_of_speakers_enable_point_of_order_speakers boolean DEFAULT 'True',
    list_of_speakers_enable_pro_contra_speech boolean DEFAULT 'False',
    list_of_speakers_can_set_contribution_self boolean DEFAULT 'False',
    list_of_speakers_speaker_note_for_everyone boolean DEFAULT 'True',
    list_of_speakers_initially_closed boolean DEFAULT 'False',
    motions_default_workflow_id integer NOT NULL,
    motions_default_amendment_workflow_id integer NOT NULL,
    motions_default_statute_amendment_workflow_id integer NOT NULL,
    motions_preamble text DEFAULT 'The assembly may decide:',
    motions_default_line_numbering varchar(256) DEFAULT 'outside',
    motions_line_length integer DEFAULT '85',
    motions_reason_required boolean DEFAULT 'False',
    motions_enable_text_on_projector boolean DEFAULT 'True',
    motions_enable_reason_on_projector boolean DEFAULT 'False',
    motions_enable_sidebox_on_projector boolean DEFAULT 'False',
    motions_enable_recommendation_on_projector boolean DEFAULT 'True',
    motions_show_referring_motions boolean DEFAULT 'True',
    motions_show_sequential_number boolean DEFAULT 'True',
    motions_recommendations_by varchar(256),
    motions_block_slide_columns integer,
    motions_statute_recommendations_by varchar(256),
    motions_recommendation_text_mode varchar(256) DEFAULT 'diff',
    motions_default_sorting varchar(256) DEFAULT 'number',
    motions_number_type varchar(256) DEFAULT 'per_category',
    motions_number_min_digits integer DEFAULT '2',
    motions_number_with_blank boolean DEFAULT 'False',
    motions_statutes_enabled boolean DEFAULT 'False',
    motions_amendments_enabled boolean DEFAULT 'True',
    motions_amendments_in_main_list boolean DEFAULT 'True',
    motions_amendments_of_amendments boolean DEFAULT 'False',
    motions_amendments_prefix varchar(256) DEFAULT '-Ä',
    motions_amendments_text_mode varchar(256) DEFAULT 'paragraph',
    motions_amendments_multiple_paragraphs boolean DEFAULT 'True',
    motions_supporters_min_amount integer DEFAULT '0',
    motions_export_title varchar(256) DEFAULT 'Motions',
    motions_export_preamble text,
    motions_export_submitter_recommendation boolean DEFAULT 'True',
    motions_export_follow_recommendation boolean DEFAULT 'False',
    motion_poll_ballot_paper_selection varchar(256) DEFAULT 'CUSTOM_NUMBER',
    motion_poll_ballot_paper_number integer DEFAULT '8',
    motion_poll_default_type varchar(256) DEFAULT 'pseudoanonymous',
    motion_poll_default_100_percent_base varchar(256) DEFAULT 'YNA',
    motion_poll_default_backend varchar(256) DEFAULT 'fast',
    users_enable_presence_view boolean DEFAULT 'False',
    users_enable_vote_weight boolean DEFAULT 'False',
    users_allow_self_set_present boolean DEFAULT 'True',
    users_pdf_welcometitle varchar(256) DEFAULT 'Welcome to OpenSlides',
    users_pdf_welcometext text DEFAULT '[Place for your welcome and help text.]',
    users_pdf_wlan_ssid varchar(256),
    users_pdf_wlan_password varchar(256),
    users_pdf_wlan_encryption varchar(256),
    users_email_sender varchar(256) DEFAULT 'OpenSlides',
    users_email_replyto varchar(256),
    users_email_subject varchar(256) DEFAULT 'OpenSlides access data',
    users_email_body text DEFAULT 'Dear {name},

this is your personal OpenSlides login:

{url}
Username: {username}
Password: {password}


This email was generated automatically.',
    users_enable_vote_delegations boolean,
    assignments_export_title varchar(256) DEFAULT 'Elections',
    assignments_export_preamble text,
    assignment_poll_ballot_paper_selection varchar(256) DEFAULT 'CUSTOM_NUMBER',
    assignment_poll_ballot_paper_number integer DEFAULT '8',
    assignment_poll_add_candidates_to_list_of_speakers boolean DEFAULT 'False',
    assignment_poll_enable_max_votes_per_option boolean DEFAULT 'False',
    assignment_poll_sort_poll_result_by_votes boolean DEFAULT 'True',
    assignment_poll_default_type varchar(256) DEFAULT 'pseudoanonymous',
    assignment_poll_default_method varchar(256) DEFAULT 'Y',
    assignment_poll_default_100_percent_base varchar(256) DEFAULT 'valid',
    assignment_poll_default_backend varchar(256) DEFAULT 'fast',
    poll_ballot_paper_selection varchar(256),
    poll_ballot_paper_number integer,
    poll_sort_poll_result_by_votes boolean,
    poll_default_type varchar(256) DEFAULT 'analog',
    poll_default_method varchar(256),
    poll_default_100_percent_base varchar(256) DEFAULT 'YNA',
    poll_default_backend varchar(256) DEFAULT 'fast',
    poll_couple_countdown boolean DEFAULT 'True',
    logo_projector_main_id integer,
    logo_projector_header_id integer,
    logo_web_header_id integer,
    logo_pdf_header_l_id integer,
    logo_pdf_header_r_id integer,
    logo_pdf_footer_l_id integer,
    logo_pdf_footer_r_id integer,
    logo_pdf_ballot_paper_id integer,
    font_regular_id integer,
    font_italic_id integer,
    font_bold_id integer,
    font_bold_italic_id integer,
    font_monospace_id integer,
    font_chyron_speaker_name_id integer,
    font_projector_h1_id integer,
    font_projector_h2_id integer,
    committee_id integer NOT NULL,
    reference_projector_id integer NOT NULL,
    default_group_id integer NOT NULL,
    admin_group_id integer
);


CREATE TABLE IF NOT EXISTS groupT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    permissions varchar(256)[],
    weight integer,
    mediafile_access_group_ids integer[],
    mediafile_inherited_access_group_ids integer[],
    read_comment_section_ids integer[],
    write_comment_section_ids integer[],
    poll_ids integer[],
    used_as_motion_poll_default_id integer,
    used_as_assignment_poll_default_id integer,
    used_as_topic_poll_default_id integer,
    used_as_poll_default_id integer,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS personal_note (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    note text,
    star boolean,
    user_id integer NOT NULL,
    motion_id integer,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS tag (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    tagged_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS agenda_item (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    item_number varchar(256),
    comment varchar(256),
    closed boolean DEFAULT 'False',
    type varchar(256) DEFAULT 'common',
    duration integer,
    is_internal boolean,
    is_hidden boolean,
    level integer,
    weight integer DEFAULT '10000',
    content_object_id integer NOT NULL,
    parent_id integer,
    tag_ids integer[],
    projection_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS list_of_speakers (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    closed boolean DEFAULT 'False',
    sequential_number integer NOT NULL,
    content_object_id integer NOT NULL,
    speaker_ids integer[],
    projection_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS speaker (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    begin_time timestamptz,
    end_time timestamptz,
    weight integer DEFAULT '10000',
    speech_state varchar(256),
    note varchar(250),
    point_of_order boolean,
    list_of_speakers_id integer NOT NULL,
    user_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS topic (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256) NOT NULL,
    text text,
    sequential_number integer NOT NULL,
    attachment_ids integer[],
    agenda_item_id integer NOT NULL,
    list_of_speakers_id integer NOT NULL,
    tag_ids integer[],
    poll_ids integer[],
    projection_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motionT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    number varchar(256),
    number_value integer,
    sequential_number integer NOT NULL,
    title varchar(256) NOT NULL,
    text text,
    amendment_paragraph jsonb,
    modified_final_version text,
    reason text,
    category_weight integer DEFAULT '10000',
    state_extension varchar(256),
    recommendation_extension varchar(256),
    sort_weight integer DEFAULT '10000',
    created timestamptz,
    last_modified timestamptz,
    start_line_number integer DEFAULT '1',
    forwarded timestamptz,
    lead_motion_id integer,
    amendment_ids integer[],
    sort_parent_id integer,
    origin_id integer,
    origin_meeting_id integer,
    derived_motion_ids integer[],
    all_origin_ids integer[],
    all_derived_motion_ids integer[],
    state_id integer NOT NULL,
    recommendation_id integer,
    state_extension_reference_ids integer[],
    referenced_in_motion_state_extension_ids integer[],
    recommendation_extension_reference_ids integer[],
    referenced_in_motion_recommendation_extension_ids integer[],
    category_id integer,
    block_id integer,
    submitter_ids integer[],
    supporter_meeting_user_ids integer[],
    poll_ids integer[],
    option_ids integer[],
    change_recommendation_ids integer[],
    statute_paragraph_id integer,
    comment_ids integer[],
    agenda_item_id integer,
    list_of_speakers_id integer NOT NULL,
    tag_ids integer[],
    attachment_ids integer[],
    projection_ids integer[],
    personal_note_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_submitter (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    weight integer,
    user_id integer NOT NULL,
    motion_id integer NOT NULL,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_comment (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    comment text,
    motion_id integer NOT NULL,
    section_id integer NOT NULL,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_comment_section (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    weight integer DEFAULT '10000',
    sequential_number integer NOT NULL,
    submitter_can_write boolean,
    comment_ids integer[],
    read_group_ids integer[],
    write_group_ids integer[]
);


CREATE TABLE IF NOT EXISTS motion_category (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    prefix varchar(256),
    weight integer DEFAULT '10000',
    level integer,
    sequential_number integer NOT NULL,
    parent_id integer,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_block (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256) NOT NULL,
    internal boolean,
    sequential_number integer NOT NULL,
    motion_ids integer[],
    agenda_item_id integer,
    list_of_speakers_id integer NOT NULL,
    projection_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_change_recommendation (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    rejected boolean DEFAULT 'False',
    internal boolean DEFAULT 'False',
    type varchar(256) DEFAULT 'replacement',
    other_description varchar(256),
    line_from integer,
    line_to integer,
    text text,
    creation_time timestamptz,
    motion_id integer NOT NULL,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_state (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    weight integer NOT NULL,
    recommendation_label varchar(256),
    css_class varchar(256) NOT NULL DEFAULT 'lightblue',
    restrictions varchar(256)[],
    allow_support boolean DEFAULT 'False',
    allow_create_poll boolean DEFAULT 'False',
    allow_submitter_edit boolean DEFAULT 'False',
    set_number boolean DEFAULT 'True',
    show_state_extension_field boolean DEFAULT 'False',
    show_recommendation_extension_field boolean DEFAULT 'False',
    merge_amendment_into_final varchar(256) DEFAULT 'undefined',
    allow_motion_forwarding boolean,
    set_created_timestamp boolean,
    submitter_withdraw_state_id integer,
    submitter_withdraw_back_ids integer[],
    next_state_ids integer[],
    previous_state_ids integer[],
    motion_ids integer[],
    motion_recommendation_ids integer[],
    workflow_id integer NOT NULL,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_state_to_state (
    previous_state_id integer NOT NULL,
    next_state_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_workflow (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    sequential_number integer NOT NULL,
    state_ids integer[],
    first_state_id integer NOT NULL,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_statute_paragraph (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256) NOT NULL,
    text text,
    weight integer DEFAULT '10000',
    sequential_number integer NOT NULL,
    motion_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS poll (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    description text,
    title varchar(256) NOT NULL,
    type varchar(256) NOT NULL,
    backend varchar(256) NOT NULL DEFAULT 'fast',
    is_pseudoanonymized boolean,
    pollmethod varchar(256) NOT NULL,
    state varchar(256) DEFAULT 'created',
    min_votes_amount integer DEFAULT '1',
    max_votes_amount integer DEFAULT '1',
    max_votes_per_option integer DEFAULT '1',
    global_yes boolean DEFAULT 'False',
    global_no boolean DEFAULT 'False',
    global_abstain boolean DEFAULT 'False',
    onehundred_percent_base varchar(256) NOT NULL DEFAULT 'disabled',
    votesvalid decimal(6),
    votesinvalid decimal(6),
    votescast decimal(6),
    entitled_users_at_stop jsonb,
    sequential_number integer NOT NULL,
    crypt_key varchar(256),
    crypt_signature varchar(256),
    votes_raw text,
    votes_signature varchar(256),
    content_object_id integer NOT NULL,
    option_ids integer[],
    global_option_id integer,
    voted_ids integer[],
    entitled_group_ids integer[],
    projection_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS option (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    weight integer DEFAULT '10000',
    text text,
    yes decimal(6),
    no decimal(6),
    abstain decimal(6),
    poll_id integer,
    vote_ids integer[],
    content_motion_id integer,
    content_user_id integer,
    content_poll_candidate_list_id integer
);


CREATE TABLE IF NOT EXISTS vote (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    weight decimal(6),
    value varchar(256),
    user_token varchar(256) NOT NULL,
    option_id integer NOT NULL,
    user_id integer,
    delegated_user_id integer
);


CREATE TABLE IF NOT EXISTS assignment (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256) NOT NULL,
    description text,
    open_posts integer DEFAULT '0',
    phase varchar(256) DEFAULT 'search',
    default_poll_description text,
    number_poll_candidates boolean,
    sequential_number integer NOT NULL,
    candidate_ids integer[],
    poll_ids integer[],
    agenda_item_id integer,
    list_of_speakers_id integer NOT NULL,
    tag_ids integer[],
    attachment_ids integer[],
    projection_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS assignment_candidate (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    weight integer DEFAULT '10000',
    assignment_id integer NOT NULL,
    user_id integer
);


CREATE TABLE IF NOT EXISTS poll_candidate_list (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    poll_candidate_ids integer[],
    option_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS poll_candidate (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    poll_candidate_list_id integer NOT NULL,
    user_id integer NOT NULL,
    weight integer NOT NULL
);


CREATE TABLE IF NOT EXISTS mediafile (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256),
    is_directory boolean,
    filesize integer,
    filename varchar(256),
    mimetype varchar(256),
    pdf_information jsonb,
    create_timestamp timestamptz,
    is_public boolean NOT NULL,
    token varchar(256),
    inherited_access_group_ids integer[],
    access_group_ids integer[],
    parent_id integer,
    list_of_speakers_id integer,
    projection_ids integer[],
    attachment_ids integer[],
    owner_meeting_id integer,
    owner_organization_id integer
);


CREATE TABLE IF NOT EXISTS projector (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256),
    scale integer DEFAULT '0',
    scroll integer DEFAULT '0',
    width integer DEFAULT '1200',
    aspect_ratio_numerator integer DEFAULT '16',
    aspect_ratio_denominator integer DEFAULT '9',
    color integer CHECK (color >= 0 and color <= 16777215) DEFAULT 0,
    background_color integer CHECK (background_color >= 0 and background_color <= 16777215) DEFAULT 16777215,
    header_background_color integer CHECK (header_background_color >= 0 and header_background_color <= 16777215) DEFAULT 3241878,
    header_font_color integer CHECK (header_font_color >= 0 and header_font_color <= 16777215) DEFAULT 16119285,
    header_h1_color integer CHECK (header_h1_color >= 0 and header_h1_color <= 16777215) DEFAULT 3241878,
    chyron_background_color integer CHECK (chyron_background_color >= 0 and chyron_background_color <= 16777215) DEFAULT 3241878,
    chyron_font_color integer CHECK (chyron_font_color >= 0 and chyron_font_color <= 16777215) DEFAULT 16777215,
    show_header_footer boolean DEFAULT 'True',
    show_title boolean DEFAULT 'True',
    show_logo boolean DEFAULT 'True',
    show_clock boolean DEFAULT 'True',
    sequential_number integer NOT NULL,
    current_projection_ids integer[],
    preview_projection_ids integer[],
    history_projection_ids integer[],
    used_as_reference_projector_meeting_id integer,
    used_as_default_projector_for_agenda_all_items_in_meeting_id integer,
    used_as_default_projector_for_topics_in_meeting_id integer,
    used_as_default_projector_for_list_of_speakers_in_meeting_id integer,
    used_as_default_projector_for_cur_list_of_speaker_in_meeting_id integer,
    used_as_default_projector_for_motion_in_meeting_id integer,
    used_as_default_projector_for_amendment_in_meeting_id integer,
    used_as_default_projector_for_motion_block_in_meeting_id integer,
    used_as_default_projector_for_assignment_in_meeting_id integer,
    used_as_default_projector_for_mediafile_in_meeting_id integer,
    used_as_default_projector_for_projector_message_in_meeting_id integer,
    used_as_default_projector_for_projector_countdown_in_meeting_id integer,
    used_as_default_projector_for_assignment_poll_in_meeting_id integer,
    used_as_default_projector_for_motion_poll_in_meeting_id integer,
    used_as_default_projector_for_poll_in_meeting_id integer,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS projection (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    options jsonb,
    stable boolean DEFAULT 'False',
    weight integer,
    type varchar(256),
    current_projector_id integer,
    preview_projector_id integer,
    history_projector_id integer,
    projection_meeting_id integer,
    projection_motion_id integer,
    projection_mediafile_id integer,
    projection_list_of_speakers_id integer,
    projection_motion_block_id integer,
    projection_assignment_id integer,
    projection_agenda_item_id integer,
    projection_topic_id integer,
    projection_poll_id integer,
    projection_projector_message_id integer,
    projection_projector_countdown_id integer,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS projector_message (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    message text,
    projection_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS projector_countdown (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256) NOT NULL,
    description varchar(256) DEFAULT '',
    default_time integer,
    countdown_time real DEFAULT '60',
    running boolean DEFAULT 'False',
    projection_ids integer[],
    used_as_list_of_speakers_countdown_meeting_id integer,
    used_as_poll_countdown_meeting_id integer,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS chat_groupT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    weight integer DEFAULT '10000',
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS chat_group_to_group (
    chat_group_id integer NOT NULL,
    group_id integer NOT NULL,
    read boolean DEFAULT 'True',
    write boolean DEFAULT 'False'
);


CREATE TABLE IF NOT EXISTS chat_message (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    content text NOT NULL,
    created timestamptz NOT NULL,
    user_id integer NOT NULL,
    chat_group_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS action_worker (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    state varchar(256) NOT NULL,
    created timestamptz NOT NULL,
    timestamp timestamptz NOT NULL,
    result jsonb
);

ALTER TABLE organizationT ADD FOREIGN KEY (theme_id) REFERENCES theme(id);
ALTER TABLE committee_to_user ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE committee_to_user ADD FOREIGN KEY (committee_id) REFERENCES committeeT(id);
ALTER TABLE group_to_user ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE group_to_user ADD FOREIGN KEY (group_id) REFERENCES groupT(id);
ALTER TABLE poll_to_user ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE poll_to_user ADD FOREIGN KEY (poll_id) REFERENCES poll(id);
ALTER TABLE meeting_user ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE meeting_user ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE meeting_user ADD FOREIGN KEY (vote_delegated_to_id) REFERENCES meeting_user(id);
ALTER TABLE organization_tag_to_committee_meeting ADD FOREIGN KEY (organization_tag_id) REFERENCES organization_tag(id);
ALTER TABLE organization_tag_to_committee_meeting ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE organization_tag_to_committee_meeting ADD FOREIGN KEY (committee_id) REFERENCES committeeT(id);
ALTER TABLE committeeT ADD FOREIGN KEY (default_meeting_id) REFERENCES meetingT(id);
ALTER TABLE committeeT ADD FOREIGN KEY (forwarding_user_id) REFERENCES userT(id);
ALTER TABLE forwarding_committee_to_committee ADD FOREIGN KEY (forwarding_committee_id) REFERENCES committeeT(id);
ALTER TABLE forwarding_committee_to_committee ADD FOREIGN KEY (receiving_committee_id) REFERENCES committeeT(id);
ALTER TABLE meetingT ADD FOREIGN KEY (motions_default_workflow_id) REFERENCES motion_workflow(id) INITIALLY DEFERRED;
ALTER TABLE meetingT ADD FOREIGN KEY (motions_default_amendment_workflow_id) REFERENCES motion_workflow(id) INITIALLY DEFERRED;
ALTER TABLE meetingT ADD FOREIGN KEY (motions_default_statute_amendment_workflow_id) REFERENCES motion_workflow(id) INITIALLY DEFERRED;
ALTER TABLE meetingT ADD FOREIGN KEY (logo_projector_main_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (logo_projector_header_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (logo_web_header_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (logo_pdf_header_l_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (logo_pdf_header_r_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (logo_pdf_footer_l_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (logo_pdf_footer_r_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (logo_pdf_ballot_paper_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (font_regular_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (font_italic_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (font_bold_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (font_bold_italic_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (font_monospace_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (font_chyron_speaker_name_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (font_projector_h1_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (font_projector_h2_id) REFERENCES mediafile(id);
ALTER TABLE meetingT ADD FOREIGN KEY (committee_id) REFERENCES committeeT(id);
ALTER TABLE meetingT ADD FOREIGN KEY (reference_projector_id) REFERENCES projector(id) INITIALLY DEFERRED;
ALTER TABLE meetingT ADD FOREIGN KEY (default_group_id) REFERENCES groupT(id) INITIALLY DEFERRED;
ALTER TABLE meetingT ADD FOREIGN KEY (admin_group_id) REFERENCES groupT(id) INITIALLY DEFERRED;
ALTER TABLE groupT ADD FOREIGN KEY (used_as_motion_poll_default_id) REFERENCES meetingT(id);
ALTER TABLE groupT ADD FOREIGN KEY (used_as_assignment_poll_default_id) REFERENCES meetingT(id);
ALTER TABLE groupT ADD FOREIGN KEY (used_as_topic_poll_default_id) REFERENCES meetingT(id);
ALTER TABLE groupT ADD FOREIGN KEY (used_as_poll_default_id) REFERENCES meetingT(id);
ALTER TABLE groupT ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE personal_note ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE personal_note ADD FOREIGN KEY (motion_id) REFERENCES motionT(id);
ALTER TABLE personal_note ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE tag ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE agenda_item ADD FOREIGN KEY (parent_id) REFERENCES agenda_item(id);
ALTER TABLE agenda_item ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE list_of_speakers ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE speaker ADD FOREIGN KEY (list_of_speakers_id) REFERENCES list_of_speakers(id);
ALTER TABLE speaker ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE topic ADD FOREIGN KEY (agenda_item_id) REFERENCES agenda_item(id);
ALTER TABLE topic ADD FOREIGN KEY (list_of_speakers_id) REFERENCES list_of_speakers(id);
ALTER TABLE topic ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motionT ADD FOREIGN KEY (lead_motion_id) REFERENCES motionT(id);
ALTER TABLE motionT ADD FOREIGN KEY (sort_parent_id) REFERENCES motionT(id);
ALTER TABLE motionT ADD FOREIGN KEY (origin_id) REFERENCES motionT(id);
ALTER TABLE motionT ADD FOREIGN KEY (origin_meeting_id) REFERENCES meetingT(id);
ALTER TABLE motionT ADD FOREIGN KEY (state_id) REFERENCES motion_state(id);
ALTER TABLE motionT ADD FOREIGN KEY (recommendation_id) REFERENCES motion_state(id);
ALTER TABLE motionT ADD FOREIGN KEY (category_id) REFERENCES motion_category(id);
ALTER TABLE motionT ADD FOREIGN KEY (block_id) REFERENCES motion_block(id);
ALTER TABLE motionT ADD FOREIGN KEY (statute_paragraph_id) REFERENCES motion_statute_paragraph(id);
ALTER TABLE motionT ADD FOREIGN KEY (agenda_item_id) REFERENCES agenda_item(id);
ALTER TABLE motionT ADD FOREIGN KEY (list_of_speakers_id) REFERENCES list_of_speakers(id);
ALTER TABLE motionT ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_submitter ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE motion_submitter ADD FOREIGN KEY (motion_id) REFERENCES motionT(id);
ALTER TABLE motion_submitter ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_comment ADD FOREIGN KEY (motion_id) REFERENCES motionT(id);
ALTER TABLE motion_comment ADD FOREIGN KEY (section_id) REFERENCES motion_comment_section(id);
ALTER TABLE motion_comment ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_category ADD FOREIGN KEY (parent_id) REFERENCES motion_category(id);
ALTER TABLE motion_category ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_block ADD FOREIGN KEY (agenda_item_id) REFERENCES agenda_item(id);
ALTER TABLE motion_block ADD FOREIGN KEY (list_of_speakers_id) REFERENCES list_of_speakers(id);
ALTER TABLE motion_block ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_change_recommendation ADD FOREIGN KEY (motion_id) REFERENCES motionT(id);
ALTER TABLE motion_change_recommendation ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_state ADD FOREIGN KEY (submitter_withdraw_state_id) REFERENCES motion_state(id);
ALTER TABLE motion_state ADD FOREIGN KEY (workflow_id) REFERENCES motion_workflow(id);
ALTER TABLE motion_state ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_state_to_state ADD FOREIGN KEY (previous_state_id) REFERENCES motion_state(id);
ALTER TABLE motion_state_to_state ADD FOREIGN KEY (next_state_id) REFERENCES motion_state(id);
ALTER TABLE motion_workflow ADD FOREIGN KEY (first_state_id) REFERENCES motion_state(id) INITIALLY DEFERRED;
ALTER TABLE motion_workflow ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_statute_paragraph ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE poll ADD FOREIGN KEY (global_option_id) REFERENCES option(id);
ALTER TABLE poll ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE option ADD FOREIGN KEY (poll_id) REFERENCES poll(id);
ALTER TABLE option ADD FOREIGN KEY (content_motion_id) REFERENCES motionT(id);
ALTER TABLE option ADD FOREIGN KEY (content_user_id) REFERENCES userT(id);
ALTER TABLE option ADD FOREIGN KEY (content_poll_candidate_list_id) REFERENCES poll_candidate_list(id);
ALTER TABLE vote ADD FOREIGN KEY (option_id) REFERENCES option(id);
ALTER TABLE vote ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE vote ADD FOREIGN KEY (delegated_user_id) REFERENCES userT(id);
ALTER TABLE assignment ADD FOREIGN KEY (agenda_item_id) REFERENCES agenda_item(id);
ALTER TABLE assignment ADD FOREIGN KEY (list_of_speakers_id) REFERENCES list_of_speakers(id);
ALTER TABLE assignment ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE assignment_candidate ADD FOREIGN KEY (assignment_id) REFERENCES assignment(id);
ALTER TABLE assignment_candidate ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE poll_candidate_list ADD FOREIGN KEY (option_id) REFERENCES option(id);
ALTER TABLE poll_candidate ADD FOREIGN KEY (poll_candidate_list_id) REFERENCES poll_candidate_list(id);
ALTER TABLE poll_candidate ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE mediafile ADD FOREIGN KEY (parent_id) REFERENCES mediafile(id);
ALTER TABLE mediafile ADD FOREIGN KEY (list_of_speakers_id) REFERENCES list_of_speakers(id);
ALTER TABLE mediafile ADD FOREIGN KEY (owner_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafile ADD FOREIGN KEY (owner_organization_id) REFERENCES organizationT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_agenda_all_items_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_topics_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_list_of_speakers_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_cur_list_of_speaker_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_motion_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_amendment_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_motion_block_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_assignment_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_mediafile_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_projector_message_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_projector_countdown_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_assignment_poll_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_motion_poll_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (used_as_default_projector_for_poll_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE projection ADD FOREIGN KEY (current_projector_id) REFERENCES projector(id);
ALTER TABLE projection ADD FOREIGN KEY (preview_projector_id) REFERENCES projector(id);
ALTER TABLE projection ADD FOREIGN KEY (history_projector_id) REFERENCES projector(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_motion_id) REFERENCES motionT(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_mediafile_id) REFERENCES mediafile(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_list_of_speakers_id) REFERENCES list_of_speakers(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_motion_block_id) REFERENCES motion_block(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_assignment_id) REFERENCES assignment(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_agenda_item_id) REFERENCES agenda_item(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_topic_id) REFERENCES topic(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_poll_id) REFERENCES poll(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_projector_message_id) REFERENCES projector_message(id);
ALTER TABLE projection ADD FOREIGN KEY (projection_projector_countdown_id) REFERENCES projector_countdown(id);
ALTER TABLE projection ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector_message ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector_countdown ADD FOREIGN KEY (used_as_list_of_speakers_countdown_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector_countdown ADD FOREIGN KEY (used_as_poll_countdown_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector_countdown ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE chat_group_to_group ADD FOREIGN KEY (chat_group_id) REFERENCES chat_groupT(id);
ALTER TABLE chat_group_to_group ADD FOREIGN KEY (group_id) REFERENCES groupT(id);
ALTER TABLE chat_message ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE chat_message ADD FOREIGN KEY (chat_group_id) REFERENCES chat_groupT(id);

CREATE OR REPLACE VIEW organization AS SELECT *,
(select array_agg(c.id) from committeeT c) as committee_ids,
(select array_agg(m.id) from meetingT m where m.state = 'active') as active_meeting_ids,
(select array_agg(m.id) from meetingT m where m.state = 'archived') as archived_meeting_ids,
(select array_agg(m.id) from meetingT m where m.template_for_organization) as template_meeting_ids
FROM organizationT o;


CREATE OR REPLACE VIEW user_ AS SELECT *,
(select array_agg(committee_id) from (
    select m.committee_id as committee_id from group_to_user gtu
      join groupT g on g.id = gtu.group_id
      join meetingT m on m.id = g.meeting_id
      where gtu.user_id = u.id
    union
    select ctu.committee_id as committee_id from committee_to_user ctu where ctu.user_id = u.id
  ) as cs) as committee_ids,
(select array_agg(g.meeting_id) from group_to_user gtu join groupT g on g.id = gtu.group_id where gtu.user_id = u.id) as meeting_ids
FROM userT u;


CREATE OR REPLACE VIEW committee AS SELECT *,
(select array_agg(f.receiving_committee_id) from forwarding_committee_to_committee f where f.forwarding_committee_id = c.id) as forward_to_committee_ids,
(select array_agg(f.forwarding_committee_id) from forwarding_committee_to_committee f where f.receiving_committee_id = c.id) as receive_from_committee_ids,
(select array_agg(user_id) from (
  select gtu.user_id as user_id from meetingT m
    join groupT g on g.meeting_id = m.id
    join group_to_user gtu on gtu.group_id = g.id
    where m.committee_id = c.id
  union
  select ctu.user_id as user_id from committee_to_user ctu where ctu.committee_id = c.id
) as x) as user_ids
FROM committeeT c;


CREATE OR REPLACE VIEW meeting AS SELECT *,
(select array_agg(gtu.user_id) from groupT g join group_to_user gtu on gtu.group_id = g.id where g.meeting_id = m.id) as user_ids
FROM meetingT m;


CREATE OR REPLACE VIEW group_ AS SELECT *,
(select m.id from meetingT m where m.default_group_id = g.id) as default_group_for_meeting_id,
(select m.id from meetingT m where m.admin_group_id = g.id) as admin_group_for_meeting_id,
(select array_agg(gtg.chat_group_id) from chat_group_to_group gtg where gtg.group_id = g.id and gtg.read) as read_chat_group_ids,
(select array_agg(gtg.chat_group_id) from chat_group_to_group gtg where gtg.group_id = g.id and gtg.write) as write_chat_group_ids
FROM groupT g;


CREATE OR REPLACE VIEW chat_group AS SELECT *,
(select array_agg(m.id) from chat_message m where m.chat_group_id = cg.id) as chat_message_ids,
(select array_agg(gtg.group_id) from chat_group_to_group gtg where gtg.chat_group_id = cg.id and gtg.read) as read_group_ids,
(select array_agg(gtg.group_id) from chat_group_to_group gtg where gtg.chat_group_id = cg.id and gtg.write) as write_group_ids
FROM chat_groupT cg;

