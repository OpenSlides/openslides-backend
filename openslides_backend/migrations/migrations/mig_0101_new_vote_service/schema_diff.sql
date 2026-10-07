-- EDIT SECTION --
ALTER TYPE enum_group_permissions RENAME VALUE 'poll.can_manage' TO 'agenda_item.can_manage_polls';

-- REMOVE SECTION --
DROP TABLE option_t CASCADE;
DROP TABLE poll_candidate_t CASCADE;
DROP TABLE poll_candidate_list_t CASCADE;
DROP TABLE vote_t CASCADE;
ALTER TABLE group_t DROP COLUMN used_as_motion_poll_default_id CASCADE;
ALTER TABLE group_t DROP COLUMN used_as_assignment_poll_default_id CASCADE;
ALTER TABLE group_t DROP COLUMN used_as_topic_poll_default_id CASCADE;
ALTER TABLE group_t DROP COLUMN used_as_poll_default_id CASCADE;
ALTER TABLE history_entry_t DROP CONSTRAINT valid_history_entry_model_id_part1;
ALTER TABLE meeting_t DROP COLUMN motion_poll_ballot_paper_selection CASCADE;
ALTER TABLE meeting_t DROP COLUMN motion_poll_ballot_paper_number CASCADE;
ALTER TABLE meeting_t DROP COLUMN motion_poll_default_type CASCADE;
ALTER TABLE meeting_t DROP COLUMN motion_poll_default_method CASCADE;
ALTER TABLE meeting_t DROP COLUMN motion_poll_default_onehundred_percent_base CASCADE;
ALTER TABLE meeting_t DROP COLUMN motion_poll_default_backend CASCADE;
ALTER TABLE meeting_t DROP COLUMN motion_poll_projection_name_order_first CASCADE;
ALTER TABLE meeting_t DROP COLUMN motion_poll_projection_max_columns CASCADE;
ALTER TABLE meeting_t DROP COLUMN assignment_poll_ballot_paper_selection CASCADE;
ALTER TABLE meeting_t DROP COLUMN assignment_poll_ballot_paper_number CASCADE;
ALTER TABLE meeting_t DROP COLUMN assignment_poll_enable_max_votes_per_option CASCADE;
ALTER TABLE meeting_t DROP COLUMN assignment_poll_sort_poll_result_by_votes CASCADE;
ALTER TABLE meeting_t DROP COLUMN assignment_poll_default_method CASCADE;
ALTER TABLE meeting_t DROP COLUMN assignment_poll_default_type CASCADE;
ALTER TABLE meeting_t DROP COLUMN assignment_poll_default_onehundred_percent_base CASCADE;
ALTER TABLE meeting_t DROP COLUMN assignment_poll_default_backend CASCADE;
ALTER TABLE meeting_t DROP COLUMN poll_ballot_paper_selection CASCADE;
ALTER TABLE meeting_t DROP COLUMN poll_ballot_paper_number CASCADE;
ALTER TABLE meeting_t DROP COLUMN poll_sort_poll_result_by_votes CASCADE;
ALTER TABLE meeting_t DROP COLUMN poll_default_type CASCADE;
ALTER TABLE meeting_t DROP COLUMN poll_default_method CASCADE;
ALTER TABLE meeting_t DROP COLUMN poll_default_onehundred_percent_base CASCADE;
ALTER TABLE meeting_t DROP COLUMN poll_default_backend CASCADE;
ALTER TABLE meeting_t DROP COLUMN poll_default_live_voting_enabled CASCADE;
ALTER TABLE meeting_user_t DROP COLUMN vote_delegated_to_id CASCADE;
ALTER TABLE poll_t DROP COLUMN description CASCADE;
ALTER TABLE poll_t DROP COLUMN type CASCADE;
ALTER TABLE poll_t DROP COLUMN backend CASCADE;
ALTER TABLE poll_t DROP COLUMN is_pseudoanonymized CASCADE;
ALTER TABLE poll_t DROP COLUMN pollmethod CASCADE;
ALTER TABLE poll_t DROP COLUMN min_votes_amount CASCADE;
ALTER TABLE poll_t DROP COLUMN max_votes_amount CASCADE;
ALTER TABLE poll_t DROP COLUMN max_votes_per_option CASCADE;
ALTER TABLE poll_t DROP COLUMN global_yes CASCADE;
ALTER TABLE poll_t DROP COLUMN global_no CASCADE;
ALTER TABLE poll_t DROP COLUMN global_abstain CASCADE;
ALTER TABLE poll_t DROP COLUMN onehundred_percent_base CASCADE;
ALTER TABLE poll_t DROP COLUMN votesvalid CASCADE;
ALTER TABLE poll_t DROP COLUMN votesinvalid CASCADE;
ALTER TABLE poll_t DROP COLUMN votescast CASCADE;
ALTER TABLE poll_t DROP COLUMN entitled_users_at_stop CASCADE;
ALTER TABLE poll_t DROP COLUMN global_option_id CASCADE;
ALTER TABLE projector_t DROP COLUMN used_as_default_projector_for_poll_in_meeting_id CASCADE;
DROP TABLE nm_poll_voted_ids_user_t CASCADE;
DROP TRIGGER equal_meeting_id_on_meeting_user_t_vote_delegations_from_ids ON meeting_user_t;
DROP TRIGGER equal_meeting_id_on_motion_t_option_ids ON motion_t;
DROP TYPE enum_ballot_paper_selection;
DROP TYPE enum_poll_backends;

-- RENAME SECTION --

-- ADD SECTION --
CREATE TYPE enum_approval_onehundred_percent_bases AS ENUM ('yes_no', 'yes_no_abstain', 'valid', 'cast', 'entitled', 'entitled_present', 'disabled');

CREATE TYPE enum_rating_approval_onehundred_percent_bases AS ENUM ('yes_no', 'yes_no_abstain', 'valid', 'cast', 'entitled', 'entitled_present', 'disabled');

CREATE TYPE enum_rating_score_onehundred_percent_bases AS ENUM ('yes_no', 'valid', 'cast', 'entitled', 'entitled_present', 'disabled');

CREATE TYPE enum_selection_onehundred_percent_bases AS ENUM ('no_general', 'valid', 'cast', 'entitled', 'entitled_present', 'disabled');

CREATE TYPE enum_required_majority AS ENUM ('no_majority', 'two_third_majority', 'absolute_majority');

CREATE TYPE enum_required_majority_selection AS ENUM ('no_majority', 'two_third_majority', 'absolute_majority', 'simple_majority');

CREATE TYPE enum_poll_visibility AS ENUM ('manually', 'named', 'open', 'secret');

CREATE TYPE enum_poll_methods AS ENUM ('approval.yes_no', 'approval.yes_no_abstain', 'selection.yes', 'selection.no', 'rating_score', 'rating_approval.yes_no', 'rating_approval.yes_no_abstain');

CREATE TYPE enum_meeting_poll_projection_name_order_first AS ENUM ('first_name', 'last_name');

CREATE TABLE meeting_poll_setting_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    sort_result_by_votes boolean
        CONSTRAINT default_meeting_poll_setting_sort_result_by_votes DEFAULT True,
    allow_live_voting boolean
        CONSTRAINT default_meeting_poll_setting_allow_live_voting DEFAULT False,
    enable_max_yes_votes boolean
        CONSTRAINT default_meeting_poll_setting_enable_max_yes_votes DEFAULT False,
    enable_cumulative_voting boolean
        CONSTRAINT default_meeting_poll_setting_enable_cumulative_voting DEFAULT False,
    enable_max_options_limit boolean
        CONSTRAINT default_meeting_poll_setting_enable_max_options_limit DEFAULT False,
    method enum_poll_methods,
    visibility enum_poll_visibility
        CONSTRAINT default_meeting_poll_setting_visibility DEFAULT 'secret',
    enable_live_voting boolean
        CONSTRAINT default_meeting_poll_setting_enable_live_voting DEFAULT False,
    required_majority varchar(256)
        CONSTRAINT default_meeting_poll_setting_required_majority DEFAULT 'no_majority',
    onehundred_percent_base varchar(256)
        CONSTRAINT default_meeting_poll_setting_onehundred_percent_base DEFAULT 'valid',
    meeting_id integer
        CONSTRAINT required_meeting_poll_setting_meeting_id NOT NULL
);




CREATE TABLE poll_ballot_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    weight decimal(16,6)
        CONSTRAINT default_poll_ballot_weight DEFAULT '1.000000',
    split boolean
        CONSTRAINT default_poll_ballot_split DEFAULT False,
    value text,
    poll_id integer
        CONSTRAINT required_poll_ballot_poll_id NOT NULL,
    poll_ballot_user_id integer
        CONSTRAINT unique_poll_ballot_poll_ballot_user_id UNIQUE
);




CREATE TABLE poll_ballot_user_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    poll_id integer
        CONSTRAINT required_poll_ballot_user_poll_id NOT NULL,
    acting_meeting_user_id integer,
    represented_meeting_user_id integer,
    CONSTRAINT unique_poll_ballot_user_poll_id_represented_meeting_user_id UNIQUE (poll_id, represented_meeting_user_id)
);




CREATE TABLE poll_config_approval_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    allow_abstain boolean
        CONSTRAINT default_poll_config_approval_allow_abstain DEFAULT True,
    onehundred_percent_base enum_approval_onehundred_percent_bases
        CONSTRAINT required_poll_config_approval_onehundred_percent_base NOT NULL,
    required_majority enum_required_majority_selection
        CONSTRAINT default_poll_config_approval_required_majority DEFAULT 'no_majority'
);




CREATE TABLE poll_config_rating_approval_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    max_options_amount integer
        CONSTRAINT default_poll_config_rating_approval_max_options_amount DEFAULT 0,
    min_options_amount integer
        CONSTRAINT default_poll_config_rating_approval_min_options_amount DEFAULT 0,
    max_yes_amount integer,
    allow_abstain boolean
        CONSTRAINT default_poll_config_rating_approval_allow_abstain DEFAULT True,
    onehundred_percent_base enum_rating_approval_onehundred_percent_bases
        CONSTRAINT required_poll_config_rating_approval_onehundred_percent_base NOT NULL,
    required_majority enum_required_majority_selection
        CONSTRAINT default_poll_config_rating_approval_required_majority DEFAULT 'no_majority'
);




CREATE TABLE poll_config_rating_score_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    max_options_amount integer
        CONSTRAINT default_poll_config_rating_score_max_options_amount DEFAULT 0,
    min_options_amount integer
        CONSTRAINT default_poll_config_rating_score_min_options_amount DEFAULT 0,
    max_votes_per_option integer
        CONSTRAINT default_poll_config_rating_score_max_votes_per_option DEFAULT 0,
    max_vote_sum integer
        CONSTRAINT default_poll_config_rating_score_max_vote_sum DEFAULT 0,
    min_vote_sum integer
        CONSTRAINT default_poll_config_rating_score_min_vote_sum DEFAULT 0,
    onehundred_percent_base enum_rating_score_onehundred_percent_bases
        CONSTRAINT required_poll_config_rating_score_onehundred_percent_base NOT NULL,
    required_majority enum_required_majority
        CONSTRAINT default_poll_config_rating_score_required_majority DEFAULT 'no_majority'
);




CREATE TABLE poll_config_selection_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    max_options_amount integer
        CONSTRAINT default_poll_config_selection_max_options_amount DEFAULT 0,
    min_options_amount integer
        CONSTRAINT default_poll_config_selection_min_options_amount DEFAULT 0,
    allow_nota boolean
        CONSTRAINT default_poll_config_selection_allow_nota DEFAULT False,
    strike_out boolean
        CONSTRAINT default_poll_config_selection_strike_out DEFAULT False,
    onehundred_percent_base enum_selection_onehundred_percent_bases
        CONSTRAINT required_poll_config_selection_onehundred_percent_base NOT NULL,
    required_majority enum_required_majority
        CONSTRAINT default_poll_config_selection_required_majority DEFAULT 'no_majority',
    display_chart varchar(256)
);




CREATE TABLE poll_config_stv_scottish_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    posts integer
        CONSTRAINT minimum_poll_config_stv_scottish_posts CHECK (posts >= 1)
        CONSTRAINT default_poll_config_stv_scottish_posts DEFAULT 1
);




CREATE TABLE poll_entitled_user_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    poll_id integer
        CONSTRAINT required_poll_entitled_user_poll_id NOT NULL,
    meeting_user_id integer,
    present boolean
        CONSTRAINT required_poll_entitled_user_present NOT NULL,
    CONSTRAINT unique_poll_entitled_user_poll_id_meeting_user_id UNIQUE (poll_id, meeting_user_id)
);




CREATE TABLE poll_option_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    poll_id integer
        CONSTRAINT required_poll_option_poll_id NOT NULL,
    weight integer,
    text varchar(256),
    content_object_id varchar(100),
    content_object_id_meeting_user_id integer
        CONSTRAINT generated_always_as_poll_option_content_object_id_meetinab51685 GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'meeting_user' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_user_id integer
        CONSTRAINT generated_always_as_poll_option_content_object_id_user_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'user' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    CONSTRAINT valid_poll_option_content_object_id_part1 CHECK (split_part(content_object_id, '/', 1) IN ('meeting_user','user'))
);



ALTER TABLE history_entry_t
    ADD COLUMN model_id_topic_id integer
        CONSTRAINT generated_always_as_history_entry_model_id_topic_id GENERATED ALWAYS AS (CASE WHEN split_part(model_id, '/', 1) = 'topic' THEN cast(split_part(model_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    ADD CONSTRAINT valid_history_entry_model_id_part1 CHECK (split_part(model_id, '/', 1) IN ('assignment','motion','topic','user'));



ALTER TABLE meeting_t
    ADD COLUMN users_vote_delegations_max_amount integer
        CONSTRAINT default_meeting_users_vote_delegations_max_amount DEFAULT 1,
    ADD COLUMN assignment_poll_config_id integer
        CONSTRAINT unique_meeting_assignment_poll_config_id UNIQUE,
    ADD COLUMN motion_poll_config_id integer
        CONSTRAINT unique_meeting_motion_poll_config_id UNIQUE,
    ADD COLUMN topic_poll_config_id integer
        CONSTRAINT unique_meeting_topic_poll_config_id UNIQUE,
    ADD COLUMN poll_projection_name_order_first enum_meeting_poll_projection_name_order_first
        CONSTRAINT default_meeting_poll_projection_name_order_first DEFAULT 'last_name'
        CONSTRAINT required_meeting_poll_projection_name_order_first NOT NULL,
    ADD COLUMN poll_projection_max_columns integer
        CONSTRAINT default_meeting_poll_projection_max_columns DEFAULT 6
        CONSTRAINT required_meeting_poll_projection_max_columns NOT NULL;

ALTER TABLE poll_t
    ADD COLUMN config_id varchar(100)
        CONSTRAINT required_poll_config_id NOT NULL,
    ADD COLUMN config_id_poll_config_approval_id integer
        CONSTRAINT unique_poll_config_id_poll_config_approval_id UNIQUE
        CONSTRAINT generated_always_as_poll_config_id_poll_config_approval_id GENERATED ALWAYS AS (CASE WHEN split_part(config_id, '/', 1) = 'poll_config_approval' THEN cast(split_part(config_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    ADD COLUMN config_id_poll_config_selection_id integer
        CONSTRAINT unique_poll_config_id_poll_config_selection_id UNIQUE
        CONSTRAINT generated_always_as_poll_config_id_poll_config_selection_id GENERATED ALWAYS AS (CASE WHEN split_part(config_id, '/', 1) = 'poll_config_selection' THEN cast(split_part(config_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    ADD COLUMN config_id_poll_config_rating_score_id integer
        CONSTRAINT unique_poll_config_id_poll_config_rating_score_id UNIQUE
        CONSTRAINT generated_always_as_poll_config_id_poll_config_rating_score_id GENERATED ALWAYS AS (CASE WHEN split_part(config_id, '/', 1) = 'poll_config_rating_score' THEN cast(split_part(config_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    ADD COLUMN config_id_poll_config_rating_approval_id integer
        CONSTRAINT unique_poll_config_id_poll_config_rating_approval_id UNIQUE
        CONSTRAINT generated_always_as_poll_config_id_poll_config_rating_ap5cb0e6b GENERATED ALWAYS AS (CASE WHEN split_part(config_id, '/', 1) = 'poll_config_rating_approval' THEN cast(split_part(config_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    ADD COLUMN config_id_poll_config_stv_scottish_id integer
        CONSTRAINT unique_poll_config_id_poll_config_stv_scottish_id UNIQUE
        CONSTRAINT generated_always_as_poll_config_id_poll_config_stv_scottish_id GENERATED ALWAYS AS (CASE WHEN split_part(config_id, '/', 1) = 'poll_config_stv_scottish' THEN cast(split_part(config_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    ADD CONSTRAINT valid_poll_config_id_part1 CHECK (split_part(config_id, '/', 1) IN ('poll_config_approval','poll_config_selection','poll_config_rating_score','poll_config_rating_approval','poll_config_stv_scottish')),
    ADD COLUMN visibility enum_poll_visibility
        CONSTRAINT required_poll_visibility NOT NULL,
    ADD COLUMN result text,
    ADD COLUMN published boolean
        CONSTRAINT default_poll_published DEFAULT False,
    ADD COLUMN anonymized boolean
        CONSTRAINT default_poll_anonymized DEFAULT False,
    ADD COLUMN allow_empty boolean
        CONSTRAINT default_poll_allow_empty DEFAULT False,
    ADD COLUMN allow_invalid boolean
        CONSTRAINT default_poll_allow_invalid DEFAULT False,
    ADD COLUMN allow_vote_split boolean
        CONSTRAINT default_poll_allow_vote_split DEFAULT False;

ALTER TABLE projector_t
    ADD COLUMN used_as_default_projector_for_topic_poll_in_meeting_id integer;

ALTER TABLE meeting_poll_setting_t ADD CONSTRAINT fk_meeting_poll_setting_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_poll_setting_t_meeting_id ON meeting_poll_setting_t (meeting_id);

ALTER TABLE poll_ballot_t ADD CONSTRAINT fk_poll_ballot_t_poll_id_poll_t_id FOREIGN KEY(poll_id) REFERENCES poll_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_ballot_t_poll_id ON poll_ballot_t (poll_id);
ALTER TABLE poll_ballot_t ADD CONSTRAINT fk_poll_ballot_t_poll_ballot_user_id_poll_ballot_user_t_id FOREIGN KEY(poll_ballot_user_id) REFERENCES poll_ballot_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_ballot_t_poll_ballot_user_id ON poll_ballot_t (poll_ballot_user_id);

ALTER TABLE poll_ballot_user_t ADD CONSTRAINT fk_poll_ballot_user_t_poll_id_poll_t_id FOREIGN KEY(poll_id) REFERENCES poll_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_ballot_user_t_poll_id ON poll_ballot_user_t (poll_id);
ALTER TABLE poll_ballot_user_t ADD CONSTRAINT fk_poll_ballot_user_t_acting_meeting_user_id_meeting_user_t_id FOREIGN KEY(acting_meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_ballot_user_t_acting_meeting_user_id ON poll_ballot_user_t (acting_meeting_user_id);
ALTER TABLE poll_ballot_user_t ADD CONSTRAINT fk_poll_ballot_user_t_represented_meeting_user_id_meetin7f0c82a FOREIGN KEY(represented_meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_ballot_user_t_represented_meeting_user_id ON poll_ballot_user_t (represented_meeting_user_id);

ALTER TABLE poll_entitled_user_t ADD CONSTRAINT fk_poll_entitled_user_t_poll_id_poll_t_id FOREIGN KEY(poll_id) REFERENCES poll_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_entitled_user_t_poll_id ON poll_entitled_user_t (poll_id);
ALTER TABLE poll_entitled_user_t ADD CONSTRAINT fk_poll_entitled_user_t_meeting_user_id_meeting_user_t_id FOREIGN KEY(meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_entitled_user_t_meeting_user_id ON poll_entitled_user_t (meeting_user_id);

ALTER TABLE poll_option_t ADD CONSTRAINT fk_poll_option_t_poll_id_poll_t_id FOREIGN KEY(poll_id) REFERENCES poll_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_option_t_poll_id ON poll_option_t (poll_id);
ALTER TABLE poll_option_t ADD CONSTRAINT fk_poll_option_t_content_object_id_meeting_user_id_meeti29ea351 FOREIGN KEY(content_object_id_meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_option_t_content_object_id_meeting_user_id ON poll_option_t (content_object_id_meeting_user_id);
ALTER TABLE poll_option_t ADD CONSTRAINT fk_poll_option_t_content_object_id_user_id_user_t_id FOREIGN KEY(content_object_id_user_id) REFERENCES user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_option_t_content_object_id_user_id ON poll_option_t (content_object_id_user_id);


-- definition trigger prevent_updates for meeting_poll_setting.meeting_id
CREATE TRIGGER tr_constant_meeting_poll_setting_meeting_id BEFORE UPDATE OF meeting_id ON meeting_poll_setting_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('meeting_poll_setting', 'meeting_id');

-- notify trigger for meeting_poll_setting
CREATE TRIGGER tr_log_meeting_poll_setting AFTER INSERT OR UPDATE OR DELETE ON meeting_poll_setting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('meeting_poll_setting');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON meeting_poll_setting_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for meeting_poll_setting fields
CREATE TRIGGER tr_log_meeting_poll_setting_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON meeting_poll_setting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'poll_setting_ids');


-- definition trigger prevent_updates for poll_ballot.weight
CREATE TRIGGER tr_constant_poll_ballot_weight BEFORE UPDATE OF weight ON poll_ballot_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('poll_ballot', 'weight');

-- definition trigger prevent_updates for poll_ballot.poll_id
CREATE TRIGGER tr_constant_poll_ballot_poll_id BEFORE UPDATE OF poll_id ON poll_ballot_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('poll_ballot', 'poll_id');


CREATE CONSTRAINT TRIGGER equal_poll_id_on_poll_ballot_t_poll_ballot_user_id AFTER INSERT OR UPDATE OF poll_ballot_user_id ON poll_ballot_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll_ballot', 'poll_ballot_user', 'poll_ballot_user_id', 'poll_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_poll_id_on_poll_ballot_user_t_poll_ballot_id AFTER INSERT ON poll_ballot_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll_ballot', 'poll_ballot_user', 'poll_ballot_user_id', 'poll_id', TRUE);


-- notify trigger for poll_ballot
CREATE TRIGGER tr_log_poll_ballot AFTER INSERT OR UPDATE OR DELETE ON poll_ballot_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_ballot');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_ballot_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for poll_ballot fields
CREATE TRIGGER tr_log_poll_ballot_t_poll_id AFTER INSERT OR UPDATE OF poll_id OR DELETE ON poll_ballot_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll', 'poll_id', 'ballot_ids');
CREATE TRIGGER tr_log_poll_ballot_t_poll_ballot_user_id AFTER INSERT OR UPDATE OF poll_ballot_user_id OR DELETE ON poll_ballot_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll_ballot_user', 'poll_ballot_user_id', 'poll_ballot_id');


-- definition trigger prevent_updates for poll_ballot_user.poll_id
CREATE TRIGGER tr_constant_poll_ballot_user_poll_id BEFORE UPDATE OF poll_id ON poll_ballot_user_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('poll_ballot_user', 'poll_id');

-- notify trigger for poll_ballot_user
CREATE TRIGGER tr_log_poll_ballot_user AFTER INSERT OR UPDATE OR DELETE ON poll_ballot_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_ballot_user');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_ballot_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for poll_ballot_user fields
CREATE TRIGGER tr_log_poll_ballot_user_t_poll_id AFTER INSERT OR UPDATE OF poll_id OR DELETE ON poll_ballot_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll', 'poll_id', 'ballot_user_ids');
CREATE TRIGGER tr_log_poll_ballot_user_t_acting_meeting_user_id AFTER INSERT OR UPDATE OF acting_meeting_user_id OR DELETE ON poll_ballot_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'acting_meeting_user_id', 'acting_ballot_ids');
CREATE TRIGGER tr_log_poll_ballot_user_t_represented_meeting_user_id AFTER INSERT OR UPDATE OF represented_meeting_user_id OR DELETE ON poll_ballot_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'represented_meeting_user_id', 'represented_ballot_ids');


-- definition trigger not null for poll_config_approval.poll_id against poll.config_id_poll_config_approval_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_poll_config_approval_poll_id AFTER INSERT ON poll_config_approval_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_config_approval', 'poll_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_poll_config_approval_poll_id AFTER UPDATE OF config_id_poll_config_approval_id OR DELETE ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_config_approval', 'poll_id', 'poll', 'config_id_poll_config_approval_id');

-- notify trigger for poll_config_approval
CREATE TRIGGER tr_log_poll_config_approval AFTER INSERT OR UPDATE OR DELETE ON poll_config_approval_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_config_approval');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_config_approval_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- definition trigger not null for poll_config_rating_approval.poll_id against poll.config_id_poll_config_rating_approval_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_poll_config_rating_approval_poll_id AFTER INSERT ON poll_config_rating_approval_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_config_rating_approval', 'poll_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_poll_config_rating_approval_poll_id AFTER UPDATE OF config_id_poll_config_rating_approval_id OR DELETE ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_config_rating_approval', 'poll_id', 'poll', 'config_id_poll_config_rating_approval_id');

-- notify trigger for poll_config_rating_approval
CREATE TRIGGER tr_log_poll_config_rating_approval AFTER INSERT OR UPDATE OR DELETE ON poll_config_rating_approval_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_config_rating_approval');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_config_rating_approval_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- definition trigger not null for poll_config_rating_score.poll_id against poll.config_id_poll_config_rating_score_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_poll_config_rating_score_poll_id AFTER INSERT ON poll_config_rating_score_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_config_rating_score', 'poll_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_poll_config_rating_score_poll_id AFTER UPDATE OF config_id_poll_config_rating_score_id OR DELETE ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_config_rating_score', 'poll_id', 'poll', 'config_id_poll_config_rating_score_id');

-- notify trigger for poll_config_rating_score
CREATE TRIGGER tr_log_poll_config_rating_score AFTER INSERT OR UPDATE OR DELETE ON poll_config_rating_score_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_config_rating_score');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_config_rating_score_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- definition trigger not null for poll_config_selection.poll_id against poll.config_id_poll_config_selection_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_poll_config_selection_poll_id AFTER INSERT ON poll_config_selection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_config_selection', 'poll_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_poll_config_selection_poll_id AFTER UPDATE OF config_id_poll_config_selection_id OR DELETE ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_config_selection', 'poll_id', 'poll', 'config_id_poll_config_selection_id');

-- notify trigger for poll_config_selection
CREATE TRIGGER tr_log_poll_config_selection AFTER INSERT OR UPDATE OR DELETE ON poll_config_selection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_config_selection');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_config_selection_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- definition trigger not null for poll_config_stv_scottish.poll_id against poll.config_id_poll_config_stv_scottish_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_poll_config_stv_scottish_poll_id AFTER INSERT ON poll_config_stv_scottish_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_config_stv_scottish', 'poll_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_poll_config_stv_scottish_poll_id AFTER UPDATE OF config_id_poll_config_stv_scottish_id OR DELETE ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_config_stv_scottish', 'poll_id', 'poll', 'config_id_poll_config_stv_scottish_id');

-- notify trigger for poll_config_stv_scottish
CREATE TRIGGER tr_log_poll_config_stv_scottish AFTER INSERT OR UPDATE OR DELETE ON poll_config_stv_scottish_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_config_stv_scottish');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_config_stv_scottish_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for poll_entitled_user
CREATE TRIGGER tr_log_poll_entitled_user AFTER INSERT OR UPDATE OR DELETE ON poll_entitled_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_entitled_user');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_entitled_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for poll_entitled_user fields
CREATE TRIGGER tr_log_poll_entitled_user_t_poll_id AFTER INSERT OR UPDATE OF poll_id OR DELETE ON poll_entitled_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll', 'poll_id', 'entitled_user_ids');
CREATE TRIGGER tr_log_poll_entitled_user_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON poll_entitled_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'poll_entitled_user_ids');

-- notify trigger for poll_option
CREATE TRIGGER tr_log_poll_option AFTER INSERT OR UPDATE OR DELETE ON poll_option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_option');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_option_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for poll_option fields
CREATE TRIGGER tr_log_poll_option_t_poll_id AFTER INSERT OR UPDATE OF poll_id OR DELETE ON poll_option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll', 'poll_id', 'option_ids');

CREATE TRIGGER tr_log_meeting_user_content_object_id_meeting_user_id AFTER INSERT OR UPDATE OF content_object_id_meeting_user_id OR DELETE ON poll_option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user','content_object_id_meeting_user_id','poll_option_ids');

CREATE TRIGGER tr_log_user_content_object_id_user_id AFTER INSERT OR UPDATE OF content_object_id_user_id OR DELETE ON poll_option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user','content_object_id_user_id','poll_option_ids');

CREATE TABLE nm_group_uimpdi_meeting_poll_setting_t (
    group_id integer
        CONSTRAINT required_nm_group_uimpdi_meeting_poll_setting_t_group_id NOT NULL
        CONSTRAINT fk_nm_group_uimpdi_meeting_poll_setting_t_group_id_group_t_id REFERENCES group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    meeting_poll_setting_id integer
        CONSTRAINT required_nm_group_uimpdi_meeting_poll_setting_t_meeting_3e3a74c NOT NULL
        CONSTRAINT fk_nm_group_uimpdi_meeting_poll_setting_t_meeting_poll_de89d9d1 REFERENCES meeting_poll_setting_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_group_uimpdi_meeting_poll_setting_t PRIMARY KEY (group_id, meeting_poll_setting_id)
);
CREATE INDEX idx_nm_group_uimpdi_meeting_poll_setting_t_group_id ON nm_group_uimpdi_meeting_poll_setting_t (group_id);
CREATE INDEX idx_nm_group_uimpdi_meeting_poll_setting_t_meeting_poll_d4adef5 ON nm_group_uimpdi_meeting_poll_setting_t (meeting_poll_setting_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_assignment_poll_config_id_meeting_poll_defa20bd2b8 FOREIGN KEY(assignment_poll_config_id) REFERENCES meeting_poll_setting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_assignment_poll_config_id ON meeting_t (assignment_poll_config_id);
CREATE TRIGGER tr_log_meeting_t_assignment_poll_config_id AFTER INSERT OR UPDATE OF assignment_poll_config_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_poll_setting', 'assignment_poll_config_id', 'used_as_assignment_poll_config_in_meeting_id');
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_motion_poll_config_id_meeting_poll_setting_t_id FOREIGN KEY(motion_poll_config_id) REFERENCES meeting_poll_setting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_motion_poll_config_id ON meeting_t (motion_poll_config_id);
CREATE TRIGGER tr_log_meeting_t_motion_poll_config_id AFTER INSERT OR UPDATE OF motion_poll_config_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_poll_setting', 'motion_poll_config_id', 'used_as_motion_poll_config_in_meeting_id');
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_topic_poll_config_id_meeting_poll_setting_t_id FOREIGN KEY(topic_poll_config_id) REFERENCES meeting_poll_setting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_topic_poll_config_id ON meeting_t (topic_poll_config_id);
CREATE TRIGGER tr_log_meeting_t_topic_poll_config_id AFTER INSERT OR UPDATE OF topic_poll_config_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_poll_setting', 'topic_poll_config_id', 'used_as_topic_poll_config_in_meeting_id');

CREATE TABLE nm_meeting_user_vote_delegated_to_ids_meeting_user_t (
    vote_delegations_from_id integer
        CONSTRAINT required_nm_meeting_user_vote_delegated_to_ids_meeting_u2c2dede NOT NULL
        CONSTRAINT fk_nm_meeting_user_vote_delegated_to_ids_meeting_user_t_3faa0ec REFERENCES meeting_user_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    vote_delegated_to_id integer
        CONSTRAINT required_nm_meeting_user_vote_delegated_to_ids_meeting_ueb04d5e NOT NULL
        CONSTRAINT fk_nm_meeting_user_vote_delegated_to_ids_meeting_user_t_d8197d4 REFERENCES meeting_user_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_meeting_user_vote_delegated_to_ids_meeting_user_t PRIMARY KEY (vote_delegations_from_id, vote_delegated_to_id)
);
CREATE INDEX idx_nm_meeting_user_vote_delegated_to_ids_meeting_user_tee86852 ON nm_meeting_user_vote_delegated_to_ids_meeting_user_t (vote_delegations_from_id);
CREATE INDEX idx_nm_meeting_user_vote_delegated_to_ids_meeting_user_t54a80eb ON nm_meeting_user_vote_delegated_to_ids_meeting_user_t (vote_delegated_to_id);
ALTER TABLE poll_t ADD CONSTRAINT fk_poll_t_config_id_poll_config_approval_id_poll_config_f74c82e FOREIGN KEY(config_id_poll_config_approval_id) REFERENCES poll_config_approval_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_t_config_id_poll_config_approval_id ON poll_t (config_id_poll_config_approval_id);
ALTER TABLE poll_t ADD CONSTRAINT fk_poll_t_config_id_poll_config_selection_id_poll_config65f401f FOREIGN KEY(config_id_poll_config_selection_id) REFERENCES poll_config_selection_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_t_config_id_poll_config_selection_id ON poll_t (config_id_poll_config_selection_id);
ALTER TABLE poll_t ADD CONSTRAINT fk_poll_t_config_id_poll_config_rating_score_id_poll_conff3b6f0 FOREIGN KEY(config_id_poll_config_rating_score_id) REFERENCES poll_config_rating_score_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_t_config_id_poll_config_rating_score_id ON poll_t (config_id_poll_config_rating_score_id);
ALTER TABLE poll_t ADD CONSTRAINT fk_poll_t_config_id_poll_config_rating_approval_id_poll_6ff58a7 FOREIGN KEY(config_id_poll_config_rating_approval_id) REFERENCES poll_config_rating_approval_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_t_config_id_poll_config_rating_approval_id ON poll_t (config_id_poll_config_rating_approval_id);
ALTER TABLE poll_t ADD CONSTRAINT fk_poll_t_config_id_poll_config_stv_scottish_id_poll_con0ff7fb4 FOREIGN KEY(config_id_poll_config_stv_scottish_id) REFERENCES poll_config_stv_scottish_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_t_config_id_poll_config_stv_scottish_id ON poll_t (config_id_poll_config_stv_scottish_id);

CREATE TRIGGER tr_log_poll_config_approval_config_id_poll_config_approval_id AFTER INSERT OR UPDATE OF config_id_poll_config_approval_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll_config_approval','config_id_poll_config_approval_id','poll_id');

CREATE TRIGGER tr_log_poll_config_selection_config_id_poll_config_selection_id AFTER INSERT OR UPDATE OF config_id_poll_config_selection_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll_config_selection','config_id_poll_config_selection_id','poll_id');

CREATE TRIGGER tr_log_poll_config_rating_score_config_id_poll_config_raf40fad3 AFTER INSERT OR UPDATE OF config_id_poll_config_rating_score_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll_config_rating_score','config_id_poll_config_rating_score_id','poll_id');

CREATE TRIGGER tr_log_poll_config_rating_approval_config_id_poll_config405bbee AFTER INSERT OR UPDATE OF config_id_poll_config_rating_approval_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll_config_rating_approval','config_id_poll_config_rating_approval_id','poll_id');

CREATE TRIGGER tr_log_poll_config_stv_scottish_config_id_poll_config_st0701463 AFTER INSERT OR UPDATE OF config_id_poll_config_stv_scottish_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll_config_stv_scottish','config_id_poll_config_stv_scottish_id','poll_id');
comment on column poll_t.result is 'Calculated result. The format depends on the value in poll/method. Can be manually set when visibility is set to manually.';
comment on column poll_t.published is 'If true, users can see the result.';
comment on column poll_t.anonymized is 'Set to true, after finished was called with anonymize.';
comment on column poll_t.allow_invalid is 'If true, the vote service does not validate. This is always the case for secret polls.';
comment on column poll_t.allow_vote_split is 'If true, users can split there vote.';
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_topic_poll_b2f5888 FOREIGN KEY(used_as_default_projector_for_topic_poll_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_topic_pollb4f5002 ON projector_t (used_as_default_projector_for_topic_poll_in_meeting_id);
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_topic_p9aaf88b AFTER INSERT OR UPDATE OF used_as_default_projector_for_topic_poll_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_topic_poll_in_meeting_id', 'default_projector_topic_poll_ids');

-- VIEWS UPDATE SECTION --
CREATE OR REPLACE VIEW "group" AS SELECT *,
(select array_agg(n.meeting_user_id ORDER BY n.meeting_user_id) from nm_group_meeting_user_ids_meeting_user_t n where n.group_id = g.id) as meeting_user_ids,
(select m.id from meeting_t m where m.default_group_id = g.id) as default_group_for_meeting_id,
(select m.id from meeting_t m where m.admin_group_id = g.id) as admin_group_for_meeting_id,
(select m.id from meeting_t m where m.anonymous_group_id = g.id) as anonymous_group_for_meeting_id,
(select array_agg(n.meeting_mediafile_id ORDER BY n.meeting_mediafile_id) from nm_group_mmagi_meeting_mediafile_t n where n.group_id = g.id) as meeting_mediafile_access_group_ids,
(select array_agg(n.meeting_mediafile_id ORDER BY n.meeting_mediafile_id) from nm_group_mmiagi_meeting_mediafile_t n where n.group_id = g.id) as meeting_mediafile_inherited_access_group_ids,
(select array_agg(n.motion_comment_section_id ORDER BY n.motion_comment_section_id) from nm_group_read_comment_section_ids_motion_comment_section_t n where n.group_id = g.id) as read_comment_section_ids,
(select array_agg(n.motion_comment_section_id ORDER BY n.motion_comment_section_id) from nm_group_write_comment_section_ids_motion_comment_section_t n where n.group_id = g.id) as write_comment_section_ids,
(select array_agg(n.chat_group_id ORDER BY n.chat_group_id) from nm_chat_group_read_group_ids_group_t n where n.group_id = g.id) as read_chat_group_ids,
(select array_agg(n.chat_group_id ORDER BY n.chat_group_id) from nm_chat_group_write_group_ids_group_t n where n.group_id = g.id) as write_chat_group_ids,
(select array_agg(n.poll_id ORDER BY n.poll_id) from nm_group_poll_ids_poll_t n where n.group_id = g.id) as poll_ids,
(select array_agg(n.meeting_poll_setting_id ORDER BY n.meeting_poll_setting_id) from nm_group_uimpdi_meeting_poll_setting_t n where n.group_id = g.id) as used_in_meeting_poll_setting_ids
FROM group_t g;

comment on column "group".meeting_mediafile_inherited_access_group_ids is 'Calculated field.';

CREATE OR REPLACE VIEW "meeting" AS SELECT *,
(select array_agg(mu.id ORDER BY mu.id) from meeting_user_t mu where mu.meeting_id = m.id) as meeting_user_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.meeting_id = m.id) as projector_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.meeting_id = m.id) as all_projection_ids,
(select array_agg(p.id ORDER BY p.id) from projector_message_t p where p.meeting_id = m.id) as projector_message_ids,
(select array_agg(p.id ORDER BY p.id) from projector_countdown_t p where p.meeting_id = m.id) as projector_countdown_ids,
(select array_agg(t.id ORDER BY t.id) from tag_t t where t.meeting_id = m.id) as tag_ids,
(select array_agg(a.id ORDER BY a.id) from agenda_item_t a where a.meeting_id = m.id) as agenda_item_ids,
(select array_agg(l.id ORDER BY l.id) from list_of_speakers_t l where l.meeting_id = m.id) as list_of_speakers_ids,
(select array_agg(s.id ORDER BY s.id) from structure_level_list_of_speakers_t s where s.meeting_id = m.id) as structure_level_list_of_speakers_ids,
(select array_agg(p.id ORDER BY p.id) from point_of_order_category_t p where p.meeting_id = m.id) as point_of_order_category_ids,
(select array_agg(s.id ORDER BY s.id) from speaker_t s where s.meeting_id = m.id) as speaker_ids,
(select array_agg(t.id ORDER BY t.id) from topic_t t where t.meeting_id = m.id) as topic_ids,
(select array_agg(g.id ORDER BY g.id) from group_t g where g.meeting_id = m.id) as group_ids,
(select array_agg(mm.id ORDER BY mm.id) from meeting_mediafile_t mm where mm.meeting_id = m.id) as meeting_mediafile_ids,
(select array_agg(mt.id ORDER BY mt.id) from mediafile_t mt where mt.owner_id_meeting_id = m.id) as mediafile_ids,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.meeting_id = m.id) as motion_ids,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.origin_meeting_id = m.id) as forwarded_motion_ids,
(select array_agg(mc.id ORDER BY mc.id) from motion_comment_section_t mc where mc.meeting_id = m.id) as motion_comment_section_ids,
(select array_agg(mc.id ORDER BY mc.id) from motion_category_t mc where mc.meeting_id = m.id) as motion_category_ids,
(select array_agg(mb.id ORDER BY mb.id) from motion_block_t mb where mb.meeting_id = m.id) as motion_block_ids,
(select array_agg(mw.id ORDER BY mw.id) from motion_workflow_t mw where mw.meeting_id = m.id) as motion_workflow_ids,
(select array_agg(mc.id ORDER BY mc.id) from motion_comment_t mc where mc.meeting_id = m.id) as motion_comment_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_submitter_t ms where ms.meeting_id = m.id) as motion_submitter_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_supporter_t ms where ms.meeting_id = m.id) as motion_supporter_ids,
(select array_agg(me.id ORDER BY me.id) from motion_editor_t me where me.meeting_id = m.id) as motion_editor_ids,
(select array_agg(mw.id ORDER BY mw.id) from motion_working_group_speaker_t mw where mw.meeting_id = m.id) as motion_working_group_speaker_ids,
(select array_agg(mc.id ORDER BY mc.id) from motion_change_recommendation_t mc where mc.meeting_id = m.id) as motion_change_recommendation_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_state_t ms where ms.meeting_id = m.id) as motion_state_ids,
(select array_agg(p.id ORDER BY p.id) from poll_t p where p.meeting_id = m.id) as poll_ids,
(select array_agg(mp.id ORDER BY mp.id) from meeting_poll_setting_t mp where mp.meeting_id = m.id) as poll_setting_ids,
(select array_agg(a.id ORDER BY a.id) from assignment_t a where a.meeting_id = m.id) as assignment_ids,
(select array_agg(a.id ORDER BY a.id) from assignment_candidate_t a where a.meeting_id = m.id) as assignment_candidate_ids,
(select array_agg(p.id ORDER BY p.id) from personal_note_t p where p.meeting_id = m.id) as personal_note_ids,
(select array_agg(c.id ORDER BY c.id) from chat_group_t c where c.meeting_id = m.id) as chat_group_ids,
(select array_agg(c.id ORDER BY c.id) from chat_message_t c where c.meeting_id = m.id) as chat_message_ids,
(select array_agg(s.id ORDER BY s.id) from structure_level_t s where s.meeting_id = m.id) as structure_level_ids,
(select c.id from committee_t c where c.default_meeting_id = m.id) as default_meeting_for_committee_id,
(select array_agg(g.organization_tag_id ORDER BY g.organization_tag_id) from gm_organization_tag_tagged_ids_t g where g.tagged_id_meeting_id = m.id) as organization_tag_ids,
(select array_agg(n.user_id ORDER BY n.user_id) from nm_meeting_present_user_ids_user_t n where n.meeting_id = m.id) as present_user_ids,
(
  SELECT array_agg(DISTINCT mu.user_id ORDER BY mu.user_id)
  FROM meeting_user_t mu
  WHERE mu.meeting_id = m.id
) AS user_ids
,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_meeting_id = m.id) as projection_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_agenda_item_list_in_meeting_id = m.id) as default_projector_agenda_item_list_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_topic_in_meeting_id = m.id) as default_projector_topic_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_list_of_speakers_in_meeting_id = m.id) as default_projector_list_of_speakers_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_current_los_in_meeting_id = m.id) as default_projector_current_los_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_motion_in_meeting_id = m.id) as default_projector_motion_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_amendment_in_meeting_id = m.id) as default_projector_amendment_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_motion_block_in_meeting_id = m.id) as default_projector_motion_block_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_assignment_in_meeting_id = m.id) as default_projector_assignment_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_mediafile_in_meeting_id = m.id) as default_projector_mediafile_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_message_in_meeting_id = m.id) as default_projector_message_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_countdown_in_meeting_id = m.id) as default_projector_countdown_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_assignment_poll_in_meeting_id = m.id) as default_projector_assignment_poll_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_motion_poll_in_meeting_id = m.id) as default_projector_motion_poll_ids,
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_topic_poll_in_meeting_id = m.id) as default_projector_topic_poll_ids,
(select array_agg(h.id ORDER BY h.id) from history_entry_t h where h.meeting_id = m.id) as relevant_history_entry_ids
FROM meeting_t m;

comment on column "meeting".user_ids is 'Calculated. All user ids from all users assigned to groups of this meeting.';

CREATE OR REPLACE VIEW "meeting_poll_setting" AS SELECT *,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_group_uimpdi_meeting_poll_setting_t n where n.meeting_poll_setting_id = m.id) as group_ids,
(select m1.id from meeting_t m1 where m1.assignment_poll_config_id = m.id) as used_as_assignment_poll_config_in_meeting_id,
(select m1.id from meeting_t m1 where m1.motion_poll_config_id = m.id) as used_as_motion_poll_config_in_meeting_id,
(select m1.id from meeting_t m1 where m1.topic_poll_config_id = m.id) as used_as_topic_poll_config_in_meeting_id
FROM meeting_poll_setting_t m;


CREATE OR REPLACE VIEW "meeting_user" AS SELECT *,
(select array_agg(p.id ORDER BY p.id) from personal_note_t p where p.meeting_user_id = m.id) as personal_note_ids,
(select array_agg(s.id ORDER BY s.id) from speaker_t s where s.meeting_user_id = m.id) as speaker_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_supporter_t ms where ms.meeting_user_id = m.id) as motion_supporter_ids,
(select array_agg(me.id ORDER BY me.id) from motion_editor_t me where me.meeting_user_id = m.id) as motion_editor_ids,
(select array_agg(mw.id ORDER BY mw.id) from motion_working_group_speaker_t mw where mw.meeting_user_id = m.id) as motion_working_group_speaker_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_submitter_t ms where ms.meeting_user_id = m.id) as motion_submitter_ids,
(select array_agg(a.id ORDER BY a.id) from assignment_candidate_t a where a.meeting_user_id = m.id) as assignment_candidate_ids,
(select array_agg(n.vote_delegated_to_id ORDER BY n.vote_delegated_to_id) from nm_meeting_user_vote_delegated_to_ids_meeting_user_t n where n.vote_delegations_from_id = m.id) as vote_delegated_to_ids,
(select array_agg(n.vote_delegations_from_id ORDER BY n.vote_delegations_from_id) from nm_meeting_user_vote_delegated_to_ids_meeting_user_t n where n.vote_delegated_to_id = m.id) as vote_delegations_from_ids,
(select array_agg(p.id ORDER BY p.id) from poll_option_t p where p.content_object_id_meeting_user_id = m.id) as poll_option_ids,
(select array_agg(p.id ORDER BY p.id) from poll_ballot_user_t p where p.acting_meeting_user_id = m.id) as acting_ballot_ids,
(select array_agg(p.id ORDER BY p.id) from poll_ballot_user_t p where p.represented_meeting_user_id = m.id) as represented_ballot_ids,
(select array_agg(p.id ORDER BY p.id) from poll_entitled_user_t p where p.meeting_user_id = m.id) as poll_entitled_user_ids,
(select array_agg(c.id ORDER BY c.id) from chat_message_t c where c.meeting_user_id = m.id) as chat_message_ids,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_group_meeting_user_ids_meeting_user_t n where n.meeting_user_id = m.id) as group_ids,
(select array_agg(n.structure_level_id ORDER BY n.structure_level_id) from nm_meeting_user_structure_level_ids_structure_level_t n where n.meeting_user_id = m.id) as structure_level_ids
FROM meeting_user_t m;


CREATE OR REPLACE VIEW "motion" AS SELECT *,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.lead_motion_id = m.id) as amendment_ids,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.sort_parent_id = m.id) as sort_child_ids,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.origin_id = m.id) as derived_motion_ids,
(select array_agg(n.all_origin_id ORDER BY n.all_origin_id) from nm_motion_all_derived_motion_ids_motion_t n where n.all_derived_motion_id = m.id) as all_origin_ids,
(select array_agg(n.all_derived_motion_id ORDER BY n.all_derived_motion_id) from nm_motion_all_derived_motion_ids_motion_t n where n.all_origin_id = m.id) as all_derived_motion_ids,
(select array_cat((select array_agg(n.identical_motion_id_1 ORDER BY n.identical_motion_id_1) from nm_motion_identical_motion_ids_motion_t n where n.identical_motion_id_2 = m.id), (select array_agg(n.identical_motion_id_2 ORDER BY n.identical_motion_id_2) from nm_motion_identical_motion_ids_motion_t n where n.identical_motion_id_1 = m.id))) as identical_motion_ids,
(select array_agg(g.state_extension_reference_id ORDER BY g.state_extension_reference_id) from gm_motion_state_extension_reference_ids_t g where g.motion_id = m.id) as state_extension_reference_ids,
(select array_agg(g.motion_id ORDER BY g.motion_id) from gm_motion_state_extension_reference_ids_t g where g.state_extension_reference_id_motion_id = m.id) as referenced_in_motion_state_extension_ids,
(select array_agg(g.recommendation_extension_reference_id ORDER BY g.recommendation_extension_reference_id) from gm_motion_recommendation_extension_reference_ids_t g where g.motion_id = m.id) as recommendation_extension_reference_ids,
(select array_agg(g.motion_id ORDER BY g.motion_id) from gm_motion_recommendation_extension_reference_ids_t g where g.recommendation_extension_reference_id_motion_id = m.id) as referenced_in_motion_recommendation_extension_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_submitter_t ms where ms.motion_id = m.id) as submitter_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_supporter_t ms where ms.motion_id = m.id) as supporter_ids,
(select array_agg(me.id ORDER BY me.id) from motion_editor_t me where me.motion_id = m.id) as editor_ids,
(select array_agg(mw.id ORDER BY mw.id) from motion_working_group_speaker_t mw where mw.motion_id = m.id) as working_group_speaker_ids,
(select array_agg(p.id ORDER BY p.id) from poll_t p where p.content_object_id_motion_id = m.id) as poll_ids,
(select array_agg(mc.id ORDER BY mc.id) from motion_change_recommendation_t mc where mc.motion_id = m.id) as change_recommendation_ids,
(select array_agg(mc.id ORDER BY mc.id) from motion_comment_t mc where mc.motion_id = m.id) as comment_ids,
(select a.id from agenda_item_t a where a.content_object_id_motion_id = m.id) as agenda_item_id,
(select l.id from list_of_speakers_t l where l.content_object_id_motion_id = m.id) as list_of_speakers_id,
(select array_agg(g.tag_id ORDER BY g.tag_id) from gm_tag_tagged_ids_t g where g.tagged_id_motion_id = m.id) as tag_ids,
(select array_agg(g.meeting_mediafile_id ORDER BY g.meeting_mediafile_id) from gm_meeting_mediafile_attachment_ids_t g where g.attachment_id_motion_id = m.id) as attachment_meeting_mediafile_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_motion_id = m.id) as projection_ids,
(select array_agg(p.id ORDER BY p.id) from personal_note_t p where p.content_object_id_motion_id = m.id) as personal_note_ids,
(select array_agg(h.id ORDER BY h.id) from history_entry_t h where h.model_id_motion_id = m.id) as history_entry_ids
FROM motion_t m;


CREATE OR REPLACE VIEW "poll" AS SELECT *,
(select array_agg(po.id ORDER BY po.id) from poll_option_t po where po.poll_id = p.id) as option_ids,
(select array_agg(pb.id ORDER BY pb.id) from poll_ballot_t pb where pb.poll_id = p.id) as ballot_ids,
(select array_agg(pb.id ORDER BY pb.id) from poll_ballot_user_t pb where pb.poll_id = p.id) as ballot_user_ids,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_group_poll_ids_poll_t n where n.poll_id = p.id) as entitled_group_ids,
(select array_agg(pe.id ORDER BY pe.id) from poll_entitled_user_t pe where pe.poll_id = p.id) as entitled_user_ids,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.content_object_id_poll_id = p.id) as projection_ids
FROM poll_t p;


CREATE OR REPLACE VIEW "poll_ballot" AS SELECT * FROM poll_ballot_t p;


CREATE OR REPLACE VIEW "poll_ballot_user" AS SELECT *,
(select pb.id from poll_ballot_t pb where pb.poll_ballot_user_id = p.id) as poll_ballot_id
FROM poll_ballot_user_t p;


CREATE OR REPLACE VIEW "poll_config_approval" AS SELECT *,
(select p1.id from poll_t p1 where p1.config_id_poll_config_approval_id = p.id) as poll_id
FROM poll_config_approval_t p;


CREATE OR REPLACE VIEW "poll_config_rating_approval" AS SELECT *,
(select p1.id from poll_t p1 where p1.config_id_poll_config_rating_approval_id = p.id) as poll_id
FROM poll_config_rating_approval_t p;


CREATE OR REPLACE VIEW "poll_config_rating_score" AS SELECT *,
(select p1.id from poll_t p1 where p1.config_id_poll_config_rating_score_id = p.id) as poll_id
FROM poll_config_rating_score_t p;


CREATE OR REPLACE VIEW "poll_config_selection" AS SELECT *,
(select p1.id from poll_t p1 where p1.config_id_poll_config_selection_id = p.id) as poll_id
FROM poll_config_selection_t p;


CREATE OR REPLACE VIEW "poll_config_stv_scottish" AS SELECT *,
(select p1.id from poll_t p1 where p1.config_id_poll_config_stv_scottish_id = p.id) as poll_id
FROM poll_config_stv_scottish_t p;


CREATE OR REPLACE VIEW "poll_entitled_user" AS SELECT * FROM poll_entitled_user_t p;


CREATE OR REPLACE VIEW "poll_option" AS SELECT * FROM poll_option_t p;


CREATE OR REPLACE VIEW "projector" AS SELECT *,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.current_projector_id = p.id) as current_projection_ids,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.preview_projector_id = p.id) as preview_projection_ids,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.history_projector_id = p.id) as history_projection_ids,
(select m.id from meeting_t m where m.reference_projector_id = p.id) as used_as_reference_projector_meeting_id
FROM projector_t p;


CREATE OR REPLACE VIEW "topic" AS SELECT *,
(select array_agg(g.meeting_mediafile_id ORDER BY g.meeting_mediafile_id) from gm_meeting_mediafile_attachment_ids_t g where g.attachment_id_topic_id = t.id) as attachment_meeting_mediafile_ids,
(select a.id from agenda_item_t a where a.content_object_id_topic_id = t.id) as agenda_item_id,
(select l.id from list_of_speakers_t l where l.content_object_id_topic_id = t.id) as list_of_speakers_id,
(select array_agg(p.id ORDER BY p.id) from poll_t p where p.content_object_id_topic_id = t.id) as poll_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_topic_id = t.id) as projection_ids,
(select array_agg(h.id ORDER BY h.id) from history_entry_t h where h.model_id_topic_id = t.id) as history_entry_ids
FROM topic_t t;


CREATE OR REPLACE VIEW "user" AS SELECT *,
(select array_agg(n.meeting_id ORDER BY n.meeting_id) from nm_meeting_present_user_ids_user_t n where n.user_id = u.id) as is_present_in_meeting_ids,
(
  SELECT array_agg(DISTINCT ci.committee_id ORDER BY ci.committee_id)
  FROM (
    -- Select committee_ids from meetings the user is part of
    SELECT m.committee_id
    FROM meeting_user_t AS mu
    INNER JOIN meeting_t AS m ON m.id = mu.meeting_id
    WHERE mu.user_id = u.id

    UNION

    -- Select committee_ids from committee managers
    SELECT cmu.committee_id
    FROM nm_committee_manager_ids_user_t cmu
    WHERE cmu.user_id = u.id

    UNION

    -- Select home_committee_id from user
    SELECT u_hc.home_committee_id
    FROM user_t u_hc
    WHERE u_hc.home_committee_id IS NOT NULL AND u_hc.id = u.id
  ) AS ci
) AS committee_ids
,
(select array_agg(n.committee_id ORDER BY n.committee_id) from nm_committee_manager_ids_user_t n where n.user_id = u.id) as committee_management_ids,
(select array_agg(m.id ORDER BY m.id) from meeting_user_t m where m.user_id = u.id) as meeting_user_ids,
(select array_agg(p.id ORDER BY p.id) from poll_option_t p where p.content_object_id_user_id = u.id) as poll_option_ids,
(select array_agg(h.id ORDER BY h.id) from history_position_t h where h.user_id = u.id) as history_position_ids,
(select array_agg(h.id ORDER BY h.id) from history_entry_t h where h.model_id_user_id = u.id) as history_entry_ids,
(
  SELECT array_agg(DISTINCT mu.meeting_id ORDER BY mu.meeting_id)
  FROM meeting_user_t mu
  WHERE mu.user_id = u.id
) AS meeting_ids

FROM user_t u;

comment on column "user".committee_ids is 'Calculated field: Returns committee_ids, where the user is manager or member in a meeting';
comment on column "user".meeting_ids is 'Calculated. All ids from meetings calculated via meeting_user.';
