
-- schema.sql for initial database setup OpenSlides
-- Code generated. DO NOT EDIT.

-- MODELS_YML_CHECKSUM = 'ca4dea3322316872a715c50ad7e67a20'

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
    limit_of_meetings integer,
    limit_of_users integer,
    theme_id integer NOT NULL,
    users_email_sender varchar(50),
    users_email_replyto varchar(50),
    users_email_subject varchar(50),
    users_email_body text,
    url varchar(50)
);


CREATE TABLE IF NOT EXISTS userT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    username varchar(50) NOT NULL,
    pronoun varchar(50),
    title varchar(50),
    first_name varchar(50),
    last_name varchar(50),
    is_active boolean,
    is_physical_person boolean,
    password varchar(50),
    default_password varchar(50),
    can_change_own_password boolean,
    gender varchar(50),
    email varchar(50),
    default_number varchar(50),
    default_structure_level varchar(50),
    default_vote_weight decimal(6),
    last_email_send timestamptz,
    is_demo_user boolean,
    last_login timestamptz
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
    number varchar(50),
    structure_level varchar(50),
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
    name varchar(50) NOT NULL,
    color varchar(7) NOT NULL,
    tagged_ids varchar(50)[]
);


CREATE TABLE IF NOT EXISTS organization_tag_to_committee_meeting (
    organization_tag_id integer NOT NULL,
    meeting_id integer,
    committee_id integer
);


CREATE TABLE IF NOT EXISTS theme (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(50) NOT NULL,
    accent_100 varchar(7),
    accent_200 varchar(7),
    accent_300 varchar(7),
    accent_400 varchar(7),
    accent_50 varchar(7),
    accent_500 varchar(7) NOT NULL,
    accent_600 varchar(7),
    accent_700 varchar(7),
    accent_800 varchar(7),
    accent_900 varchar(7),
    accent_a100 varchar(7),
    accent_a200 varchar(7),
    accent_a400 varchar(7),
    accent_a700 varchar(7),
    primary_100 varchar(7),
    primary_200 varchar(7),
    primary_300 varchar(7),
    primary_400 varchar(7),
    primary_50 varchar(7),
    primary_500 varchar(7) NOT NULL,
    primary_600 varchar(7),
    primary_700 varchar(7),
    primary_800 varchar(7),
    primary_900 varchar(7),
    primary_a100 varchar(7),
    primary_a200 varchar(7),
    primary_a400 varchar(7),
    primary_a700 varchar(7),
    warn_100 varchar(7),
    warn_200 varchar(7),
    warn_300 varchar(7),
    warn_400 varchar(7),
    warn_50 varchar(7),
    warn_500 varchar(7) NOT NULL,
    warn_600 varchar(7),
    warn_700 varchar(7),
    warn_800 varchar(7),
    warn_900 varchar(7),
    warn_a100 varchar(7),
    warn_a200 varchar(7),
    warn_a400 varchar(7),
    warn_a700 varchar(7),
    headbar varchar(7),
    yes varchar(7),
    no varchar(7),
    abstain varchar(7),
    theme_for_organization_id integer
);


CREATE TABLE IF NOT EXISTS committee (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(50) NOT NULL,
    description text,
    meeting_ids integer[],
    default_meeting_id integer,
    user_ids integer[],
    manager_ids integer[],
    forwarding_user_id integer,
    organization_tag_ids integer[]
);


CREATE TABLE IF NOT EXISTS forwarding_committee_to_committee (
    forwarding_committee_id integer NOT NULL,
    receiving_committee_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS meetingT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    welcome_title varchar(50),
    welcome_text text,
    name varchar(50),
    state varchar(50),
    description varchar(50),
    location varchar(50),
    start_time timestamptz,
    end_time timestamptz,
    imported_at timestamptz,
    jitsi_domain varchar(50),
    jitsi_room_name varchar(50),
    jitsi_room_password varchar(50),
    template_for_organization_id integer,
    enable_anonymous boolean,
    custom_translations jsonb,
    conference_show boolean,
    conference_auto_connect boolean,
    conference_los_restriction boolean,
    conference_stream_url varchar(50),
    conference_stream_poster_url varchar(50),
    conference_open_microphone boolean,
    conference_open_video boolean,
    conference_auto_connect_next_speakers integer,
    conference_enable_helpdesk boolean,
    applause_enable boolean,
    applause_type varchar(50),
    applause_show_level boolean,
    applause_min_amount integer,
    applause_max_amount integer,
    applause_timeout integer,
    applause_particle_image_url varchar(50),
    projector_countdown_default_time integer NOT NULL,
    projector_countdown_warning_time integer NOT NULL,
    export_csv_encoding varchar(50),
    export_csv_separator varchar(50),
    export_pdf_pagenumber_alignment varchar(50),
    export_pdf_fontsize integer,
    export_pdf_line_height real,
    export_pdf_page_margin_left integer,
    export_pdf_page_margin_top integer,
    export_pdf_page_margin_right integer,
    export_pdf_page_margin_bottom integer,
    export_pdf_pagesize varchar(50),
    agenda_show_subtitles boolean,
    agenda_enable_numbering boolean,
    agenda_number_prefix varchar(50),
    agenda_numeral_system varchar(50),
    agenda_item_creation varchar(50),
    agenda_new_items_default_visibility varchar(50),
    agenda_show_internal_items_on_projector boolean,
    list_of_speakers_amount_last_on_projector integer,
    list_of_speakers_amount_next_on_projector integer,
    list_of_speakers_couple_countdown boolean,
    list_of_speakers_show_amount_of_speakers_on_slide boolean,
    list_of_speakers_present_users_only boolean,
    list_of_speakers_show_first_contribution boolean,
    list_of_speakers_enable_point_of_order_speakers boolean,
    list_of_speakers_enable_pro_contra_speech boolean,
    list_of_speakers_can_set_contribution_self boolean,
    list_of_speakers_speaker_note_for_everyone boolean,
    list_of_speakers_initially_closed boolean,
    motions_default_workflow_id integer NOT NULL,
    motions_default_amendment_workflow_id integer NOT NULL,
    motions_default_statute_amendment_workflow_id integer NOT NULL,
    motions_preamble text,
    motions_default_line_numbering varchar(50),
    motions_line_length integer,
    motions_reason_required boolean,
    motions_enable_text_on_projector boolean,
    motions_enable_reason_on_projector boolean,
    motions_enable_sidebox_on_projector boolean,
    motions_enable_recommendation_on_projector boolean,
    motions_show_referring_motions boolean,
    motions_show_sequential_number boolean,
    motions_recommendations_by varchar(50),
    motions_block_slide_columns integer,
    motions_statute_recommendations_by varchar(50),
    motions_recommendation_text_mode varchar(50),
    motions_default_sorting varchar(50),
    motions_number_type varchar(50),
    motions_number_min_digits integer,
    motions_number_with_blank boolean,
    motions_statutes_enabled boolean,
    motions_amendments_enabled boolean,
    motions_amendments_in_main_list boolean,
    motions_amendments_of_amendments boolean,
    motions_amendments_prefix varchar(50),
    motions_amendments_text_mode varchar(50),
    motions_amendments_multiple_paragraphs boolean,
    motions_supporters_min_amount integer,
    motions_export_title varchar(50),
    motions_export_preamble text,
    motions_export_submitter_recommendation boolean,
    motions_export_follow_recommendation boolean,
    motion_poll_ballot_paper_selection varchar(50),
    motion_poll_ballot_paper_number integer,
    motion_poll_default_type varchar(50),
    motion_poll_default_100_percent_base varchar(50),
    motion_poll_default_backend varchar(50),
    users_enable_presence_view boolean,
    users_enable_vote_weight boolean,
    users_allow_self_set_present boolean,
    users_pdf_welcometitle varchar(50),
    users_pdf_welcometext text,
    users_pdf_wlan_ssid varchar(50),
    users_pdf_wlan_password varchar(50),
    users_pdf_wlan_encryption varchar(50),
    users_email_sender varchar(50),
    users_email_replyto varchar(50),
    users_email_subject varchar(50),
    users_email_body text,
    users_enable_vote_delegations boolean,
    assignments_export_title varchar(50),
    assignments_export_preamble text,
    assignment_poll_ballot_paper_selection varchar(50),
    assignment_poll_ballot_paper_number integer,
    assignment_poll_add_candidates_to_list_of_speakers boolean,
    assignment_poll_enable_max_votes_per_option boolean,
    assignment_poll_sort_poll_result_by_votes boolean,
    assignment_poll_default_type varchar(50),
    assignment_poll_default_method varchar(50),
    assignment_poll_default_100_percent_base varchar(50),
    assignment_poll_default_backend varchar(50),
    poll_ballot_paper_selection varchar(50),
    poll_ballot_paper_number integer,
    poll_sort_poll_result_by_votes boolean,
    poll_default_type varchar(50),
    poll_default_method varchar(50),
    poll_default_100_percent_base varchar(50),
    poll_default_backend varchar(50),
    poll_couple_countdown boolean,
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
    name varchar(50) NOT NULL,
    permissions varchar(50)[],
    weight integer,
    mediafile_access_group_ids integer[],
    mediafile_inherited_access_group_ids integer[],
    read_comment_section_ids integer[],
    write_comment_section_ids integer[],
    read_chat_group_ids integer[],
    write_chat_group_ids integer[],
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
    content_object_id integer,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS tag (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(50) NOT NULL,
    tagged_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS agenda_item (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    item_number varchar(50),
    comment varchar(50),
    closed boolean,
    type varchar(50),
    duration integer,
    is_internal boolean,
    is_hidden boolean,
    level integer,
    weight integer,
    content_object_id integer NOT NULL,
    parent_id integer,
    tag_ids integer[],
    projection_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS list_of_speakers (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    closed boolean,
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
    weight integer,
    speech_state varchar(50),
    note varchar(50),
    point_of_order boolean,
    list_of_speakers_id integer NOT NULL,
    user_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS topic (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(50) NOT NULL,
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


CREATE TABLE IF NOT EXISTS motion (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    number varchar(50),
    number_value integer,
    sequential_number integer NOT NULL,
    title varchar(50) NOT NULL,
    text text,
    amendment_paragraph jsonb,
    modified_final_version text,
    reason text,
    category_weight integer,
    state_extension varchar(50),
    recommendation_extension varchar(50),
    sort_weight integer,
    created timestamptz,
    last_modified timestamptz,
    start_line_number integer,
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
    name varchar(50) NOT NULL,
    weight integer,
    sequential_number integer NOT NULL,
    submitter_can_write boolean,
    comment_ids integer[],
    read_group_ids integer[],
    write_group_ids integer[]
);


CREATE TABLE IF NOT EXISTS motion_category (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(50) NOT NULL,
    prefix varchar(50),
    weight integer,
    level integer,
    sequential_number integer NOT NULL,
    parent_id integer,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_block (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(50) NOT NULL,
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
    rejected boolean,
    internal boolean,
    type varchar(50),
    other_description varchar(50),
    line_from integer,
    line_to integer,
    text text,
    creation_time timestamptz,
    motion_id integer NOT NULL,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_state (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(50) NOT NULL,
    weight integer NOT NULL,
    recommendation_label varchar(50),
    css_class varchar(50) NOT NULL,
    restrictions varchar(50)[],
    allow_support boolean,
    allow_create_poll boolean,
    allow_submitter_edit boolean,
    set_number boolean,
    show_state_extension_field boolean,
    show_recommendation_extension_field boolean,
    merge_amendment_into_final varchar(50),
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


CREATE TABLE IF NOT EXISTS motion_workflow (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(50) NOT NULL,
    sequential_number integer NOT NULL,
    state_ids integer[],
    first_state_id integer NOT NULL,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS motion_statute_paragraph (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(50) NOT NULL,
    text text,
    weight integer,
    sequential_number integer NOT NULL,
    motion_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS poll (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    description text,
    title varchar(50) NOT NULL,
    type varchar(50) NOT NULL,
    backend varchar(50) NOT NULL,
    is_pseudoanonymized boolean,
    pollmethod varchar(50) NOT NULL,
    state varchar(50),
    min_votes_amount integer,
    max_votes_amount integer,
    max_votes_per_option integer,
    global_yes boolean,
    global_no boolean,
    global_abstain boolean,
    onehundred_percent_base varchar(50) NOT NULL,
    votesvalid decimal(6),
    votesinvalid decimal(6),
    votescast decimal(6),
    entitled_users_at_stop jsonb,
    sequential_number integer NOT NULL,
    crypt_key varchar(50),
    crypt_signature varchar(50),
    votes_raw text,
    votes_signature varchar(50),
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
    weight integer,
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
    value varchar(50),
    user_token varchar(50) NOT NULL,
    option_id integer NOT NULL,
    user_id integer,
    delegated_user_id integer
);


CREATE TABLE IF NOT EXISTS assignment (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(50) NOT NULL,
    description text,
    open_posts integer,
    phase varchar(50),
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
    weight integer,
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
    title varchar(50),
    is_directory boolean,
    filesize integer,
    filename varchar(50),
    mimetype varchar(50),
    pdf_information jsonb,
    create_timestamp timestamptz,
    is_public boolean NOT NULL,
    token varchar(50),
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
    name varchar(50),
    scale integer,
    scroll integer,
    width integer,
    aspect_ratio_numerator integer,
    aspect_ratio_denominator integer,
    color varchar(7),
    background_color varchar(7),
    header_background_color varchar(7),
    header_font_color varchar(7),
    header_h1_color varchar(7),
    chyron_background_color varchar(7),
    chyron_font_color varchar(7),
    show_header_footer boolean,
    show_title boolean,
    show_logo boolean,
    show_clock boolean,
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
    stable boolean,
    weight integer,
    type varchar(50),
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
    title varchar(50) NOT NULL,
    description varchar(50),
    default_time integer,
    countdown_time real,
    running boolean,
    projection_ids integer[],
    used_as_list_of_speakers_countdown_meeting_id integer,
    used_as_poll_countdown_meeting_id integer,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS chat_group (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(50) NOT NULL,
    weight integer,
    chat_message_ids integer[],
    read_group_ids integer[],
    write_group_ids integer[],
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS chat_message (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    content text NOT NULL,
    created timestamptz NOT NULL,
    user_id integer NOT NULL,
    chat_group_id integer NOT NULL,
    meeting_id integer NOT NULL
);


CREATE TABLE IF NOT EXISTS action_worker (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(50) NOT NULL,
    state varchar(50) NOT NULL,
    created timestamptz NOT NULL,
    timestamp timestamptz NOT NULL,
    result jsonb
);

ALTER TABLE organizationT ADD FOREIGN KEY (theme_id) REFERENCES theme(id);
ALTER TABLE poll_to_user ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE poll_to_user ADD FOREIGN KEY (poll_id) REFERENCES poll(id);
ALTER TABLE meeting_user ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE meeting_user ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE meeting_user ADD FOREIGN KEY (vote_delegated_to_id) REFERENCES meeting_user(id);
ALTER TABLE organization_tag_to_committee_meeting ADD FOREIGN KEY (organization_tag_id) REFERENCES organization_tag(id);
ALTER TABLE organization_tag_to_committee_meeting ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE organization_tag_to_committee_meeting ADD FOREIGN KEY (committee_id) REFERENCES committee(id);
ALTER TABLE theme ADD FOREIGN KEY (theme_for_organization_id) REFERENCES organizationT(id);
ALTER TABLE committee ADD FOREIGN KEY (default_meeting_id) REFERENCES meetingT(id);
ALTER TABLE committee ADD FOREIGN KEY (forwarding_user_id) REFERENCES userT(id);
ALTER TABLE forwarding_committee_to_committee ADD FOREIGN KEY (forwarding_committee_id) REFERENCES committee(id);
ALTER TABLE forwarding_committee_to_committee ADD FOREIGN KEY (receiving_committee_id) REFERENCES committee(id);
ALTER TABLE meetingT ADD FOREIGN KEY (template_for_organization_id) REFERENCES organizationT(id);
ALTER TABLE meetingT ADD FOREIGN KEY (motions_default_workflow_id) REFERENCES motion_workflow(id);
ALTER TABLE meetingT ADD FOREIGN KEY (motions_default_amendment_workflow_id) REFERENCES motion_workflow(id);
ALTER TABLE meetingT ADD FOREIGN KEY (motions_default_statute_amendment_workflow_id) REFERENCES motion_workflow(id);
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
ALTER TABLE meetingT ADD FOREIGN KEY (committee_id) REFERENCES committee(id);
ALTER TABLE meetingT ADD FOREIGN KEY (reference_projector_id) REFERENCES projector(id);
ALTER TABLE meetingT ADD FOREIGN KEY (default_group_id) REFERENCES groupT(id);
ALTER TABLE meetingT ADD FOREIGN KEY (admin_group_id) REFERENCES groupT(id);
ALTER TABLE groupT ADD FOREIGN KEY (used_as_motion_poll_default_id) REFERENCES meetingT(id);
ALTER TABLE groupT ADD FOREIGN KEY (used_as_assignment_poll_default_id) REFERENCES meetingT(id);
ALTER TABLE groupT ADD FOREIGN KEY (used_as_topic_poll_default_id) REFERENCES meetingT(id);
ALTER TABLE groupT ADD FOREIGN KEY (used_as_poll_default_id) REFERENCES meetingT(id);
ALTER TABLE groupT ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE personal_note ADD FOREIGN KEY (user_id) REFERENCES userT(id);
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
ALTER TABLE motion ADD FOREIGN KEY (lead_motion_id) REFERENCES motion(id);
ALTER TABLE motion ADD FOREIGN KEY (sort_parent_id) REFERENCES motion(id);
ALTER TABLE motion ADD FOREIGN KEY (origin_id) REFERENCES motion(id);
ALTER TABLE motion ADD FOREIGN KEY (origin_meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion ADD FOREIGN KEY (state_id) REFERENCES motion_state(id);
ALTER TABLE motion ADD FOREIGN KEY (recommendation_id) REFERENCES motion_state(id);
ALTER TABLE motion ADD FOREIGN KEY (category_id) REFERENCES motion_category(id);
ALTER TABLE motion ADD FOREIGN KEY (block_id) REFERENCES motion_block(id);
ALTER TABLE motion ADD FOREIGN KEY (statute_paragraph_id) REFERENCES motion_statute_paragraph(id);
ALTER TABLE motion ADD FOREIGN KEY (agenda_item_id) REFERENCES agenda_item(id);
ALTER TABLE motion ADD FOREIGN KEY (list_of_speakers_id) REFERENCES list_of_speakers(id);
ALTER TABLE motion ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_submitter ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE motion_submitter ADD FOREIGN KEY (motion_id) REFERENCES motion(id);
ALTER TABLE motion_submitter ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_comment ADD FOREIGN KEY (motion_id) REFERENCES motion(id);
ALTER TABLE motion_comment ADD FOREIGN KEY (section_id) REFERENCES motion_comment_section(id);
ALTER TABLE motion_comment ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_category ADD FOREIGN KEY (parent_id) REFERENCES motion_category(id);
ALTER TABLE motion_category ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_block ADD FOREIGN KEY (agenda_item_id) REFERENCES agenda_item(id);
ALTER TABLE motion_block ADD FOREIGN KEY (list_of_speakers_id) REFERENCES list_of_speakers(id);
ALTER TABLE motion_block ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_change_recommendation ADD FOREIGN KEY (motion_id) REFERENCES motion(id);
ALTER TABLE motion_change_recommendation ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_state ADD FOREIGN KEY (submitter_withdraw_state_id) REFERENCES motion_state(id);
ALTER TABLE motion_state ADD FOREIGN KEY (workflow_id) REFERENCES motion_workflow(id);
ALTER TABLE motion_state ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_workflow ADD FOREIGN KEY (first_state_id) REFERENCES motion_state(id);
ALTER TABLE motion_workflow ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE motion_statute_paragraph ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE poll ADD FOREIGN KEY (global_option_id) REFERENCES option(id);
ALTER TABLE poll ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);
ALTER TABLE option ADD FOREIGN KEY (poll_id) REFERENCES poll(id);
ALTER TABLE option ADD FOREIGN KEY (content_motion_id) REFERENCES motion(id);
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
ALTER TABLE projection ADD FOREIGN KEY (projection_motion_id) REFERENCES motion(id);
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
ALTER TABLE chat_message ADD FOREIGN KEY (user_id) REFERENCES userT(id);
ALTER TABLE chat_message ADD FOREIGN KEY (chat_group_id) REFERENCES chat_group(id);
ALTER TABLE chat_message ADD FOREIGN KEY (meeting_id) REFERENCES meetingT(id);

CREATE OR REPLACE VIEW organization AS SELECT id
FROM organizationT c;


CREATE OR REPLACE VIEW user_ AS SELECT id
FROM userT c;


CREATE OR REPLACE VIEW committeeV AS SELECT id,
(select array_agg(f.receiving_committee_id) from forwarding_committee_to_committee f where f.forwarding_committee_id = c.id) as forward_to_committee_ids,
(select array_agg(f.forwarding_committee_id) from forwarding_committee_to_committee f where f.receiving_committee_id = c.id) as receive_from_committee_ids
FROM committee c;


CREATE OR REPLACE VIEW meeting AS SELECT id
FROM meetingT c;


CREATE OR REPLACE VIEW group_ AS SELECT id
FROM groupT c;

