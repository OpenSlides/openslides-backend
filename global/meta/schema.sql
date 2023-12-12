
-- schema.sql for initial database setup OpenSlides
-- Code generated. DO NOT EDIT.

-- MODELS_YML_CHECKSUM = '2117dc6643bb235c645c1f21ff5cd1ee'
-- Type definitions
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_organization_default_language') THEN
        CREATE TYPE enum_organization_default_language AS ENUM ('en', 'de', 'it', 'es', 'ru', 'cs');
    ELSE
        RAISE NOTICE 'type "enum_organization_default_language" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_user_organization_management_level') THEN
        CREATE TYPE enum_user_organization_management_level AS ENUM ('superadmin', 'can_manage_organization', 'can_manage_users');
    ELSE
        RAISE NOTICE 'type "enum_user_organization_management_level" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_language') THEN
        CREATE TYPE enum_meeting_language AS ENUM ('en', 'de', 'it', 'es', 'ru', 'cs');
    ELSE
        RAISE NOTICE 'type "enum_meeting_language" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_applause_type') THEN
        CREATE TYPE enum_meeting_applause_type AS ENUM ('applause-type-bar', 'applause-type-particles');
    ELSE
        RAISE NOTICE 'type "enum_meeting_applause_type" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_export_csv_encoding') THEN
        CREATE TYPE enum_meeting_export_csv_encoding AS ENUM ('utf-8', 'iso-8859-15');
    ELSE
        RAISE NOTICE 'type "enum_meeting_export_csv_encoding" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_export_pdf_pagenumber_alignment') THEN
        CREATE TYPE enum_meeting_export_pdf_pagenumber_alignment AS ENUM ('left', 'right', 'center');
    ELSE
        RAISE NOTICE 'type "enum_meeting_export_pdf_pagenumber_alignment" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_export_pdf_fontsize') THEN
        CREATE TYPE enum_meeting_export_pdf_fontsize AS ENUM ('10', '11', '12');
    ELSE
        RAISE NOTICE 'type "enum_meeting_export_pdf_fontsize" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_export_pdf_pagesize') THEN
        CREATE TYPE enum_meeting_export_pdf_pagesize AS ENUM ('A4', 'A5');
    ELSE
        RAISE NOTICE 'type "enum_meeting_export_pdf_pagesize" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_agenda_numeral_system') THEN
        CREATE TYPE enum_meeting_agenda_numeral_system AS ENUM ('arabic', 'roman');
    ELSE
        RAISE NOTICE 'type "enum_meeting_agenda_numeral_system" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_agenda_item_creation') THEN
        CREATE TYPE enum_meeting_agenda_item_creation AS ENUM ('always', 'never', 'default_yes', 'default_no');
    ELSE
        RAISE NOTICE 'type "enum_meeting_agenda_item_creation" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_agenda_new_items_default_visibility') THEN
        CREATE TYPE enum_meeting_agenda_new_items_default_visibility AS ENUM ('common', 'internal', 'hidden');
    ELSE
        RAISE NOTICE 'type "enum_meeting_agenda_new_items_default_visibility" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_motions_default_line_numbering') THEN
        CREATE TYPE enum_meeting_motions_default_line_numbering AS ENUM ('outside', 'inline', 'none');
    ELSE
        RAISE NOTICE 'type "enum_meeting_motions_default_line_numbering" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_motions_recommendation_text_mode') THEN
        CREATE TYPE enum_meeting_motions_recommendation_text_mode AS ENUM ('original', 'changed', 'diff', 'agreed');
    ELSE
        RAISE NOTICE 'type "enum_meeting_motions_recommendation_text_mode" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_motions_default_sorting') THEN
        CREATE TYPE enum_meeting_motions_default_sorting AS ENUM ('number', 'weight');
    ELSE
        RAISE NOTICE 'type "enum_meeting_motions_default_sorting" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_motions_number_type') THEN
        CREATE TYPE enum_meeting_motions_number_type AS ENUM ('per_category', 'serially_numbered', 'manually');
    ELSE
        RAISE NOTICE 'type "enum_meeting_motions_number_type" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_motions_amendments_text_mode') THEN
        CREATE TYPE enum_meeting_motions_amendments_text_mode AS ENUM ('freestyle', 'fulltext', 'paragraph');
    ELSE
        RAISE NOTICE 'type "enum_meeting_motions_amendments_text_mode" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_motion_poll_ballot_paper_selection') THEN
        CREATE TYPE enum_meeting_motion_poll_ballot_paper_selection AS ENUM ('NUMBER_OF_DELEGATES', 'NUMBER_OF_ALL_PARTICIPANTS', 'CUSTOM_NUMBER');
    ELSE
        RAISE NOTICE 'type "enum_meeting_motion_poll_ballot_paper_selection" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_motion_poll_default_backend') THEN
        CREATE TYPE enum_meeting_motion_poll_default_backend AS ENUM ('long', 'fast');
    ELSE
        RAISE NOTICE 'type "enum_meeting_motion_poll_default_backend" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_users_pdf_wlan_encryption') THEN
        CREATE TYPE enum_meeting_users_pdf_wlan_encryption AS ENUM ('', 'WEP', 'WPA', 'nopass');
    ELSE
        RAISE NOTICE 'type "enum_meeting_users_pdf_wlan_encryption" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_assignment_poll_ballot_paper_selection') THEN
        CREATE TYPE enum_meeting_assignment_poll_ballot_paper_selection AS ENUM ('NUMBER_OF_DELEGATES', 'NUMBER_OF_ALL_PARTICIPANTS', 'CUSTOM_NUMBER');
    ELSE
        RAISE NOTICE 'type "enum_meeting_assignment_poll_ballot_paper_selection" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_assignment_poll_default_backend') THEN
        CREATE TYPE enum_meeting_assignment_poll_default_backend AS ENUM ('long', 'fast');
    ELSE
        RAISE NOTICE 'type "enum_meeting_assignment_poll_default_backend" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_poll_ballot_paper_selection') THEN
        CREATE TYPE enum_meeting_poll_ballot_paper_selection AS ENUM ('NUMBER_OF_DELEGATES', 'NUMBER_OF_ALL_PARTICIPANTS', 'CUSTOM_NUMBER');
    ELSE
        RAISE NOTICE 'type "enum_meeting_poll_ballot_paper_selection" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_meeting_poll_default_backend') THEN
        CREATE TYPE enum_meeting_poll_default_backend AS ENUM ('long', 'fast');
    ELSE
        RAISE NOTICE 'type "enum_meeting_poll_default_backend" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_group_permissions') THEN
        CREATE TYPE enum_group_permissions AS ENUM ('agenda_item.can_manage', 'agenda_item.can_see', 'agenda_item.can_see_internal', 'assignment.can_manage', 'assignment.can_nominate_other', 'assignment.can_nominate_self', 'assignment.can_see', 'chat.can_manage', 'list_of_speakers.can_be_speaker', 'list_of_speakers.can_manage', 'list_of_speakers.can_see', 'mediafile.can_manage', 'mediafile.can_see', 'meeting.can_manage_logos_and_fonts', 'meeting.can_manage_settings', 'meeting.can_see_autopilot', 'meeting.can_see_frontpage', 'meeting.can_see_history', 'meeting.can_see_livestream', 'motion.can_create', 'motion.can_create_amendments', 'motion.can_forward', 'motion.can_manage', 'motion.can_manage_metadata', 'motion.can_manage_polls', 'motion.can_see', 'motion.can_see_internal', 'motion.can_support', 'poll.can_manage', 'projector.can_manage', 'projector.can_see', 'tag.can_manage', 'user.can_manage', 'user.can_manage_presence', 'user.can_see');
    ELSE
        RAISE NOTICE 'type "enum_group_permissions" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_agenda_item_type') THEN
        CREATE TYPE enum_agenda_item_type AS ENUM ('common', 'internal', 'hidden');
    ELSE
        RAISE NOTICE 'type "enum_agenda_item_type" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_speaker_speech_state') THEN
        CREATE TYPE enum_speaker_speech_state AS ENUM ('contribution', 'pro', 'contra');
    ELSE
        RAISE NOTICE 'type "enum_speaker_speech_state" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_motion_change_recommendation_type') THEN
        CREATE TYPE enum_motion_change_recommendation_type AS ENUM ('replacement', 'insertion', 'deletion', 'other');
    ELSE
        RAISE NOTICE 'type "enum_motion_change_recommendation_type" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_motion_state_css_class') THEN
        CREATE TYPE enum_motion_state_css_class AS ENUM ('grey', 'red', 'green', 'lightblue', 'yellow');
    ELSE
        RAISE NOTICE 'type "enum_motion_state_css_class" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_motion_state_restrictions') THEN
        CREATE TYPE enum_motion_state_restrictions AS ENUM ('motion.can_see_internal', 'motion.can_manage_metadata', 'motion.can_manage', 'is_submitter');
    ELSE
        RAISE NOTICE 'type "enum_motion_state_restrictions" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_motion_state_merge_amendment_into_final') THEN
        CREATE TYPE enum_motion_state_merge_amendment_into_final AS ENUM ('do_not_merge', 'undefined', 'do_merge');
    ELSE
        RAISE NOTICE 'type "enum_motion_state_merge_amendment_into_final" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_poll_type') THEN
        CREATE TYPE enum_poll_type AS ENUM ('analog', 'named', 'pseudoanonymous', 'cryptographic');
    ELSE
        RAISE NOTICE 'type "enum_poll_type" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_poll_backend') THEN
        CREATE TYPE enum_poll_backend AS ENUM ('long', 'fast');
    ELSE
        RAISE NOTICE 'type "enum_poll_backend" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_poll_pollmethod') THEN
        CREATE TYPE enum_poll_pollmethod AS ENUM ('Y', 'YN', 'YNA', 'N');
    ELSE
        RAISE NOTICE 'type "enum_poll_pollmethod" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_poll_state') THEN
        CREATE TYPE enum_poll_state AS ENUM ('created', 'started', 'finished', 'published');
    ELSE
        RAISE NOTICE 'type "enum_poll_state" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_poll_onehundred_percent_base') THEN
        CREATE TYPE enum_poll_onehundred_percent_base AS ENUM ('Y', 'YN', 'YNA', 'N', 'valid', 'cast', 'entitled', 'disabled');
    ELSE
        RAISE NOTICE 'type "enum_poll_onehundred_percent_base" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_assignment_phase') THEN
        CREATE TYPE enum_assignment_phase AS ENUM ('search', 'voting', 'finished');
    ELSE
        RAISE NOTICE 'type "enum_assignment_phase" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_action_worker_state') THEN
        CREATE TYPE enum_action_worker_state AS ENUM ('running', 'end', 'aborted');
    ELSE
        RAISE NOTICE 'type "enum_action_worker_state" already exists, skipping';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enum_import_preview_state') THEN
        CREATE TYPE enum_import_preview_state AS ENUM ('warning', 'error', 'done');
    ELSE
        RAISE NOTICE 'type "enum_import_preview_state" already exists, skipping';
    END IF;
END$$;


-- Table definitions
CREATE TABLE IF NOT EXISTS organizationT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256),
    description text,
    legal_notice text,
    privacy_policy text,
    login_text text,
    reset_password_verbose_errors boolean,
    genders varchar(256)[] DEFAULT '{"male", "female", "diverse", "non-binary"}',
    enable_electronic_voting boolean,
    enable_chat boolean,
    limit_of_meetings integer CONSTRAINT minimum_limit_of_meetings CHECK (limit_of_meetings >= 0) DEFAULT 0,
    limit_of_users integer CONSTRAINT minimum_limit_of_users CHECK (limit_of_users >= 0) DEFAULT 0,
    default_language enum_organization_default_language NOT NULL,
    saml_enabled boolean,
    saml_login_button_text varchar(256) DEFAULT 'SAML login',
    saml_attr_mapping jsonb,
    saml_metadata_idp text,
    saml_metadata_sp text,
    saml_private_key text,
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



comment on column organizationT.limit_of_meetings is 'Maximum of active meetings for the whole organization. 0 means no limitation at all';
comment on column organizationT.limit_of_users is 'Maximum of active users for the whole organization. 0 means no limitation at all';

/*
 Fields without SQL definition for table organization

    vote_decrypt_public_main_key type:string is marked as a calculated field

*/

CREATE TABLE IF NOT EXISTS userT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    username varchar(256) NOT NULL,
    saml_id varchar(256) CONSTRAINT minLength_saml_id CHECK (char_length(saml_id) >= 1),
    pronoun varchar(32),
    title varchar(256),
    first_name varchar(256),
    last_name varchar(256),
    is_active boolean,
    is_physical_person boolean DEFAULT True,
    password varchar(256),
    default_password varchar(256),
    can_change_own_password boolean DEFAULT True,
    gender varchar(256),
    email varchar(256),
    default_number varchar(256),
    default_structure_level varchar(256),
    default_vote_weight decimal(6) CONSTRAINT minimum_default_vote_weight CHECK (default_vote_weight >= 0.000001) DEFAULT '1.000000',
    last_email_sent timestamptz,
    is_demo_user boolean,
    last_login timestamptz,
    organization_management_level enum_user_organization_management_level,
    meeting_ids integer[],
    organization_id integer NOT NULL
);



comment on column userT.saml_id is 'unique-key from IdP for SAML login';
comment on column userT.organization_management_level is 'Hierarchical permission level for the whole organization.';
comment on column userT.meeting_ids is 'Calculated. All ids from meetings calculated via meeting_user and group_ids as integers.';


CREATE TABLE IF NOT EXISTS meeting_userT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY NOT NULL,
    comment text,
    number varchar(256),
    structure_level varchar(256),
    about_me text,
    vote_weight decimal(6) CONSTRAINT minimum_vote_weight CHECK (vote_weight >= 0.000001),
    user_id integer NOT NULL,
    meeting_id integer NOT NULL,
    vote_delegated_to_id integer
);




CREATE TABLE IF NOT EXISTS organization_tagT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    color integer CHECK (color >= 0 and color <= 16777215) NOT NULL,
    organization_id integer NOT NULL
);



/*
 Fields without SQL definition for table organization_tag

    tagged_ids type:generic-relation-list no method defined

*/

CREATE TABLE IF NOT EXISTS themeT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY NOT NULL,
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
    abstain integer CHECK (abstain >= 0 and abstain <= 16777215),
    theme_for_organization_id integer,
    organization_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS committeeT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    description text,
    external_id varchar(256),
    default_meeting_id integer,
    forwarding_user_id integer,
    organization_id integer NOT NULL
);



comment on column committeeT.external_id is 'unique';


CREATE TABLE IF NOT EXISTS meetingT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    external_id varchar(256),
    welcome_title varchar(256) DEFAULT 'Welcome to OpenSlides',
    welcome_text text DEFAULT 'Space for your welcome text.',
    name varchar(100) NOT NULL DEFAULT 'OpenSlides',
    is_active_in_organization_id integer,
    is_archived_in_organization_id integer,
    description varchar(100) DEFAULT 'Presentation and assembly system',
    location varchar(256),
    start_time timestamptz,
    end_time timestamptz,
    imported_at timestamptz,
    language enum_meeting_language NOT NULL,
    jitsi_domain varchar(256),
    jitsi_room_name varchar(256),
    jitsi_room_password varchar(256),
    template_for_organization_id integer,
    enable_anonymous boolean DEFAULT False,
    custom_translations jsonb,
    conference_show boolean DEFAULT False,
    conference_auto_connect boolean DEFAULT False,
    conference_los_restriction boolean DEFAULT True,
    conference_stream_url varchar(256),
    conference_stream_poster_url varchar(256),
    conference_open_microphone boolean DEFAULT False,
    conference_open_video boolean DEFAULT False,
    conference_auto_connect_next_speakers integer DEFAULT 0,
    conference_enable_helpdesk boolean DEFAULT False,
    applause_enable boolean DEFAULT False,
    applause_type enum_meeting_applause_type DEFAULT 'applause-type-bar',
    applause_show_level boolean DEFAULT False,
    applause_min_amount integer CONSTRAINT minimum_applause_min_amount CHECK (applause_min_amount >= 0) DEFAULT 1,
    applause_max_amount integer CONSTRAINT minimum_applause_max_amount CHECK (applause_max_amount >= 0) DEFAULT 0,
    applause_timeout integer CONSTRAINT minimum_applause_timeout CHECK (applause_timeout >= 0) DEFAULT 5,
    applause_particle_image_url varchar(256),
    projector_countdown_default_time integer NOT NULL DEFAULT 60,
    projector_countdown_warning_time integer NOT NULL CONSTRAINT minimum_projector_countdown_warning_time CHECK (projector_countdown_warning_time >= 0) DEFAULT 0,
    export_csv_encoding enum_meeting_export_csv_encoding DEFAULT 'utf-8',
    export_csv_separator varchar(256) DEFAULT ';',
    export_pdf_pagenumber_alignment enum_meeting_export_pdf_pagenumber_alignment DEFAULT 'center',
    export_pdf_fontsize enum_meeting_export_pdf_fontsize DEFAULT '10',
    export_pdf_line_height real CONSTRAINT minimum_export_pdf_line_height CHECK (export_pdf_line_height >= 1.0) DEFAULT 1.25,
    export_pdf_page_margin_left integer CONSTRAINT minimum_export_pdf_page_margin_left CHECK (export_pdf_page_margin_left >= 0) DEFAULT 20,
    export_pdf_page_margin_top integer CONSTRAINT minimum_export_pdf_page_margin_top CHECK (export_pdf_page_margin_top >= 0) DEFAULT 25,
    export_pdf_page_margin_right integer CONSTRAINT minimum_export_pdf_page_margin_right CHECK (export_pdf_page_margin_right >= 0) DEFAULT 20,
    export_pdf_page_margin_bottom integer CONSTRAINT minimum_export_pdf_page_margin_bottom CHECK (export_pdf_page_margin_bottom >= 0) DEFAULT 20,
    export_pdf_pagesize enum_meeting_export_pdf_pagesize DEFAULT 'A4',
    agenda_show_subtitles boolean DEFAULT False,
    agenda_enable_numbering boolean DEFAULT True,
    agenda_number_prefix varchar(20),
    agenda_numeral_system enum_meeting_agenda_numeral_system DEFAULT 'arabic',
    agenda_item_creation enum_meeting_agenda_item_creation DEFAULT 'default_no',
    agenda_new_items_default_visibility enum_meeting_agenda_new_items_default_visibility DEFAULT 'internal',
    agenda_show_internal_items_on_projector boolean DEFAULT False,
    list_of_speakers_amount_last_on_projector integer CONSTRAINT minimum_list_of_speakers_amount_last_on_projector CHECK (list_of_speakers_amount_last_on_projector >= -1) DEFAULT 0,
    list_of_speakers_amount_next_on_projector integer CONSTRAINT minimum_list_of_speakers_amount_next_on_projector CHECK (list_of_speakers_amount_next_on_projector >= -1) DEFAULT -1,
    list_of_speakers_couple_countdown boolean DEFAULT True,
    list_of_speakers_show_amount_of_speakers_on_slide boolean DEFAULT True,
    list_of_speakers_present_users_only boolean DEFAULT False,
    list_of_speakers_show_first_contribution boolean DEFAULT False,
    list_of_speakers_enable_point_of_order_speakers boolean DEFAULT True,
    list_of_speakers_enable_point_of_order_categories boolean DEFAULT False,
    list_of_speakers_closing_disables_point_of_order boolean DEFAULT False,
    list_of_speakers_enable_pro_contra_speech boolean DEFAULT False,
    list_of_speakers_can_set_contribution_self boolean DEFAULT False,
    list_of_speakers_speaker_note_for_everyone boolean DEFAULT True,
    list_of_speakers_initially_closed boolean DEFAULT False,
    motions_default_workflow_id integer NOT NULL,
    motions_default_amendment_workflow_id integer NOT NULL,
    motions_default_statute_amendment_workflow_id integer NOT NULL,
    motions_preamble text DEFAULT 'The assembly may decide:',
    motions_default_line_numbering enum_meeting_motions_default_line_numbering DEFAULT 'outside',
    motions_line_length integer CONSTRAINT minimum_motions_line_length CHECK (motions_line_length >= 40) DEFAULT 85,
    motions_reason_required boolean DEFAULT False,
    motions_enable_text_on_projector boolean DEFAULT True,
    motions_enable_reason_on_projector boolean DEFAULT False,
    motions_enable_sidebox_on_projector boolean DEFAULT False,
    motions_enable_recommendation_on_projector boolean DEFAULT True,
    motions_show_referring_motions boolean DEFAULT True,
    motions_show_sequential_number boolean DEFAULT True,
    motions_recommendations_by varchar(256),
    motions_block_slide_columns integer CONSTRAINT minimum_motions_block_slide_columns CHECK (motions_block_slide_columns >= 1),
    motions_statute_recommendations_by varchar(256),
    motions_recommendation_text_mode enum_meeting_motions_recommendation_text_mode DEFAULT 'diff',
    motions_default_sorting enum_meeting_motions_default_sorting DEFAULT 'number',
    motions_number_type enum_meeting_motions_number_type DEFAULT 'per_category',
    motions_number_min_digits integer DEFAULT 2,
    motions_number_with_blank boolean DEFAULT False,
    motions_statutes_enabled boolean DEFAULT False,
    motions_amendments_enabled boolean DEFAULT True,
    motions_amendments_in_main_list boolean DEFAULT True,
    motions_amendments_of_amendments boolean DEFAULT False,
    motions_amendments_prefix varchar(256) DEFAULT '-Ä',
    motions_amendments_text_mode enum_meeting_motions_amendments_text_mode DEFAULT 'paragraph',
    motions_amendments_multiple_paragraphs boolean DEFAULT True,
    motions_supporters_min_amount integer CONSTRAINT minimum_motions_supporters_min_amount CHECK (motions_supporters_min_amount >= 0) DEFAULT 0,
    motions_export_title varchar(256) DEFAULT 'Motions',
    motions_export_preamble text,
    motions_export_submitter_recommendation boolean DEFAULT True,
    motions_export_follow_recommendation boolean DEFAULT False,
    motion_poll_ballot_paper_selection enum_meeting_motion_poll_ballot_paper_selection DEFAULT 'CUSTOM_NUMBER',
    motion_poll_ballot_paper_number integer DEFAULT 8,
    motion_poll_default_type varchar(256) DEFAULT 'pseudoanonymous',
    motion_poll_default_onehundred_percent_base varchar(256) DEFAULT 'YNA',
    motion_poll_default_backend enum_meeting_motion_poll_default_backend DEFAULT 'fast',
    users_enable_presence_view boolean DEFAULT False,
    users_enable_vote_weight boolean DEFAULT False,
    users_allow_self_set_present boolean DEFAULT True,
    users_pdf_welcometitle varchar(256) DEFAULT 'Welcome to OpenSlides',
    users_pdf_welcometext text DEFAULT '[Place for your welcome and help text.]',
    users_pdf_wlan_ssid varchar(256),
    users_pdf_wlan_password varchar(256),
    users_pdf_wlan_encryption enum_meeting_users_pdf_wlan_encryption DEFAULT 'WPA',
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
    assignment_poll_ballot_paper_selection enum_meeting_assignment_poll_ballot_paper_selection DEFAULT 'CUSTOM_NUMBER',
    assignment_poll_ballot_paper_number integer DEFAULT 8,
    assignment_poll_add_candidates_to_list_of_speakers boolean DEFAULT False,
    assignment_poll_enable_max_votes_per_option boolean DEFAULT False,
    assignment_poll_sort_poll_result_by_votes boolean DEFAULT True,
    assignment_poll_default_type varchar(256) DEFAULT 'pseudoanonymous',
    assignment_poll_default_method varchar(256) DEFAULT 'Y',
    assignment_poll_default_onehundred_percent_base varchar(256) DEFAULT 'valid',
    assignment_poll_default_backend enum_meeting_assignment_poll_default_backend DEFAULT 'fast',
    poll_ballot_paper_selection enum_meeting_poll_ballot_paper_selection,
    poll_ballot_paper_number integer,
    poll_sort_poll_result_by_votes boolean,
    poll_default_type varchar(256) DEFAULT 'analog',
    poll_default_method varchar(256),
    poll_default_onehundred_percent_base varchar(256) DEFAULT 'YNA',
    poll_default_backend enum_meeting_poll_default_backend DEFAULT 'fast',
    poll_couple_countdown boolean DEFAULT True,
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
    default_meeting_for_committee_id integer,
    user_ids integer[],
    reference_projector_id integer NOT NULL,
    list_of_speakers_countdown_id integer,
    poll_countdown_id integer,
    default_group_id integer NOT NULL,
    admin_group_id integer
);



comment on column meetingT.external_id is 'unique in committee';
comment on column meetingT.is_active_in_organization_id is 'Backrelation and boolean flag at once';
comment on column meetingT.is_archived_in_organization_id is 'Backrelation and boolean flag at once';
comment on column meetingT.user_ids is 'Calculated. All user ids from all users assigned to groups of this meeting.';


CREATE TABLE IF NOT EXISTS groupT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    external_id varchar(256),
    name varchar(256) NOT NULL,
    permissions enum_group_permissions[],
    weight integer,
    default_group_for_meeting_id integer,
    admin_group_for_meeting_id integer,
    used_as_motion_poll_default_id integer,
    used_as_assignment_poll_default_id integer,
    used_as_topic_poll_default_id integer,
    used_as_poll_default_id integer,
    meeting_id integer NOT NULL
);



comment on column groupT.external_id is 'unique in meeting';


CREATE TABLE IF NOT EXISTS personal_noteT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    note text,
    star boolean,
    meeting_user_id integer NOT NULL,
    meeting_id integer NOT NULL
);



/*
 Fields without SQL definition for table personal_note

    content_object_id type:generic-relation no method defined

*/

CREATE TABLE IF NOT EXISTS tagT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    meeting_id integer NOT NULL
);



/*
 Fields without SQL definition for table tag

    tagged_ids type:generic-relation-list no method defined

*/

CREATE TABLE IF NOT EXISTS agenda_itemT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    item_number varchar(256),
    comment varchar(256),
    closed boolean DEFAULT False,
    type enum_agenda_item_type DEFAULT 'common',
    duration integer CONSTRAINT minimum_duration CHECK (duration >= 0),
    is_internal boolean,
    is_hidden boolean,
    level integer,
    weight integer,
    parent_id integer,
    meeting_id integer NOT NULL
);



comment on column agenda_itemT.duration is 'Given in seconds';
comment on column agenda_itemT.is_internal is 'Calculated by the server';
comment on column agenda_itemT.is_hidden is 'Calculated by the server';
comment on column agenda_itemT.level is 'Calculated by the server';

/*
 Fields without SQL definition for table agenda_item

    content_object_id type:generic-relation no method defined

*/

CREATE TABLE IF NOT EXISTS list_of_speakersT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    closed boolean DEFAULT False,
    sequential_number integer NOT NULL,
    meeting_id integer NOT NULL
);



comment on column list_of_speakersT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';

/*
 Fields without SQL definition for table list_of_speakers

    content_object_id type:generic-relation no method defined

*/

CREATE TABLE IF NOT EXISTS point_of_order_categoryT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    text varchar(256) NOT NULL,
    rank integer NOT NULL,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS speakerT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    begin_time timestamptz,
    end_time timestamptz,
    weight integer DEFAULT 10000,
    speech_state enum_speaker_speech_state,
    note varchar(250),
    point_of_order boolean,
    list_of_speakers_id integer NOT NULL,
    meeting_user_id integer,
    point_of_order_category_id integer,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS topicT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256) NOT NULL,
    text text,
    sequential_number integer NOT NULL,
    agenda_item_id integer NOT NULL,
    list_of_speakers_id integer NOT NULL,
    meeting_id integer NOT NULL
);



comment on column topicT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE IF NOT EXISTS motionT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    number varchar(256),
    number_value integer,
    sequential_number integer NOT NULL,
    title varchar(256) NOT NULL,
    text text,
    amendment_paragraphs jsonb,
    modified_final_version text,
    reason text,
    category_weight integer DEFAULT 10000,
    state_extension varchar(256),
    recommendation_extension varchar(256),
    sort_weight integer DEFAULT 10000,
    created timestamptz,
    last_modified timestamptz,
    workflow_timestamp timestamptz,
    start_line_number integer CONSTRAINT minimum_start_line_number CHECK (start_line_number >= 1) DEFAULT 1,
    forwarded timestamptz,
    lead_motion_id integer,
    sort_parent_id integer,
    origin_id integer,
    origin_meeting_id integer,
    state_id integer NOT NULL,
    recommendation_id integer,
    category_id integer,
    block_id integer,
    statute_paragraph_id integer,
    agenda_item_id integer,
    list_of_speakers_id integer NOT NULL,
    meeting_id integer NOT NULL
);



comment on column motionT.number_value is 'The number value of this motion. This number is auto-generated and read-only.';
comment on column motionT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';

/*
 Fields without SQL definition for table motion

    state_extension_reference_ids type:generic-relation-list no method defined
    recommendation_extension_reference_ids type:generic-relation-list no method defined

*/

CREATE TABLE IF NOT EXISTS motion_submitterT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    weight integer,
    meeting_user_id integer NOT NULL,
    motion_id integer NOT NULL,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS motion_commentT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    comment text,
    motion_id integer NOT NULL,
    section_id integer NOT NULL,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS motion_comment_sectionT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    weight integer DEFAULT 10000,
    sequential_number integer NOT NULL,
    submitter_can_write boolean,
    meeting_id integer NOT NULL
);



comment on column motion_comment_sectionT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE IF NOT EXISTS motion_categoryT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    prefix varchar(256),
    weight integer DEFAULT 10000,
    level integer,
    sequential_number integer NOT NULL,
    parent_id integer,
    meeting_id integer NOT NULL
);



comment on column motion_categoryT.level is 'Calculated field.';
comment on column motion_categoryT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE IF NOT EXISTS motion_blockT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256) NOT NULL,
    internal boolean,
    sequential_number integer NOT NULL,
    agenda_item_id integer,
    list_of_speakers_id integer NOT NULL,
    meeting_id integer NOT NULL
);



comment on column motion_blockT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE IF NOT EXISTS motion_change_recommendationT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    rejected boolean DEFAULT False,
    internal boolean DEFAULT False,
    type enum_motion_change_recommendation_type DEFAULT 'replacement',
    other_description varchar(256),
    line_from integer CONSTRAINT minimum_line_from CHECK (line_from >= 0),
    line_to integer CONSTRAINT minimum_line_to CHECK (line_to >= 0),
    text text,
    creation_time timestamptz,
    motion_id integer NOT NULL,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS motion_stateT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    weight integer NOT NULL,
    recommendation_label varchar(256),
    css_class enum_motion_state_css_class NOT NULL DEFAULT 'lightblue',
    restrictions enum_motion_state_restrictions[],
    allow_support boolean DEFAULT False,
    allow_create_poll boolean DEFAULT False,
    allow_submitter_edit boolean DEFAULT False,
    set_number boolean DEFAULT True,
    show_state_extension_field boolean DEFAULT False,
    show_recommendation_extension_field boolean DEFAULT False,
    merge_amendment_into_final enum_motion_state_merge_amendment_into_final DEFAULT 'undefined',
    allow_motion_forwarding boolean,
    set_workflow_timestamp boolean,
    submitter_withdraw_state_id integer,
    workflow_id integer NOT NULL,
    first_state_of_workflow_id integer,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS motion_workflowT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    sequential_number integer NOT NULL,
    first_state_id integer NOT NULL,
    default_workflow_meeting_id integer,
    default_amendment_workflow_meeting_id integer,
    default_statute_amendment_workflow_meeting_id integer,
    meeting_id integer NOT NULL
);



comment on column motion_workflowT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE IF NOT EXISTS motion_statute_paragraphT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256) NOT NULL,
    text text,
    weight integer DEFAULT 10000,
    sequential_number integer NOT NULL,
    meeting_id integer NOT NULL
);



comment on column motion_statute_paragraphT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE IF NOT EXISTS pollT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    description text,
    title varchar(256) NOT NULL,
    type enum_poll_type NOT NULL,
    backend enum_poll_backend NOT NULL DEFAULT 'fast',
    is_pseudoanonymized boolean,
    pollmethod enum_poll_pollmethod NOT NULL,
    state enum_poll_state DEFAULT 'created',
    min_votes_amount integer CONSTRAINT minimum_min_votes_amount CHECK (min_votes_amount >= 1) DEFAULT 1,
    max_votes_amount integer CONSTRAINT minimum_max_votes_amount CHECK (max_votes_amount >= 1) DEFAULT 1,
    max_votes_per_option integer CONSTRAINT minimum_max_votes_per_option CHECK (max_votes_per_option >= 1) DEFAULT 1,
    global_yes boolean DEFAULT False,
    global_no boolean DEFAULT False,
    global_abstain boolean DEFAULT False,
    onehundred_percent_base enum_poll_onehundred_percent_base NOT NULL DEFAULT 'disabled',
    votesvalid decimal(6),
    votesinvalid decimal(6),
    votescast decimal(6),
    entitled_users_at_stop jsonb,
    sequential_number integer NOT NULL,
    crypt_key varchar(256),
    crypt_signature varchar(256),
    votes_raw text,
    votes_signature varchar(256),
    global_option_id integer,
    meeting_id integer NOT NULL
);



comment on column pollT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';
comment on column pollT.crypt_key is 'base64 public key to cryptographic votes.';
comment on column pollT.crypt_signature is 'base64 signature of cryptographic_key.';
comment on column pollT.votes_raw is 'original form of decrypted votes.';
comment on column pollT.votes_signature is 'base64 signature of votes_raw field.';

/*
 Fields without SQL definition for table poll

    vote_count type:number is marked as a calculated field
    content_object_id type:generic-relation no method defined

*/

CREATE TABLE IF NOT EXISTS optionT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    weight integer DEFAULT 10000,
    text text,
    yes decimal(6),
    no decimal(6),
    abstain decimal(6),
    poll_id integer,
    used_as_global_option_in_poll_id integer,
    meeting_id integer NOT NULL
);



/*
 Fields without SQL definition for table option

    content_object_id type:generic-relation no method defined

*/

CREATE TABLE IF NOT EXISTS voteT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    weight decimal(6),
    value varchar(256),
    user_token varchar(256) NOT NULL,
    option_id integer NOT NULL,
    user_id integer,
    delegated_user_id integer,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS assignmentT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256) NOT NULL,
    description text,
    open_posts integer CONSTRAINT minimum_open_posts CHECK (open_posts >= 0) DEFAULT 0,
    phase enum_assignment_phase DEFAULT 'search',
    default_poll_description text,
    number_poll_candidates boolean,
    sequential_number integer NOT NULL,
    agenda_item_id integer,
    list_of_speakers_id integer NOT NULL,
    meeting_id integer NOT NULL
);



comment on column assignmentT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE IF NOT EXISTS assignment_candidateT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    weight integer DEFAULT 10000,
    assignment_id integer NOT NULL,
    meeting_user_id integer,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS poll_candidate_listT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    meeting_id integer NOT NULL,
    option_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS poll_candidateT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    poll_candidate_list_id integer NOT NULL,
    user_id integer,
    weight integer NOT NULL,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS mediafileT (
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
    parent_id integer,
    list_of_speakers_id integer,
    used_as_logo_projector_main_in_meeting_id integer,
    used_as_logo_projector_header_in_meeting_id integer,
    used_as_logo_web_header_in_meeting_id integer,
    used_as_logo_pdf_header_l_in_meeting_id integer,
    used_as_logo_pdf_header_r_in_meeting_id integer,
    used_as_logo_pdf_footer_l_in_meeting_id integer,
    used_as_logo_pdf_footer_r_in_meeting_id integer,
    used_as_logo_pdf_ballot_paper_in_meeting_id integer,
    used_as_font_regular_in_meeting_id integer,
    used_as_font_italic_in_meeting_id integer,
    used_as_font_bold_in_meeting_id integer,
    used_as_font_bold_italic_in_meeting_id integer,
    used_as_font_monospace_in_meeting_id integer,
    used_as_font_chyron_speaker_name_in_meeting_id integer,
    used_as_font_projector_h1_in_meeting_id integer,
    used_as_font_projector_h2_in_meeting_id integer
);



comment on column mediafileT.title is 'Title and parent_id must be unique.';
comment on column mediafileT.filesize is 'In bytes, not the human readable format anymore.';
comment on column mediafileT.filename is 'The uploaded filename. Will be used for downloading. Only writeable on create.';
comment on column mediafileT.is_public is 'Calculated field. inherited_access_group_ids == [] can have two causes: cancelling access groups (=> is_public := false) or no access groups at all (=> is_public := true)';

/*
 Fields without SQL definition for table mediafile

    attachment_ids type:generic-relation-list no method defined
    owner_id type:generic-relation no method defined

*/

CREATE TABLE IF NOT EXISTS projectorT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256),
    is_internal boolean DEFAULT False,
    scale integer DEFAULT 0,
    scroll integer CONSTRAINT minimum_scroll CHECK (scroll >= 0) DEFAULT 0,
    width integer CONSTRAINT minimum_width CHECK (width >= 1) DEFAULT 1200,
    aspect_ratio_numerator integer CONSTRAINT minimum_aspect_ratio_numerator CHECK (aspect_ratio_numerator >= 1) DEFAULT 16,
    aspect_ratio_denominator integer CONSTRAINT minimum_aspect_ratio_denominator CHECK (aspect_ratio_denominator >= 1) DEFAULT 9,
    color integer CHECK (color >= 0 and color <= 16777215) DEFAULT 0,
    background_color integer CHECK (background_color >= 0 and background_color <= 16777215) DEFAULT 16777215,
    header_background_color integer CHECK (header_background_color >= 0 and header_background_color <= 16777215) DEFAULT 3241878,
    header_font_color integer CHECK (header_font_color >= 0 and header_font_color <= 16777215) DEFAULT 16119285,
    header_h1_color integer CHECK (header_h1_color >= 0 and header_h1_color <= 16777215) DEFAULT 3241878,
    chyron_background_color integer CHECK (chyron_background_color >= 0 and chyron_background_color <= 16777215) DEFAULT 3241878,
    chyron_font_color integer CHECK (chyron_font_color >= 0 and chyron_font_color <= 16777215) DEFAULT 16777215,
    show_header_footer boolean DEFAULT True,
    show_title boolean DEFAULT True,
    show_logo boolean DEFAULT True,
    show_clock boolean DEFAULT True,
    sequential_number integer NOT NULL,
    used_as_reference_projector_meeting_id integer,
    used_as_default_projector_for_agenda_item_list_in_meeting_id integer,
    used_as_default_projector_for_topic_in_meeting_id integer,
    used_as_default_projector_for_list_of_speakers_in_meeting_id integer,
    used_as_default_projector_for_current_los_in_meeting_id integer,
    used_as_default_projector_for_motion_in_meeting_id integer,
    used_as_default_projector_for_amendment_in_meeting_id integer,
    used_as_default_projector_for_motion_block_in_meeting_id integer,
    used_as_default_projector_for_assignment_in_meeting_id integer,
    used_as_default_projector_for_mediafile_in_meeting_id integer,
    used_as_default_projector_for_message_in_meeting_id integer,
    used_as_default_projector_for_countdown_in_meeting_id integer,
    used_as_default_projector_for_assignment_poll_in_meeting_id integer,
    used_as_default_projector_for_motion_poll_in_meeting_id integer,
    used_as_default_projector_for_poll_in_meeting_id integer,
    meeting_id integer NOT NULL
);



comment on column projectorT.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE IF NOT EXISTS projectionT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    options jsonb,
    stable boolean DEFAULT False,
    weight integer,
    type varchar(256),
    current_projector_id integer,
    preview_projector_id integer,
    history_projector_id integer,
    meeting_id integer NOT NULL
);



/*
 Fields without SQL definition for table projection

    content type:JSON is marked as a calculated field
    content_object_id type:generic-relation no method defined

*/

CREATE TABLE IF NOT EXISTS projector_messageT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    message text,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS projector_countdownT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title varchar(256) NOT NULL,
    description varchar(256) DEFAULT '',
    default_time integer,
    countdown_time real DEFAULT 60,
    running boolean DEFAULT False,
    used_as_list_of_speakers_countdown_meeting_id integer,
    used_as_poll_countdown_meeting_id integer,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS chat_groupT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    weight integer DEFAULT 10000,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS chat_messageT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    content text NOT NULL,
    created timestamptz NOT NULL,
    meeting_user_id integer NOT NULL,
    chat_group_id integer NOT NULL,
    meeting_id integer NOT NULL
);




CREATE TABLE IF NOT EXISTS action_workerT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    state enum_action_worker_state NOT NULL,
    created timestamptz NOT NULL,
    timestamp timestamptz NOT NULL,
    result jsonb
);




CREATE TABLE IF NOT EXISTS import_previewT (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(256) NOT NULL,
    state enum_import_preview_state NOT NULL,
    created timestamptz NOT NULL,
    result jsonb
);



-- View definitions

CREATE OR REPLACE VIEW organization AS SELECT *,
(select array_agg(c.id) from committeeT c where c.organization_id = o.id) as committee_ids,
(select array_agg(m.id) from meetingT m where m.is_active_in_organization_id = o.id) as active_meeting_ids,
(select array_agg(m.id) from meetingT m where m.is_archived_in_organization_id = o.id) as archived_meeting_ids,
(select array_agg(m.id) from meetingT m where m.template_for_organization_id = o.id) as template_meeting_ids,
(select array_agg(ot.id) from organization_tagT ot where ot.organization_id = o.id) as organization_tag_ids,
(select array_agg(t.id) from themeT t where t.organization_id = o.id) as theme_ids,
(select array_agg(u.id) from userT u where u.organization_id = o.id) as user_ids
FROM organizationT o;


CREATE OR REPLACE VIEW user_ AS SELECT *,
(select array_agg(c.id) from committeeT c where c.forwarding_user_id = u.id) as forwarding_committee_ids,
(select array_agg(m.id) from meeting_userT m where m.user_id = u.id) as meeting_user_ids,
(select array_agg(v.id) from voteT v where v.user_id = u.id) as vote_ids,
(select array_agg(v.id) from voteT v where v.delegated_user_id = u.id) as delegated_vote_ids,
(select array_agg(p.id) from poll_candidateT p where p.user_id = u.id) as poll_candidate_ids
FROM userT u;


CREATE OR REPLACE VIEW meeting_user AS SELECT *,
(select array_agg(p.id) from personal_noteT p where p.meeting_user_id = m.id) as personal_note_ids,
(select array_agg(s.id) from speakerT s where s.meeting_user_id = m.id) as speaker_ids,
(select array_agg(ms.id) from motion_submitterT ms where ms.meeting_user_id = m.id) as motion_submitter_ids,
(select array_agg(a.id) from assignment_candidateT a where a.meeting_user_id = m.id) as assignment_candidate_ids,
(select array_agg(mu.id) from meeting_userT mu where mu.vote_delegated_to_id = m.id) as vote_delegations_from_ids,
(select array_agg(c.id) from chat_messageT c where c.meeting_user_id = m.id) as chat_message_ids
FROM meeting_userT m;


CREATE OR REPLACE VIEW committee AS SELECT *,
(select array_agg(m.id) from meetingT m where m.committee_id = c.id) as meeting_ids
FROM committeeT c;


CREATE OR REPLACE VIEW meeting AS SELECT *,
(select array_agg(g.id) from groupT g where g.used_as_motion_poll_default_id = m.id) as motion_poll_default_group_ids,
(select array_agg(p.id) from poll_candidate_listT p where p.meeting_id = m.id) as poll_candidate_list_ids,
(select array_agg(p.id) from poll_candidateT p where p.meeting_id = m.id) as poll_candidate_ids,
(select array_agg(mu.id) from meeting_userT mu where mu.meeting_id = m.id) as meeting_user_ids,
(select array_agg(g.id) from groupT g where g.used_as_assignment_poll_default_id = m.id) as assignment_poll_default_group_ids,
(select array_agg(g.id) from groupT g where g.used_as_poll_default_id = m.id) as poll_default_group_ids,
(select array_agg(g.id) from groupT g where g.used_as_topic_poll_default_id = m.id) as topic_poll_default_group_ids,
(select array_agg(p.id) from projectorT p where p.meeting_id = m.id) as projector_ids,
(select array_agg(p.id) from projectionT p where p.meeting_id = m.id) as all_projection_ids,
(select array_agg(p.id) from projector_messageT p where p.meeting_id = m.id) as projector_message_ids,
(select array_agg(p.id) from projector_countdownT p where p.meeting_id = m.id) as projector_countdown_ids,
(select array_agg(t.id) from tagT t where t.meeting_id = m.id) as tag_ids,
(select array_agg(a.id) from agenda_itemT a where a.meeting_id = m.id) as agenda_item_ids,
(select array_agg(l.id) from list_of_speakersT l where l.meeting_id = m.id) as list_of_speakers_ids,
(select array_agg(p.id) from point_of_order_categoryT p where p.meeting_id = m.id) as point_of_order_category_ids,
(select array_agg(s.id) from speakerT s where s.meeting_id = m.id) as speaker_ids,
(select array_agg(t.id) from topicT t where t.meeting_id = m.id) as topic_ids,
(select array_agg(g.id) from groupT g where g.meeting_id = m.id) as group_ids,
(select array_agg(m1.id) from motionT m1 where m1.meeting_id = m.id) as motion_ids,
(select array_agg(m1.id) from motionT m1 where m1.origin_meeting_id = m.id) as forwarded_motion_ids,
(select array_agg(mc.id) from motion_comment_sectionT mc where mc.meeting_id = m.id) as motion_comment_section_ids,
(select array_agg(mc.id) from motion_categoryT mc where mc.meeting_id = m.id) as motion_category_ids,
(select array_agg(mb.id) from motion_blockT mb where mb.meeting_id = m.id) as motion_block_ids,
(select array_agg(mw.id) from motion_workflowT mw where mw.meeting_id = m.id) as motion_workflow_ids,
(select array_agg(ms.id) from motion_statute_paragraphT ms where ms.meeting_id = m.id) as motion_statute_paragraph_ids,
(select array_agg(mc.id) from motion_commentT mc where mc.meeting_id = m.id) as motion_comment_ids,
(select array_agg(ms.id) from motion_submitterT ms where ms.meeting_id = m.id) as motion_submitter_ids,
(select array_agg(mc.id) from motion_change_recommendationT mc where mc.meeting_id = m.id) as motion_change_recommendation_ids,
(select array_agg(ms.id) from motion_stateT ms where ms.meeting_id = m.id) as motion_state_ids,
(select array_agg(p.id) from pollT p where p.meeting_id = m.id) as poll_ids,
(select array_agg(o.id) from optionT o where o.meeting_id = m.id) as option_ids,
(select array_agg(v.id) from voteT v where v.meeting_id = m.id) as vote_ids,
(select array_agg(a.id) from assignmentT a where a.meeting_id = m.id) as assignment_ids,
(select array_agg(a.id) from assignment_candidateT a where a.meeting_id = m.id) as assignment_candidate_ids,
(select array_agg(p.id) from personal_noteT p where p.meeting_id = m.id) as personal_note_ids,
(select array_agg(c.id) from chat_groupT c where c.meeting_id = m.id) as chat_group_ids,
(select array_agg(c.id) from chat_messageT c where c.meeting_id = m.id) as chat_message_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_agenda_item_list_in_meeting_id = m.id) as default_projector_agenda_item_list_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_topic_in_meeting_id = m.id) as default_projector_topic_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_list_of_speakers_in_meeting_id = m.id) as default_projector_list_of_speakers_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_current_los_in_meeting_id = m.id) as default_projector_current_list_of_speakers_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_motion_in_meeting_id = m.id) as default_projector_motion_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_amendment_in_meeting_id = m.id) as default_projector_amendment_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_motion_block_in_meeting_id = m.id) as default_projector_motion_block_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_assignment_in_meeting_id = m.id) as default_projector_assignment_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_mediafile_in_meeting_id = m.id) as default_projector_mediafile_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_message_in_meeting_id = m.id) as default_projector_message_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_countdown_in_meeting_id = m.id) as default_projector_countdown_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_assignment_poll_in_meeting_id = m.id) as default_projector_assignment_poll_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_motion_poll_in_meeting_id = m.id) as default_projector_motion_poll_ids,
(select array_agg(p.id) from projectorT p where p.used_as_default_projector_for_poll_in_meeting_id = m.id) as default_projector_poll_ids
FROM meetingT m;


CREATE OR REPLACE VIEW agenda_item AS SELECT *,
(select array_agg(ai.id) from agenda_itemT ai where ai.parent_id = a.id) as child_ids
FROM agenda_itemT a;


CREATE OR REPLACE VIEW list_of_speakers AS SELECT *,
(select array_agg(s.id) from speakerT s where s.list_of_speakers_id = l.id) as speaker_ids
FROM list_of_speakersT l;


CREATE OR REPLACE VIEW point_of_order_category AS SELECT *,
(select array_agg(s.id) from speakerT s where s.point_of_order_category_id = p.id) as speaker_ids
FROM point_of_order_categoryT p;


CREATE OR REPLACE VIEW motion AS SELECT *,
(select array_agg(m1.id) from motionT m1 where m1.lead_motion_id = m.id) as amendment_ids,
(select array_agg(m1.id) from motionT m1 where m1.sort_parent_id = m.id) as sort_child_ids,
(select array_agg(m1.id) from motionT m1 where m1.origin_id = m.id) as derived_motion_ids,
(select array_agg(ms.id) from motion_submitterT ms where ms.motion_id = m.id) as submitter_ids,
(select array_agg(mc.id) from motion_change_recommendationT mc where mc.motion_id = m.id) as change_recommendation_ids,
(select array_agg(mc.id) from motion_commentT mc where mc.motion_id = m.id) as comment_ids
FROM motionT m;


CREATE OR REPLACE VIEW motion_comment_section AS SELECT *,
(select array_agg(mc.id) from motion_commentT mc where mc.section_id = m.id) as comment_ids
FROM motion_comment_sectionT m;


CREATE OR REPLACE VIEW motion_category AS SELECT *,
(select array_agg(mc.id) from motion_categoryT mc where mc.parent_id = m.id) as child_ids,
(select array_agg(m1.id) from motionT m1 where m1.category_id = m.id) as motion_ids
FROM motion_categoryT m;


CREATE OR REPLACE VIEW motion_block AS SELECT *,
(select array_agg(m1.id) from motionT m1 where m1.block_id = m.id) as motion_ids
FROM motion_blockT m;


CREATE OR REPLACE VIEW motion_state AS SELECT *,
(select array_agg(ms.id) from motion_stateT ms where ms.submitter_withdraw_state_id = m.id) as submitter_withdraw_back_ids,
(select array_agg(m1.id) from motionT m1 where m1.state_id = m.id) as motion_ids,
(select array_agg(m1.id) from motionT m1 where m1.recommendation_id = m.id) as motion_recommendation_ids
FROM motion_stateT m;


CREATE OR REPLACE VIEW motion_workflow AS SELECT *,
(select array_agg(ms.id) from motion_stateT ms where ms.workflow_id = m.id) as state_ids
FROM motion_workflowT m;


CREATE OR REPLACE VIEW motion_statute_paragraph AS SELECT *,
(select array_agg(m1.id) from motionT m1 where m1.statute_paragraph_id = m.id) as motion_ids
FROM motion_statute_paragraphT m;


CREATE OR REPLACE VIEW poll AS SELECT *,
(select array_agg(o.id) from optionT o where o.poll_id = p.id) as option_ids
FROM pollT p;


CREATE OR REPLACE VIEW option AS SELECT *,
(select array_agg(v.id) from voteT v where v.option_id = o.id) as vote_ids
FROM optionT o;


CREATE OR REPLACE VIEW assignment AS SELECT *,
(select array_agg(ac.id) from assignment_candidateT ac where ac.assignment_id = a.id) as candidate_ids
FROM assignmentT a;


CREATE OR REPLACE VIEW poll_candidate_list AS SELECT *,
(select array_agg(pc.id) from poll_candidateT pc where pc.poll_candidate_list_id = p.id) as poll_candidate_ids
FROM poll_candidate_listT p;


CREATE OR REPLACE VIEW mediafile AS SELECT *,
(select array_agg(m1.id) from mediafileT m1 where m1.parent_id = m.id) as child_ids
FROM mediafileT m;


CREATE OR REPLACE VIEW projector AS SELECT *,
(select array_agg(p1.id) from projectionT p1 where p1.current_projector_id = p.id) as current_projection_ids,
(select array_agg(p1.id) from projectionT p1 where p1.preview_projector_id = p.id) as preview_projection_ids,
(select array_agg(p1.id) from projectionT p1 where p1.history_projector_id = p.id) as history_projection_ids
FROM projectorT p;


CREATE OR REPLACE VIEW chat_group AS SELECT *,
(select array_agg(cm.id) from chat_messageT cm where cm.chat_group_id = c.id) as chat_message_ids
FROM chat_groupT c;

-- Alter table relations
ALTER TABLE organizationT ADD FOREIGN KEY(theme_id) REFERENCES themeT(id) INITIALLY DEFERRED;

ALTER TABLE userT ADD FOREIGN KEY(organization_id) REFERENCES organizationT(id);

ALTER TABLE meeting_userT ADD FOREIGN KEY(user_id) REFERENCES userT(id);
ALTER TABLE meeting_userT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);
ALTER TABLE meeting_userT ADD FOREIGN KEY(vote_delegated_to_id) REFERENCES meeting_userT(id);

ALTER TABLE organization_tagT ADD FOREIGN KEY(organization_id) REFERENCES organizationT(id);

ALTER TABLE themeT ADD FOREIGN KEY(theme_for_organization_id) REFERENCES organizationT(id) INITIALLY DEFERRED;
ALTER TABLE themeT ADD FOREIGN KEY(organization_id) REFERENCES organizationT(id) INITIALLY DEFERRED;

ALTER TABLE committeeT ADD FOREIGN KEY(default_meeting_id) REFERENCES meetingT(id);
ALTER TABLE committeeT ADD FOREIGN KEY(forwarding_user_id) REFERENCES userT(id);
ALTER TABLE committeeT ADD FOREIGN KEY(organization_id) REFERENCES organizationT(id);

ALTER TABLE meetingT ADD FOREIGN KEY(is_active_in_organization_id) REFERENCES organizationT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(is_archived_in_organization_id) REFERENCES organizationT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(template_for_organization_id) REFERENCES organizationT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(motions_default_workflow_id) REFERENCES motion_workflowT(id) INITIALLY DEFERRED;
ALTER TABLE meetingT ADD FOREIGN KEY(motions_default_amendment_workflow_id) REFERENCES motion_workflowT(id) INITIALLY DEFERRED;
ALTER TABLE meetingT ADD FOREIGN KEY(motions_default_statute_amendment_workflow_id) REFERENCES motion_workflowT(id) INITIALLY DEFERRED;
ALTER TABLE meetingT ADD FOREIGN KEY(logo_projector_main_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(logo_projector_header_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(logo_web_header_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(logo_pdf_header_l_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(logo_pdf_header_r_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(logo_pdf_footer_l_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(logo_pdf_footer_r_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(logo_pdf_ballot_paper_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(font_regular_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(font_italic_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(font_bold_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(font_bold_italic_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(font_monospace_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(font_chyron_speaker_name_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(font_projector_h1_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(font_projector_h2_id) REFERENCES mediafileT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(committee_id) REFERENCES committeeT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(default_meeting_for_committee_id) REFERENCES committeeT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(reference_projector_id) REFERENCES projectorT(id) INITIALLY DEFERRED;
ALTER TABLE meetingT ADD FOREIGN KEY(list_of_speakers_countdown_id) REFERENCES projector_countdownT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(poll_countdown_id) REFERENCES projector_countdownT(id);
ALTER TABLE meetingT ADD FOREIGN KEY(default_group_id) REFERENCES groupT(id) INITIALLY DEFERRED;
ALTER TABLE meetingT ADD FOREIGN KEY(admin_group_id) REFERENCES groupT(id) INITIALLY DEFERRED;

ALTER TABLE groupT ADD FOREIGN KEY(default_group_for_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE groupT ADD FOREIGN KEY(admin_group_for_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE groupT ADD FOREIGN KEY(used_as_motion_poll_default_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE groupT ADD FOREIGN KEY(used_as_assignment_poll_default_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE groupT ADD FOREIGN KEY(used_as_topic_poll_default_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE groupT ADD FOREIGN KEY(used_as_poll_default_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE groupT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;

ALTER TABLE personal_noteT ADD FOREIGN KEY(meeting_user_id) REFERENCES meeting_userT(id);
ALTER TABLE personal_noteT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE tagT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE agenda_itemT ADD FOREIGN KEY(parent_id) REFERENCES agenda_itemT(id);
ALTER TABLE agenda_itemT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE list_of_speakersT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE point_of_order_categoryT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE speakerT ADD FOREIGN KEY(list_of_speakers_id) REFERENCES list_of_speakersT(id);
ALTER TABLE speakerT ADD FOREIGN KEY(meeting_user_id) REFERENCES meeting_userT(id);
ALTER TABLE speakerT ADD FOREIGN KEY(point_of_order_category_id) REFERENCES point_of_order_categoryT(id);
ALTER TABLE speakerT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE topicT ADD FOREIGN KEY(agenda_item_id) REFERENCES agenda_itemT(id);
ALTER TABLE topicT ADD FOREIGN KEY(list_of_speakers_id) REFERENCES list_of_speakersT(id);
ALTER TABLE topicT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE motionT ADD FOREIGN KEY(lead_motion_id) REFERENCES motionT(id);
ALTER TABLE motionT ADD FOREIGN KEY(sort_parent_id) REFERENCES motionT(id);
ALTER TABLE motionT ADD FOREIGN KEY(origin_id) REFERENCES motionT(id);
ALTER TABLE motionT ADD FOREIGN KEY(origin_meeting_id) REFERENCES meetingT(id);
ALTER TABLE motionT ADD FOREIGN KEY(state_id) REFERENCES motion_stateT(id);
ALTER TABLE motionT ADD FOREIGN KEY(recommendation_id) REFERENCES motion_stateT(id);
ALTER TABLE motionT ADD FOREIGN KEY(category_id) REFERENCES motion_categoryT(id);
ALTER TABLE motionT ADD FOREIGN KEY(block_id) REFERENCES motion_blockT(id);
ALTER TABLE motionT ADD FOREIGN KEY(statute_paragraph_id) REFERENCES motion_statute_paragraphT(id);
ALTER TABLE motionT ADD FOREIGN KEY(agenda_item_id) REFERENCES agenda_itemT(id);
ALTER TABLE motionT ADD FOREIGN KEY(list_of_speakers_id) REFERENCES list_of_speakersT(id);
ALTER TABLE motionT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE motion_submitterT ADD FOREIGN KEY(meeting_user_id) REFERENCES meeting_userT(id);
ALTER TABLE motion_submitterT ADD FOREIGN KEY(motion_id) REFERENCES motionT(id);
ALTER TABLE motion_submitterT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE motion_commentT ADD FOREIGN KEY(motion_id) REFERENCES motionT(id);
ALTER TABLE motion_commentT ADD FOREIGN KEY(section_id) REFERENCES motion_comment_sectionT(id);
ALTER TABLE motion_commentT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE motion_comment_sectionT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE motion_categoryT ADD FOREIGN KEY(parent_id) REFERENCES motion_categoryT(id);
ALTER TABLE motion_categoryT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE motion_blockT ADD FOREIGN KEY(agenda_item_id) REFERENCES agenda_itemT(id);
ALTER TABLE motion_blockT ADD FOREIGN KEY(list_of_speakers_id) REFERENCES list_of_speakersT(id);
ALTER TABLE motion_blockT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE motion_change_recommendationT ADD FOREIGN KEY(motion_id) REFERENCES motionT(id);
ALTER TABLE motion_change_recommendationT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE motion_stateT ADD FOREIGN KEY(submitter_withdraw_state_id) REFERENCES motion_stateT(id);
ALTER TABLE motion_stateT ADD FOREIGN KEY(workflow_id) REFERENCES motion_workflowT(id) INITIALLY DEFERRED;
ALTER TABLE motion_stateT ADD FOREIGN KEY(first_state_of_workflow_id) REFERENCES motion_workflowT(id) INITIALLY DEFERRED;
ALTER TABLE motion_stateT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE motion_workflowT ADD FOREIGN KEY(first_state_id) REFERENCES motion_stateT(id) INITIALLY DEFERRED;
ALTER TABLE motion_workflowT ADD FOREIGN KEY(default_workflow_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE motion_workflowT ADD FOREIGN KEY(default_amendment_workflow_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE motion_workflowT ADD FOREIGN KEY(default_statute_amendment_workflow_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE motion_workflowT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;

ALTER TABLE motion_statute_paragraphT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE pollT ADD FOREIGN KEY(global_option_id) REFERENCES optionT(id);
ALTER TABLE pollT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE optionT ADD FOREIGN KEY(poll_id) REFERENCES pollT(id);
ALTER TABLE optionT ADD FOREIGN KEY(used_as_global_option_in_poll_id) REFERENCES pollT(id);
ALTER TABLE optionT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE voteT ADD FOREIGN KEY(option_id) REFERENCES optionT(id);
ALTER TABLE voteT ADD FOREIGN KEY(user_id) REFERENCES userT(id);
ALTER TABLE voteT ADD FOREIGN KEY(delegated_user_id) REFERENCES userT(id);
ALTER TABLE voteT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE assignmentT ADD FOREIGN KEY(agenda_item_id) REFERENCES agenda_itemT(id);
ALTER TABLE assignmentT ADD FOREIGN KEY(list_of_speakers_id) REFERENCES list_of_speakersT(id);
ALTER TABLE assignmentT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE assignment_candidateT ADD FOREIGN KEY(assignment_id) REFERENCES assignmentT(id);
ALTER TABLE assignment_candidateT ADD FOREIGN KEY(meeting_user_id) REFERENCES meeting_userT(id);
ALTER TABLE assignment_candidateT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE poll_candidate_listT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);
ALTER TABLE poll_candidate_listT ADD FOREIGN KEY(option_id) REFERENCES optionT(id);

ALTER TABLE poll_candidateT ADD FOREIGN KEY(poll_candidate_list_id) REFERENCES poll_candidate_listT(id);
ALTER TABLE poll_candidateT ADD FOREIGN KEY(user_id) REFERENCES userT(id);
ALTER TABLE poll_candidateT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE mediafileT ADD FOREIGN KEY(parent_id) REFERENCES mediafileT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(list_of_speakers_id) REFERENCES list_of_speakersT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_logo_projector_main_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_logo_projector_header_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_logo_web_header_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_logo_pdf_header_l_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_logo_pdf_header_r_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_logo_pdf_footer_l_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_logo_pdf_footer_r_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_logo_pdf_ballot_paper_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_font_regular_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_font_italic_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_font_bold_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_font_bold_italic_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_font_monospace_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_font_chyron_speaker_name_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_font_projector_h1_in_meeting_id) REFERENCES meetingT(id);
ALTER TABLE mediafileT ADD FOREIGN KEY(used_as_font_projector_h2_in_meeting_id) REFERENCES meetingT(id);

ALTER TABLE projectorT ADD FOREIGN KEY(used_as_reference_projector_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_agenda_item_list_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_topic_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_list_of_speakers_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_current_los_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_motion_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_amendment_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_motion_block_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_assignment_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_mediafile_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_message_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_countdown_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_assignment_poll_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_motion_poll_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(used_as_default_projector_for_poll_in_meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;
ALTER TABLE projectorT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id) INITIALLY DEFERRED;

ALTER TABLE projectionT ADD FOREIGN KEY(current_projector_id) REFERENCES projectorT(id);
ALTER TABLE projectionT ADD FOREIGN KEY(preview_projector_id) REFERENCES projectorT(id);
ALTER TABLE projectionT ADD FOREIGN KEY(history_projector_id) REFERENCES projectorT(id);
ALTER TABLE projectionT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE projector_messageT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE projector_countdownT ADD FOREIGN KEY(used_as_list_of_speakers_countdown_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector_countdownT ADD FOREIGN KEY(used_as_poll_countdown_meeting_id) REFERENCES meetingT(id);
ALTER TABLE projector_countdownT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE chat_groupT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);

ALTER TABLE chat_messageT ADD FOREIGN KEY(meeting_user_id) REFERENCES meeting_userT(id);
ALTER TABLE chat_messageT ADD FOREIGN KEY(chat_group_id) REFERENCES chat_groupT(id);
ALTER TABLE chat_messageT ADD FOREIGN KEY(meeting_id) REFERENCES meetingT(id);


/*   Relation-list infos 
organization.committee_ids: Type: relation-list -> committee.organization_id: Type: relation, Required:True SQL: False
organization.active_meeting_ids: Type: relation-list -> meeting.is_active_in_organization_id: Type: relation, Required:- SQL: False
organization.archived_meeting_ids: Type: relation-list -> meeting.is_archived_in_organization_id: Type: relation, Required:- SQL: False
organization.template_meeting_ids: Type: relation-list -> meeting.template_for_organization_id: Type: relation, Required:- SQL: False
organization.organization_tag_ids: Type: relation-list -> organization_tag.organization_id: Type: relation, Required:True SQL: False
******* 1:1 without sql:organization.theme_id: Type: relation -> theme.theme_for_organization_id: Type: relation, Required:- SQL: False
organization.theme_ids: Type: relation-list -> theme.organization_id: Type: relation, Required:True SQL: False
organization.mediafile_ids: Type: relation-list -> mediafile.owner_id: Type: generic-relation, Required:True SQL: False
organization.user_ids: Type: relation-list -> user.organization_id: Type: relation, Required:True SQL: False

user.is_present_in_meeting_ids: Type: relation-list -> meeting.present_user_ids: Type: relation-list, Required:- SQL: False
user.committee_ids: Type: relation-list -> committee.user_ids: Type: relation-list, Required:- SQL: False
user.committee_management_ids: Type: relation-list -> committee.manager_ids: Type: relation-list, Required:- SQL: False
user.forwarding_committee_ids: Type: relation-list -> committee.forwarding_user_id: Type: relation, Required:- SQL: False
user.meeting_user_ids: Type: relation-list -> meeting_user.user_id: Type: relation, Required:True SQL: False
user.poll_voted_ids: Type: relation-list -> poll.voted_ids: Type: relation-list, Required:- SQL: False
user.option_ids: Type: relation-list -> option.content_object_id: Type: generic-relation, Required:- SQL: False
user.vote_ids: Type: relation-list -> vote.user_id: Type: relation, Required:- SQL: False
user.delegated_vote_ids: Type: relation-list -> vote.delegated_user_id: Type: relation, Required:- SQL: False
user.poll_candidate_ids: Type: relation-list -> poll_candidate.user_id: Type: relation, Required:- SQL: False
user.organization_id: Type: relation -> organization.user_ids: Type: relation-list, Required:- SQL: False

meeting_user.user_id: Type: relation -> user.meeting_user_ids: Type: relation-list, Required:- SQL: False
meeting_user.meeting_id: Type: relation -> meeting.meeting_user_ids: Type: relation-list, Required:- SQL: False
meeting_user.personal_note_ids: Type: relation-list -> personal_note.meeting_user_id: Type: relation, Required:True SQL: False
meeting_user.speaker_ids: Type: relation-list -> speaker.meeting_user_id: Type: relation, Required:- SQL: False
meeting_user.supported_motion_ids: Type: relation-list -> motion.supporter_meeting_user_ids: Type: relation-list, Required:- SQL: False
meeting_user.motion_submitter_ids: Type: relation-list -> motion_submitter.meeting_user_id: Type: relation, Required:True SQL: False
meeting_user.assignment_candidate_ids: Type: relation-list -> assignment_candidate.meeting_user_id: Type: relation, Required:- SQL: False
meeting_user.vote_delegated_to_id: Type: relation -> meeting_user.vote_delegations_from_ids: Type: relation-list, Required:- SQL: False
meeting_user.vote_delegations_from_ids: Type: relation-list -> meeting_user.vote_delegated_to_id: Type: relation, Required:- SQL: False
meeting_user.chat_message_ids: Type: relation-list -> chat_message.meeting_user_id: Type: relation, Required:True SQL: False
meeting_user.group_ids: Type: relation-list -> group.meeting_user_ids: Type: relation-list, Required:- SQL: False

organization_tag.organization_id: Type: relation -> organization.organization_tag_ids: Type: relation-list, Required:- SQL: False

******* 1:1 without sql:theme.theme_for_organization_id: Type: relation -> organization.theme_id: Type: relation, Required:True SQL: False
theme.organization_id: Type: relation -> organization.theme_ids: Type: relation-list, Required:- SQL: False

committee.meeting_ids: Type: relation-list -> meeting.committee_id: Type: relation, Required:True SQL: False
******* 1:1 without sql:committee.default_meeting_id: Type: relation -> meeting.default_meeting_for_committee_id: Type: relation, Required:- SQL: False
committee.user_ids: Type: relation-list -> user.committee_ids: Type: relation-list, Required:- SQL: False
committee.manager_ids: Type: relation-list -> user.committee_management_ids: Type: relation-list, Required:- SQL: False
committee.forward_to_committee_ids: Type: relation-list -> committee.receive_forwardings_from_committee_ids: Type: relation-list, Required:- SQL: False
committee.receive_forwardings_from_committee_ids: Type: relation-list -> committee.forward_to_committee_ids: Type: relation-list, Required:- SQL: False
committee.forwarding_user_id: Type: relation -> user.forwarding_committee_ids: Type: relation-list, Required:- SQL: False
committee.organization_tag_ids: Type: relation-list -> organization_tag.tagged_ids: Type: generic-relation-list, Required:- SQL: False
committee.organization_id: Type: relation -> organization.committee_ids: Type: relation-list, Required:- SQL: False

meeting.is_active_in_organization_id: Type: relation -> organization.active_meeting_ids: Type: relation-list, Required:- SQL: False
meeting.is_archived_in_organization_id: Type: relation -> organization.archived_meeting_ids: Type: relation-list, Required:- SQL: False
meeting.template_for_organization_id: Type: relation -> organization.template_meeting_ids: Type: relation-list, Required:- SQL: False
******* 1:1 without sql:meeting.motions_default_workflow_id: Type: relation -> motion_workflow.default_workflow_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.motions_default_amendment_workflow_id: Type: relation -> motion_workflow.default_amendment_workflow_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.motions_default_statute_amendment_workflow_id: Type: relation -> motion_workflow.default_statute_amendment_workflow_meeting_id: Type: relation, Required:- SQL: False
meeting.motion_poll_default_group_ids: Type: relation-list -> group.used_as_motion_poll_default_id: Type: relation, Required:- SQL: False
meeting.poll_candidate_list_ids: Type: relation-list -> poll_candidate_list.meeting_id: Type: relation, Required:True SQL: False
meeting.poll_candidate_ids: Type: relation-list -> poll_candidate.meeting_id: Type: relation, Required:True SQL: False
meeting.meeting_user_ids: Type: relation-list -> meeting_user.meeting_id: Type: relation, Required:True SQL: False
meeting.assignment_poll_default_group_ids: Type: relation-list -> group.used_as_assignment_poll_default_id: Type: relation, Required:- SQL: False
meeting.poll_default_group_ids: Type: relation-list -> group.used_as_poll_default_id: Type: relation, Required:- SQL: False
meeting.topic_poll_default_group_ids: Type: relation-list -> group.used_as_topic_poll_default_id: Type: relation, Required:- SQL: False
meeting.projector_ids: Type: relation-list -> projector.meeting_id: Type: relation, Required:True SQL: False
meeting.all_projection_ids: Type: relation-list -> projection.meeting_id: Type: relation, Required:True SQL: False
meeting.projector_message_ids: Type: relation-list -> projector_message.meeting_id: Type: relation, Required:True SQL: False
meeting.projector_countdown_ids: Type: relation-list -> projector_countdown.meeting_id: Type: relation, Required:True SQL: False
meeting.tag_ids: Type: relation-list -> tag.meeting_id: Type: relation, Required:True SQL: False
meeting.agenda_item_ids: Type: relation-list -> agenda_item.meeting_id: Type: relation, Required:True SQL: False
meeting.list_of_speakers_ids: Type: relation-list -> list_of_speakers.meeting_id: Type: relation, Required:True SQL: False
meeting.point_of_order_category_ids: Type: relation-list -> point_of_order_category.meeting_id: Type: relation, Required:True SQL: False
meeting.speaker_ids: Type: relation-list -> speaker.meeting_id: Type: relation, Required:True SQL: False
meeting.topic_ids: Type: relation-list -> topic.meeting_id: Type: relation, Required:True SQL: False
meeting.group_ids: Type: relation-list -> group.meeting_id: Type: relation, Required:True SQL: False
meeting.mediafile_ids: Type: relation-list -> mediafile.owner_id: Type: generic-relation, Required:True SQL: False
meeting.motion_ids: Type: relation-list -> motion.meeting_id: Type: relation, Required:True SQL: False
meeting.forwarded_motion_ids: Type: relation-list -> motion.origin_meeting_id: Type: relation, Required:- SQL: False
meeting.motion_comment_section_ids: Type: relation-list -> motion_comment_section.meeting_id: Type: relation, Required:True SQL: False
meeting.motion_category_ids: Type: relation-list -> motion_category.meeting_id: Type: relation, Required:True SQL: False
meeting.motion_block_ids: Type: relation-list -> motion_block.meeting_id: Type: relation, Required:True SQL: False
meeting.motion_workflow_ids: Type: relation-list -> motion_workflow.meeting_id: Type: relation, Required:True SQL: False
meeting.motion_statute_paragraph_ids: Type: relation-list -> motion_statute_paragraph.meeting_id: Type: relation, Required:True SQL: False
meeting.motion_comment_ids: Type: relation-list -> motion_comment.meeting_id: Type: relation, Required:True SQL: False
meeting.motion_submitter_ids: Type: relation-list -> motion_submitter.meeting_id: Type: relation, Required:True SQL: False
meeting.motion_change_recommendation_ids: Type: relation-list -> motion_change_recommendation.meeting_id: Type: relation, Required:True SQL: False
meeting.motion_state_ids: Type: relation-list -> motion_state.meeting_id: Type: relation, Required:True SQL: False
meeting.poll_ids: Type: relation-list -> poll.meeting_id: Type: relation, Required:True SQL: False
meeting.option_ids: Type: relation-list -> option.meeting_id: Type: relation, Required:True SQL: False
meeting.vote_ids: Type: relation-list -> vote.meeting_id: Type: relation, Required:True SQL: False
meeting.assignment_ids: Type: relation-list -> assignment.meeting_id: Type: relation, Required:True SQL: False
meeting.assignment_candidate_ids: Type: relation-list -> assignment_candidate.meeting_id: Type: relation, Required:True SQL: False
meeting.personal_note_ids: Type: relation-list -> personal_note.meeting_id: Type: relation, Required:True SQL: False
meeting.chat_group_ids: Type: relation-list -> chat_group.meeting_id: Type: relation, Required:True SQL: False
meeting.chat_message_ids: Type: relation-list -> chat_message.meeting_id: Type: relation, Required:True SQL: False
******* 1:1 without sql:meeting.logo_projector_main_id: Type: relation -> mediafile.used_as_logo_projector_main_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.logo_projector_header_id: Type: relation -> mediafile.used_as_logo_projector_header_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.logo_web_header_id: Type: relation -> mediafile.used_as_logo_web_header_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.logo_pdf_header_l_id: Type: relation -> mediafile.used_as_logo_pdf_header_l_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.logo_pdf_header_r_id: Type: relation -> mediafile.used_as_logo_pdf_header_r_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.logo_pdf_footer_l_id: Type: relation -> mediafile.used_as_logo_pdf_footer_l_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.logo_pdf_footer_r_id: Type: relation -> mediafile.used_as_logo_pdf_footer_r_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.logo_pdf_ballot_paper_id: Type: relation -> mediafile.used_as_logo_pdf_ballot_paper_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.font_regular_id: Type: relation -> mediafile.used_as_font_regular_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.font_italic_id: Type: relation -> mediafile.used_as_font_italic_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.font_bold_id: Type: relation -> mediafile.used_as_font_bold_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.font_bold_italic_id: Type: relation -> mediafile.used_as_font_bold_italic_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.font_monospace_id: Type: relation -> mediafile.used_as_font_monospace_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.font_chyron_speaker_name_id: Type: relation -> mediafile.used_as_font_chyron_speaker_name_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.font_projector_h1_id: Type: relation -> mediafile.used_as_font_projector_h1_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.font_projector_h2_id: Type: relation -> mediafile.used_as_font_projector_h2_in_meeting_id: Type: relation, Required:- SQL: False
meeting.committee_id: Type: relation -> committee.meeting_ids: Type: relation-list, Required:- SQL: False
******* 1:1 without sql:meeting.default_meeting_for_committee_id: Type: relation -> committee.default_meeting_id: Type: relation, Required:- SQL: False
meeting.organization_tag_ids: Type: relation-list -> organization_tag.tagged_ids: Type: generic-relation-list, Required:- SQL: False
meeting.present_user_ids: Type: relation-list -> user.is_present_in_meeting_ids: Type: relation-list, Required:- SQL: False
******* 1:1 without sql:meeting.reference_projector_id: Type: relation -> projector.used_as_reference_projector_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.list_of_speakers_countdown_id: Type: relation -> projector_countdown.used_as_list_of_speakers_countdown_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.poll_countdown_id: Type: relation -> projector_countdown.used_as_poll_countdown_meeting_id: Type: relation, Required:- SQL: False
meeting.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
meeting.default_projector_agenda_item_list_ids: Type: relation-list -> projector.used_as_default_projector_for_agenda_item_list_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_topic_ids: Type: relation-list -> projector.used_as_default_projector_for_topic_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_list_of_speakers_ids: Type: relation-list -> projector.used_as_default_projector_for_list_of_speakers_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_current_list_of_speakers_ids: Type: relation-list -> projector.used_as_default_projector_for_current_los_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_motion_ids: Type: relation-list -> projector.used_as_default_projector_for_motion_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_amendment_ids: Type: relation-list -> projector.used_as_default_projector_for_amendment_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_motion_block_ids: Type: relation-list -> projector.used_as_default_projector_for_motion_block_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_assignment_ids: Type: relation-list -> projector.used_as_default_projector_for_assignment_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_mediafile_ids: Type: relation-list -> projector.used_as_default_projector_for_mediafile_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_message_ids: Type: relation-list -> projector.used_as_default_projector_for_message_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_countdown_ids: Type: relation-list -> projector.used_as_default_projector_for_countdown_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_assignment_poll_ids: Type: relation-list -> projector.used_as_default_projector_for_assignment_poll_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_motion_poll_ids: Type: relation-list -> projector.used_as_default_projector_for_motion_poll_in_meeting_id: Type: relation, Required:- SQL: False
meeting.default_projector_poll_ids: Type: relation-list -> projector.used_as_default_projector_for_poll_in_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.default_group_id: Type: relation -> group.default_group_for_meeting_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:meeting.admin_group_id: Type: relation -> group.admin_group_for_meeting_id: Type: relation, Required:- SQL: False

group.meeting_user_ids: Type: relation-list -> meeting_user.group_ids: Type: relation-list, Required:- SQL: False
******* 1:1 without sql:group.default_group_for_meeting_id: Type: relation -> meeting.default_group_id: Type: relation, Required:True SQL: False
******* 1:1 without sql:group.admin_group_for_meeting_id: Type: relation -> meeting.admin_group_id: Type: relation, Required:- SQL: False
group.mediafile_access_group_ids: Type: relation-list -> mediafile.access_group_ids: Type: relation-list, Required:- SQL: False
group.mediafile_inherited_access_group_ids: Type: relation-list -> mediafile.inherited_access_group_ids: Type: relation-list, Required:- SQL: False
group.read_comment_section_ids: Type: relation-list -> motion_comment_section.read_group_ids: Type: relation-list, Required:- SQL: False
group.write_comment_section_ids: Type: relation-list -> motion_comment_section.write_group_ids: Type: relation-list, Required:- SQL: False
group.read_chat_group_ids: Type: relation-list -> chat_group.read_group_ids: Type: relation-list, Required:- SQL: False
group.write_chat_group_ids: Type: relation-list -> chat_group.write_group_ids: Type: relation-list, Required:- SQL: False
group.poll_ids: Type: relation-list -> poll.entitled_group_ids: Type: relation-list, Required:- SQL: False
group.used_as_motion_poll_default_id: Type: relation -> meeting.motion_poll_default_group_ids: Type: relation-list, Required:- SQL: False
group.used_as_assignment_poll_default_id: Type: relation -> meeting.assignment_poll_default_group_ids: Type: relation-list, Required:- SQL: False
group.used_as_topic_poll_default_id: Type: relation -> meeting.topic_poll_default_group_ids: Type: relation-list, Required:- SQL: False
group.used_as_poll_default_id: Type: relation -> meeting.poll_default_group_ids: Type: relation-list, Required:- SQL: False
group.meeting_id: Type: relation -> meeting.group_ids: Type: relation-list, Required:- SQL: False

personal_note.meeting_user_id: Type: relation -> meeting_user.personal_note_ids: Type: relation-list, Required:- SQL: False
personal_note.meeting_id: Type: relation -> meeting.personal_note_ids: Type: relation-list, Required:- SQL: False

tag.meeting_id: Type: relation -> meeting.tag_ids: Type: relation-list, Required:- SQL: False

agenda_item.parent_id: Type: relation -> agenda_item.child_ids: Type: relation-list, Required:- SQL: False
agenda_item.child_ids: Type: relation-list -> agenda_item.parent_id: Type: relation, Required:- SQL: False
agenda_item.tag_ids: Type: relation-list -> tag.tagged_ids: Type: generic-relation-list, Required:- SQL: False
agenda_item.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
agenda_item.meeting_id: Type: relation -> meeting.agenda_item_ids: Type: relation-list, Required:- SQL: False

list_of_speakers.speaker_ids: Type: relation-list -> speaker.list_of_speakers_id: Type: relation, Required:True SQL: False
list_of_speakers.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
list_of_speakers.meeting_id: Type: relation -> meeting.list_of_speakers_ids: Type: relation-list, Required:- SQL: False

point_of_order_category.meeting_id: Type: relation -> meeting.point_of_order_category_ids: Type: relation-list, Required:- SQL: False
point_of_order_category.speaker_ids: Type: relation-list -> speaker.point_of_order_category_id: Type: relation, Required:- SQL: False

speaker.list_of_speakers_id: Type: relation -> list_of_speakers.speaker_ids: Type: relation-list, Required:- SQL: False
speaker.meeting_user_id: Type: relation -> meeting_user.speaker_ids: Type: relation-list, Required:- SQL: False
speaker.point_of_order_category_id: Type: relation -> point_of_order_category.speaker_ids: Type: relation-list, Required:- SQL: False
speaker.meeting_id: Type: relation -> meeting.speaker_ids: Type: relation-list, Required:- SQL: False

topic.attachment_ids: Type: relation-list -> mediafile.attachment_ids: Type: generic-relation-list, Required:- SQL: False
topic.agenda_item_id: Type: relation -> agenda_item.content_object_id: Type: generic-relation, Required:True SQL: False
topic.list_of_speakers_id: Type: relation -> list_of_speakers.content_object_id: Type: generic-relation, Required:True SQL: False
topic.poll_ids: Type: relation-list -> poll.content_object_id: Type: generic-relation, Required:True SQL: False
topic.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
topic.meeting_id: Type: relation -> meeting.topic_ids: Type: relation-list, Required:- SQL: False

motion.lead_motion_id: Type: relation -> motion.amendment_ids: Type: relation-list, Required:- SQL: False
motion.amendment_ids: Type: relation-list -> motion.lead_motion_id: Type: relation, Required:- SQL: False
motion.sort_parent_id: Type: relation -> motion.sort_child_ids: Type: relation-list, Required:- SQL: False
motion.sort_child_ids: Type: relation-list -> motion.sort_parent_id: Type: relation, Required:- SQL: False
motion.origin_id: Type: relation -> motion.derived_motion_ids: Type: relation-list, Required:- SQL: False
motion.origin_meeting_id: Type: relation -> meeting.forwarded_motion_ids: Type: relation-list, Required:- SQL: False
motion.derived_motion_ids: Type: relation-list -> motion.origin_id: Type: relation, Required:- SQL: False
motion.all_origin_ids: Type: relation-list -> motion.all_derived_motion_ids: Type: relation-list, Required:- SQL: False
motion.all_derived_motion_ids: Type: relation-list -> motion.all_origin_ids: Type: relation-list, Required:- SQL: False
motion.state_id: Type: relation -> motion_state.motion_ids: Type: relation-list, Required:- SQL: False
motion.recommendation_id: Type: relation -> motion_state.motion_recommendation_ids: Type: relation-list, Required:- SQL: False
motion.referenced_in_motion_state_extension_ids: Type: relation-list -> motion.state_extension_reference_ids: Type: generic-relation-list, Required:- SQL: False
motion.referenced_in_motion_recommendation_extension_ids: Type: relation-list -> motion.recommendation_extension_reference_ids: Type: generic-relation-list, Required:- SQL: False
motion.category_id: Type: relation -> motion_category.motion_ids: Type: relation-list, Required:- SQL: False
motion.block_id: Type: relation -> motion_block.motion_ids: Type: relation-list, Required:- SQL: False
motion.submitter_ids: Type: relation-list -> motion_submitter.motion_id: Type: relation, Required:True SQL: False
motion.supporter_meeting_user_ids: Type: relation-list -> meeting_user.supported_motion_ids: Type: relation-list, Required:- SQL: False
motion.poll_ids: Type: relation-list -> poll.content_object_id: Type: generic-relation, Required:True SQL: False
motion.option_ids: Type: relation-list -> option.content_object_id: Type: generic-relation, Required:- SQL: False
motion.change_recommendation_ids: Type: relation-list -> motion_change_recommendation.motion_id: Type: relation, Required:True SQL: False
motion.statute_paragraph_id: Type: relation -> motion_statute_paragraph.motion_ids: Type: relation-list, Required:- SQL: False
motion.comment_ids: Type: relation-list -> motion_comment.motion_id: Type: relation, Required:True SQL: False
motion.agenda_item_id: Type: relation -> agenda_item.content_object_id: Type: generic-relation, Required:True SQL: False
motion.list_of_speakers_id: Type: relation -> list_of_speakers.content_object_id: Type: generic-relation, Required:True SQL: False
motion.tag_ids: Type: relation-list -> tag.tagged_ids: Type: generic-relation-list, Required:- SQL: False
motion.attachment_ids: Type: relation-list -> mediafile.attachment_ids: Type: generic-relation-list, Required:- SQL: False
motion.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
motion.personal_note_ids: Type: relation-list -> personal_note.content_object_id: Type: generic-relation, Required:- SQL: False
motion.meeting_id: Type: relation -> meeting.motion_ids: Type: relation-list, Required:- SQL: False

motion_submitter.meeting_user_id: Type: relation -> meeting_user.motion_submitter_ids: Type: relation-list, Required:- SQL: False
motion_submitter.motion_id: Type: relation -> motion.submitter_ids: Type: relation-list, Required:- SQL: False
motion_submitter.meeting_id: Type: relation -> meeting.motion_submitter_ids: Type: relation-list, Required:- SQL: False

motion_comment.motion_id: Type: relation -> motion.comment_ids: Type: relation-list, Required:- SQL: False
motion_comment.section_id: Type: relation -> motion_comment_section.comment_ids: Type: relation-list, Required:- SQL: False
motion_comment.meeting_id: Type: relation -> meeting.motion_comment_ids: Type: relation-list, Required:- SQL: False

motion_comment_section.comment_ids: Type: relation-list -> motion_comment.section_id: Type: relation, Required:True SQL: False
motion_comment_section.read_group_ids: Type: relation-list -> group.read_comment_section_ids: Type: relation-list, Required:- SQL: False
motion_comment_section.write_group_ids: Type: relation-list -> group.write_comment_section_ids: Type: relation-list, Required:- SQL: False
motion_comment_section.meeting_id: Type: relation -> meeting.motion_comment_section_ids: Type: relation-list, Required:- SQL: False

motion_category.parent_id: Type: relation -> motion_category.child_ids: Type: relation-list, Required:- SQL: False
motion_category.child_ids: Type: relation-list -> motion_category.parent_id: Type: relation, Required:- SQL: False
motion_category.motion_ids: Type: relation-list -> motion.category_id: Type: relation, Required:- SQL: False
motion_category.meeting_id: Type: relation -> meeting.motion_category_ids: Type: relation-list, Required:- SQL: False

motion_block.motion_ids: Type: relation-list -> motion.block_id: Type: relation, Required:- SQL: False
motion_block.agenda_item_id: Type: relation -> agenda_item.content_object_id: Type: generic-relation, Required:True SQL: False
motion_block.list_of_speakers_id: Type: relation -> list_of_speakers.content_object_id: Type: generic-relation, Required:True SQL: False
motion_block.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
motion_block.meeting_id: Type: relation -> meeting.motion_block_ids: Type: relation-list, Required:- SQL: False

motion_change_recommendation.motion_id: Type: relation -> motion.change_recommendation_ids: Type: relation-list, Required:- SQL: False
motion_change_recommendation.meeting_id: Type: relation -> meeting.motion_change_recommendation_ids: Type: relation-list, Required:- SQL: False

motion_state.submitter_withdraw_state_id: Type: relation -> motion_state.submitter_withdraw_back_ids: Type: relation-list, Required:- SQL: False
motion_state.submitter_withdraw_back_ids: Type: relation-list -> motion_state.submitter_withdraw_state_id: Type: relation, Required:- SQL: False
motion_state.next_state_ids: Type: relation-list -> motion_state.previous_state_ids: Type: relation-list, Required:- SQL: False
motion_state.previous_state_ids: Type: relation-list -> motion_state.next_state_ids: Type: relation-list, Required:- SQL: False
motion_state.motion_ids: Type: relation-list -> motion.state_id: Type: relation, Required:True SQL: False
motion_state.motion_recommendation_ids: Type: relation-list -> motion.recommendation_id: Type: relation, Required:- SQL: False
motion_state.workflow_id: Type: relation -> motion_workflow.state_ids: Type: relation-list, Required:- SQL: False
******* 1:1 without sql:motion_state.first_state_of_workflow_id: Type: relation -> motion_workflow.first_state_id: Type: relation, Required:True SQL: False
motion_state.meeting_id: Type: relation -> meeting.motion_state_ids: Type: relation-list, Required:- SQL: False

motion_workflow.state_ids: Type: relation-list -> motion_state.workflow_id: Type: relation, Required:True SQL: False
******* 1:1 without sql:motion_workflow.first_state_id: Type: relation -> motion_state.first_state_of_workflow_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:motion_workflow.default_workflow_meeting_id: Type: relation -> meeting.motions_default_workflow_id: Type: relation, Required:True SQL: False
******* 1:1 without sql:motion_workflow.default_amendment_workflow_meeting_id: Type: relation -> meeting.motions_default_amendment_workflow_id: Type: relation, Required:True SQL: False
******* 1:1 without sql:motion_workflow.default_statute_amendment_workflow_meeting_id: Type: relation -> meeting.motions_default_statute_amendment_workflow_id: Type: relation, Required:True SQL: False
motion_workflow.meeting_id: Type: relation -> meeting.motion_workflow_ids: Type: relation-list, Required:- SQL: False

motion_statute_paragraph.motion_ids: Type: relation-list -> motion.statute_paragraph_id: Type: relation, Required:- SQL: False
motion_statute_paragraph.meeting_id: Type: relation -> meeting.motion_statute_paragraph_ids: Type: relation-list, Required:- SQL: False

poll.option_ids: Type: relation-list -> option.poll_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:poll.global_option_id: Type: relation -> option.used_as_global_option_in_poll_id: Type: relation, Required:- SQL: False
poll.voted_ids: Type: relation-list -> user.poll_voted_ids: Type: relation-list, Required:- SQL: False
poll.entitled_group_ids: Type: relation-list -> group.poll_ids: Type: relation-list, Required:- SQL: False
poll.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
poll.meeting_id: Type: relation -> meeting.poll_ids: Type: relation-list, Required:- SQL: False

option.poll_id: Type: relation -> poll.option_ids: Type: relation-list, Required:- SQL: False
******* 1:1 without sql:option.used_as_global_option_in_poll_id: Type: relation -> poll.global_option_id: Type: relation, Required:- SQL: False
option.vote_ids: Type: relation-list -> vote.option_id: Type: relation, Required:True SQL: False
option.meeting_id: Type: relation -> meeting.option_ids: Type: relation-list, Required:- SQL: False

vote.option_id: Type: relation -> option.vote_ids: Type: relation-list, Required:- SQL: False
vote.user_id: Type: relation -> user.vote_ids: Type: relation-list, Required:- SQL: False
vote.delegated_user_id: Type: relation -> user.delegated_vote_ids: Type: relation-list, Required:- SQL: False
vote.meeting_id: Type: relation -> meeting.vote_ids: Type: relation-list, Required:- SQL: False

assignment.candidate_ids: Type: relation-list -> assignment_candidate.assignment_id: Type: relation, Required:True SQL: False
assignment.poll_ids: Type: relation-list -> poll.content_object_id: Type: generic-relation, Required:True SQL: False
assignment.agenda_item_id: Type: relation -> agenda_item.content_object_id: Type: generic-relation, Required:True SQL: False
assignment.list_of_speakers_id: Type: relation -> list_of_speakers.content_object_id: Type: generic-relation, Required:True SQL: False
assignment.tag_ids: Type: relation-list -> tag.tagged_ids: Type: generic-relation-list, Required:- SQL: False
assignment.attachment_ids: Type: relation-list -> mediafile.attachment_ids: Type: generic-relation-list, Required:- SQL: False
assignment.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
assignment.meeting_id: Type: relation -> meeting.assignment_ids: Type: relation-list, Required:- SQL: False

assignment_candidate.assignment_id: Type: relation -> assignment.candidate_ids: Type: relation-list, Required:- SQL: False
assignment_candidate.meeting_user_id: Type: relation -> meeting_user.assignment_candidate_ids: Type: relation-list, Required:- SQL: False
assignment_candidate.meeting_id: Type: relation -> meeting.assignment_candidate_ids: Type: relation-list, Required:- SQL: False

poll_candidate_list.poll_candidate_ids: Type: relation-list -> poll_candidate.poll_candidate_list_id: Type: relation, Required:True SQL: False
poll_candidate_list.meeting_id: Type: relation -> meeting.poll_candidate_list_ids: Type: relation-list, Required:- SQL: False
poll_candidate_list.option_id: Type: relation -> option.content_object_id: Type: generic-relation, Required:- SQL: False

poll_candidate.poll_candidate_list_id: Type: relation -> poll_candidate_list.poll_candidate_ids: Type: relation-list, Required:- SQL: False
poll_candidate.user_id: Type: relation -> user.poll_candidate_ids: Type: relation-list, Required:- SQL: False
poll_candidate.meeting_id: Type: relation -> meeting.poll_candidate_ids: Type: relation-list, Required:- SQL: False

mediafile.inherited_access_group_ids: Type: relation-list -> group.mediafile_inherited_access_group_ids: Type: relation-list, Required:- SQL: False
mediafile.access_group_ids: Type: relation-list -> group.mediafile_access_group_ids: Type: relation-list, Required:- SQL: False
mediafile.parent_id: Type: relation -> mediafile.child_ids: Type: relation-list, Required:- SQL: False
mediafile.child_ids: Type: relation-list -> mediafile.parent_id: Type: relation, Required:- SQL: False
mediafile.list_of_speakers_id: Type: relation -> list_of_speakers.content_object_id: Type: generic-relation, Required:True SQL: False
mediafile.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
******* 1:1 without sql:mediafile.used_as_logo_projector_main_in_meeting_id: Type: relation -> meeting.logo_projector_main_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_logo_projector_header_in_meeting_id: Type: relation -> meeting.logo_projector_header_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_logo_web_header_in_meeting_id: Type: relation -> meeting.logo_web_header_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_logo_pdf_header_l_in_meeting_id: Type: relation -> meeting.logo_pdf_header_l_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_logo_pdf_header_r_in_meeting_id: Type: relation -> meeting.logo_pdf_header_r_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_logo_pdf_footer_l_in_meeting_id: Type: relation -> meeting.logo_pdf_footer_l_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_logo_pdf_footer_r_in_meeting_id: Type: relation -> meeting.logo_pdf_footer_r_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_logo_pdf_ballot_paper_in_meeting_id: Type: relation -> meeting.logo_pdf_ballot_paper_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_font_regular_in_meeting_id: Type: relation -> meeting.font_regular_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_font_italic_in_meeting_id: Type: relation -> meeting.font_italic_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_font_bold_in_meeting_id: Type: relation -> meeting.font_bold_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_font_bold_italic_in_meeting_id: Type: relation -> meeting.font_bold_italic_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_font_monospace_in_meeting_id: Type: relation -> meeting.font_monospace_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_font_chyron_speaker_name_in_meeting_id: Type: relation -> meeting.font_chyron_speaker_name_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_font_projector_h1_in_meeting_id: Type: relation -> meeting.font_projector_h1_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:mediafile.used_as_font_projector_h2_in_meeting_id: Type: relation -> meeting.font_projector_h2_id: Type: relation, Required:- SQL: False

projector.current_projection_ids: Type: relation-list -> projection.current_projector_id: Type: relation, Required:- SQL: False
projector.preview_projection_ids: Type: relation-list -> projection.preview_projector_id: Type: relation, Required:- SQL: False
projector.history_projection_ids: Type: relation-list -> projection.history_projector_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:projector.used_as_reference_projector_meeting_id: Type: relation -> meeting.reference_projector_id: Type: relation, Required:True SQL: False
projector.used_as_default_projector_for_agenda_item_list_in_meeting_id: Type: relation -> meeting.default_projector_agenda_item_list_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_topic_in_meeting_id: Type: relation -> meeting.default_projector_topic_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_list_of_speakers_in_meeting_id: Type: relation -> meeting.default_projector_list_of_speakers_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_current_los_in_meeting_id: Type: relation -> meeting.default_projector_current_list_of_speakers_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_motion_in_meeting_id: Type: relation -> meeting.default_projector_motion_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_amendment_in_meeting_id: Type: relation -> meeting.default_projector_amendment_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_motion_block_in_meeting_id: Type: relation -> meeting.default_projector_motion_block_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_assignment_in_meeting_id: Type: relation -> meeting.default_projector_assignment_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_mediafile_in_meeting_id: Type: relation -> meeting.default_projector_mediafile_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_message_in_meeting_id: Type: relation -> meeting.default_projector_message_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_countdown_in_meeting_id: Type: relation -> meeting.default_projector_countdown_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_assignment_poll_in_meeting_id: Type: relation -> meeting.default_projector_assignment_poll_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_motion_poll_in_meeting_id: Type: relation -> meeting.default_projector_motion_poll_ids: Type: relation-list, Required:True SQL: False
projector.used_as_default_projector_for_poll_in_meeting_id: Type: relation -> meeting.default_projector_poll_ids: Type: relation-list, Required:True SQL: False
projector.meeting_id: Type: relation -> meeting.projector_ids: Type: relation-list, Required:- SQL: False

projection.current_projector_id: Type: relation -> projector.current_projection_ids: Type: relation-list, Required:- SQL: False
projection.preview_projector_id: Type: relation -> projector.preview_projection_ids: Type: relation-list, Required:- SQL: False
projection.history_projector_id: Type: relation -> projector.history_projection_ids: Type: relation-list, Required:- SQL: False
projection.meeting_id: Type: relation -> meeting.all_projection_ids: Type: relation-list, Required:- SQL: False

projector_message.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
projector_message.meeting_id: Type: relation -> meeting.projector_message_ids: Type: relation-list, Required:- SQL: False

projector_countdown.projection_ids: Type: relation-list -> projection.content_object_id: Type: generic-relation, Required:True SQL: False
******* 1:1 without sql:projector_countdown.used_as_list_of_speakers_countdown_meeting_id: Type: relation -> meeting.list_of_speakers_countdown_id: Type: relation, Required:- SQL: False
******* 1:1 without sql:projector_countdown.used_as_poll_countdown_meeting_id: Type: relation -> meeting.poll_countdown_id: Type: relation, Required:- SQL: False
projector_countdown.meeting_id: Type: relation -> meeting.projector_countdown_ids: Type: relation-list, Required:- SQL: False

chat_group.chat_message_ids: Type: relation-list -> chat_message.chat_group_id: Type: relation, Required:True SQL: False
chat_group.read_group_ids: Type: relation-list -> group.read_chat_group_ids: Type: relation-list, Required:- SQL: False
chat_group.write_group_ids: Type: relation-list -> group.write_chat_group_ids: Type: relation-list, Required:- SQL: False
chat_group.meeting_id: Type: relation -> meeting.chat_group_ids: Type: relation-list, Required:- SQL: False

chat_message.meeting_user_id: Type: relation -> meeting_user.chat_message_ids: Type: relation-list, Required:- SQL: False
chat_message.chat_group_id: Type: relation -> chat_group.chat_message_ids: Type: relation-list, Required:- SQL: False
chat_message.meeting_id: Type: relation -> meeting.chat_message_ids: Type: relation-list, Required:- SQL: False


*/
/*   Missing attribute handling for to, reference, on_delete, equal_fields */