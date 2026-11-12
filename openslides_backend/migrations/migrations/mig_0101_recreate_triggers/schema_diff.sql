CREATE OR REPLACE FUNCTION log_iu_modified_calculated_id_array_field()
RETURNS trigger AS $log_modified_calculated_id_array_field_trigger$
-- Expects in this order:
-- 0. log_collection – Target collection for the log entry
-- 1. log_collection_id_column – Column used to fetch the 'log_collection' id
--    (ignored if 'log_collection_id_sql' is provided => may be NULL)
-- 2. log_collection_id_sql – Custom SQL to fetch the 'log_collection' id. Result column needs to be called 'id'
-- 3. log_field – Field to be logged
-- 4. added_item_column – Column used to fetch the value added to 'log_field'
--    (ignored if 'added_item_sql' is provided => may be NULL)
-- 5. added_item_sql – Custom SQL to fetch the value added to 'log_field'. Result column needs to be called 'id'
DECLARE
    log_collection TEXT := TG_ARGV[0];
    log_collection_id_column TEXT := TG_ARGV[1];
    log_collection_id_sql TEXT := TG_ARGV[2];
    log_field TEXT := TG_ARGV[3];
    added_item_column TEXT := TG_ARGV[4];
    added_item_sql TEXT := TG_ARGV[5];

    new_hstore hstore := hstore(NEW);
    log_collection_id INTEGER;
    log_collection_ids INTEGER[];
    added_item INTEGER;
    added_items INTEGER[];
    old_log_field_value INTEGER[];
    fqid_var TEXT;
BEGIN
    -- No related log_collection instance -> return
    IF (log_collection_id_sql <> '') THEN
        EXECUTE format('SELECT array_agg(DISTINCT id) FROM (%s);', log_collection_id_sql) INTO log_collection_ids USING NEW;
    ELSE
        log_collection_id := new_hstore -> log_collection_id_column;
        IF log_collection_id IS NULL THEN
            RETURN NEW;
        END IF;
        log_collection_ids := ARRAY[log_collection_id];
    END IF;

    IF array_length(log_collection_ids,1) IS NULL THEN
        RETURN NEW;
    END IF;

    -- No value in column used for log_field -> return
    -- Value deletion on update is processed in after-trigger
    IF (added_item_sql <> '') THEN
        EXECUTE format('SELECT array_agg(DISTINCT id) FROM (%s);', added_item_sql) INTO added_items USING NEW;
    ELSE
        added_item := new_hstore -> added_item_column;
        IF added_item IS NULL THEN
            RETURN NEW;
        END IF;
        added_items := ARRAY[added_item];
    END IF;

    IF array_length(added_items,1) IS NULL THEN
        RETURN NEW;
    END IF;

    -- Add log entries only if log_field value actually changes
    FOREACH log_collection_id IN ARRAY log_collection_ids LOOP
        EXECUTE format('SELECT %I from %I where id = %L', log_field, log_collection, log_collection_id) INTO old_log_field_value;
        IF old_log_field_value IS NULL OR NOT (added_items <@ old_log_field_value) THEN
            fqid_var := log_collection || '/' || log_collection_id;
            CALL log_field_change('update', fqid_var, ARRAY[log_field]);
        END IF;
    END LOOP;

    RETURN NEW;
END;
$log_modified_calculated_id_array_field_trigger$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION log_ud_modified_calculated_id_array_field()
RETURNS trigger AS $log_modified_calculated_id_array_field_trigger$
-- Expects in this order:
-- 0. log_collection – Target collection for the log entry
-- 1. log_collection_id_column – Column used to fetch the 'log_collection' id
--    (ignored if 'log_collection_id_sql' is provided => may be NULL)
-- 2. log_collection_id_sql – Custom SQL to fetch the 'log_collection' id. Result column needs to be called 'id'
-- 3. log_field – Field to be logged
-- 4. deleted_item_column – Column used to fetch the value deleted from 'log_field'
--    (ignored if 'deleted_item_sql' is provided => may be NULL)
-- 5. deleted_item_sql – Custom SQL to fetch the value deleted from 'log_field'. Result column needs to be called 'id'
DECLARE
    log_collection TEXT := TG_ARGV[0];
    log_collection_id_column TEXT := TG_ARGV[1];
    log_collection_id_sql TEXT := TG_ARGV[2];
    log_field TEXT := TG_ARGV[3];
    deleted_item_column TEXT := TG_ARGV[4];
    deleted_item_sql TEXT := TG_ARGV[5];

    old_hstore hstore := hstore(OLD);
    log_collection_id INTEGER;
    log_collection_ids INTEGER[];
    deleted_item INTEGER;
    deleted_items INTEGER[];
    new_log_field_value INTEGER[];
    fqid_var TEXT;
BEGIN
    -- No related log_collection instance -> return
    IF (log_collection_id_sql <> '') THEN
        EXECUTE format('SELECT array_agg(DISTINCT id) FROM (%s);', log_collection_id_sql) INTO log_collection_ids USING OLD;
    ELSE
        log_collection_id := old_hstore -> log_collection_id_column;
        IF log_collection_id IS NULL THEN
            RETURN NULL;
        END IF;
        log_collection_ids := ARRAY[log_collection_id];
    END IF;

    IF array_length(log_collection_ids,1) IS NULL THEN
        RETURN NULL;
    END IF;

    -- No value in column used for log_field -> return
    -- Value adding on update is processed in before-trigger
    IF (deleted_item_sql <> '') THEN
        EXECUTE format('SELECT array_agg(DISTINCT id) FROM (%s);', deleted_item_sql) INTO deleted_items USING OLD;
    ELSE
        deleted_item := old_hstore -> deleted_item_column;
        IF deleted_item IS NULL THEN
            RETURN NULL;
        END IF;
        deleted_items := ARRAY[deleted_item];
    END IF;

    IF array_length(deleted_items,1) IS NULL THEN
        RETURN NULL;
    END IF;

    -- Add log entries only if log_field value actually changes
    FOREACH log_collection_id IN ARRAY log_collection_ids LOOP
        EXECUTE format('SELECT %I from %I where id = %L', log_field, log_collection, log_collection_id) INTO new_log_field_value;
        IF new_log_field_value IS NULL OR NOT (deleted_items <@ new_log_field_value) THEN
            fqid_var := log_collection || '/' || log_collection_id;
            CALL log_field_change('update', fqid_var, ARRAY[log_field]);
        END IF;
    END LOOP;

    RETURN NULL;
END;
$log_modified_calculated_id_array_field_trigger$ LANGUAGE plpgsql;

-- Create triggers generating partitioned sequences

-- definition trigger generate partitioned sequence number for assignment_t.sequential_number partitioned by meeting_id
CREATE TRIGGER tr_generate_sequence_assignment_sequential_number BEFORE INSERT ON assignment_t
FOR EACH ROW EXECUTE FUNCTION generate_sequence('assignment_t', 'sequential_number', 'meeting_id');


-- definition trigger generate partitioned sequence number for list_of_speakers_t.sequential_number partitioned by meeting_id
CREATE TRIGGER tr_generate_sequence_list_of_speakers_sequential_number BEFORE INSERT ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION generate_sequence('list_of_speakers_t', 'sequential_number', 'meeting_id');


-- definition trigger generate partitioned sequence number for motion_t.sequential_number partitioned by meeting_id
CREATE TRIGGER tr_generate_sequence_motion_sequential_number BEFORE INSERT ON motion_t
FOR EACH ROW EXECUTE FUNCTION generate_sequence('motion_t', 'sequential_number', 'meeting_id');


-- definition trigger generate partitioned sequence number for motion_block_t.sequential_number partitioned by meeting_id
CREATE TRIGGER tr_generate_sequence_motion_block_sequential_number BEFORE INSERT ON motion_block_t
FOR EACH ROW EXECUTE FUNCTION generate_sequence('motion_block_t', 'sequential_number', 'meeting_id');


-- definition trigger generate partitioned sequence number for motion_category_t.sequential_number partitioned by meeting_id
CREATE TRIGGER tr_generate_sequence_motion_category_sequential_number BEFORE INSERT ON motion_category_t
FOR EACH ROW EXECUTE FUNCTION generate_sequence('motion_category_t', 'sequential_number', 'meeting_id');


-- definition trigger generate partitioned sequence number for motion_comment_section_t.sequential_number partitioned by meeting_id
CREATE TRIGGER tr_generate_sequence_motion_comment_section_sequential_number BEFORE INSERT ON motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION generate_sequence('motion_comment_section_t', 'sequential_number', 'meeting_id');


-- definition trigger generate partitioned sequence number for motion_workflow_t.sequential_number partitioned by meeting_id
CREATE TRIGGER tr_generate_sequence_motion_workflow_sequential_number BEFORE INSERT ON motion_workflow_t
FOR EACH ROW EXECUTE FUNCTION generate_sequence('motion_workflow_t', 'sequential_number', 'meeting_id');


-- definition trigger generate partitioned sequence number for poll_t.sequential_number partitioned by meeting_id
CREATE TRIGGER tr_generate_sequence_poll_sequential_number BEFORE INSERT ON poll_t
FOR EACH ROW EXECUTE FUNCTION generate_sequence('poll_t', 'sequential_number', 'meeting_id');


-- definition trigger generate partitioned sequence number for projector_t.sequential_number partitioned by meeting_id
CREATE TRIGGER tr_generate_sequence_projector_sequential_number BEFORE INSERT ON projector_t
FOR EACH ROW EXECUTE FUNCTION generate_sequence('projector_t', 'sequential_number', 'meeting_id');


-- definition trigger generate partitioned sequence number for topic_t.sequential_number partitioned by meeting_id
CREATE TRIGGER tr_generate_sequence_topic_sequential_number BEFORE INSERT ON topic_t
FOR EACH ROW EXECUTE FUNCTION generate_sequence('topic_t', 'sequential_number', 'meeting_id');



-- Create triggers checking foreign_id not null for view-relations and no duplicates in 1:1 relationships

-- definition trigger not null for assignment.list_of_speakers_id against list_of_speakers.content_object_id_assignment_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_assignment_list_of_speakers_id AFTER INSERT ON assignment_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('assignment', 'list_of_speakers_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_assignment_list_of_speakers_id AFTER UPDATE OF content_object_id_assignment_id OR DELETE ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('assignment', 'list_of_speakers_id', 'list_of_speakers', 'content_object_id_assignment_id');


-- definition trigger not null for motion.list_of_speakers_id against list_of_speakers.content_object_id_motion_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_motion_list_of_speakers_id AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('motion', 'list_of_speakers_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_motion_list_of_speakers_id AFTER UPDATE OF content_object_id_motion_id OR DELETE ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('motion', 'list_of_speakers_id', 'list_of_speakers', 'content_object_id_motion_id');


-- definition trigger not null for motion_block.list_of_speakers_id against list_of_speakers.content_object_id_motion_block_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_motion_block_list_of_speakers_id AFTER INSERT ON motion_block_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('motion_block', 'list_of_speakers_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_motion_block_list_of_speakers_id AFTER UPDATE OF content_object_id_motion_block_id OR DELETE ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('motion_block', 'list_of_speakers_id', 'list_of_speakers', 'content_object_id_motion_block_id');


-- definition trigger not null for poll_candidate_list.option_id against option.content_object_id_poll_candidate_list_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_poll_candidate_list_option_id AFTER INSERT ON poll_candidate_list_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_candidate_list', 'option_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_poll_candidate_list_option_id AFTER UPDATE OF content_object_id_poll_candidate_list_id OR DELETE ON option_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('poll_candidate_list', 'option_id', 'option', 'content_object_id_poll_candidate_list_id');


-- definition trigger not null for topic.agenda_item_id against agenda_item.content_object_id_topic_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_topic_agenda_item_id AFTER INSERT ON topic_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('topic', 'agenda_item_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_topic_agenda_item_id AFTER UPDATE OF content_object_id_topic_id OR DELETE ON agenda_item_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('topic', 'agenda_item_id', 'agenda_item', 'content_object_id_topic_id');

-- definition trigger not null for topic.list_of_speakers_id against list_of_speakers.content_object_id_topic_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_topic_list_of_speakers_id AFTER INSERT ON topic_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('topic', 'list_of_speakers_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_topic_list_of_speakers_id AFTER UPDATE OF content_object_id_topic_id OR DELETE ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_1('topic', 'list_of_speakers_id', 'list_of_speakers', 'content_object_id_topic_id');



-- Create triggers checking foreign_id not null for 1:n relationships

-- definition trigger not null for meeting.default_projector_agenda_item_list_ids against projector.used_as_default_projector_for_agenda_item_list_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_agenda_item_list_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_agenda_item_list_ids', 'projector_t', 'used_as_default_projector_for_agenda_item_list_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_agenda_item_list_ids AFTER UPDATE OF used_as_default_projector_for_agenda_item_list_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_agenda_item_list_ids', 'projector_t', 'used_as_default_projector_for_agenda_item_list_in_meeting_id');


-- definition trigger not null for meeting.default_projector_topic_ids against projector.used_as_default_projector_for_topic_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_topic_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_topic_ids', 'projector_t', 'used_as_default_projector_for_topic_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_topic_ids AFTER UPDATE OF used_as_default_projector_for_topic_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_topic_ids', 'projector_t', 'used_as_default_projector_for_topic_in_meeting_id');


-- definition trigger not null for meeting.default_projector_list_of_speakers_ids against projector.used_as_default_projector_for_list_of_speakers_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_list_of_speakers_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_list_of_speakers_ids', 'projector_t', 'used_as_default_projector_for_list_of_speakers_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_list_of_speakers_ids AFTER UPDATE OF used_as_default_projector_for_list_of_speakers_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_list_of_speakers_ids', 'projector_t', 'used_as_default_projector_for_list_of_speakers_in_meeting_id');


-- definition trigger not null for meeting.default_projector_current_los_ids against projector.used_as_default_projector_for_current_los_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_current_los_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_current_los_ids', 'projector_t', 'used_as_default_projector_for_current_los_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_current_los_ids AFTER UPDATE OF used_as_default_projector_for_current_los_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_current_los_ids', 'projector_t', 'used_as_default_projector_for_current_los_in_meeting_id');


-- definition trigger not null for meeting.default_projector_motion_ids against projector.used_as_default_projector_for_motion_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_motion_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_motion_ids', 'projector_t', 'used_as_default_projector_for_motion_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_motion_ids AFTER UPDATE OF used_as_default_projector_for_motion_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_motion_ids', 'projector_t', 'used_as_default_projector_for_motion_in_meeting_id');


-- definition trigger not null for meeting.default_projector_amendment_ids against projector.used_as_default_projector_for_amendment_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_amendment_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_amendment_ids', 'projector_t', 'used_as_default_projector_for_amendment_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_amendment_ids AFTER UPDATE OF used_as_default_projector_for_amendment_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_amendment_ids', 'projector_t', 'used_as_default_projector_for_amendment_in_meeting_id');


-- definition trigger not null for meeting.default_projector_motion_block_ids against projector.used_as_default_projector_for_motion_block_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_motion_block_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_motion_block_ids', 'projector_t', 'used_as_default_projector_for_motion_block_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_motion_block_ids AFTER UPDATE OF used_as_default_projector_for_motion_block_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_motion_block_ids', 'projector_t', 'used_as_default_projector_for_motion_block_in_meeting_id');


-- definition trigger not null for meeting.default_projector_assignment_ids against projector.used_as_default_projector_for_assignment_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_assignment_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_assignment_ids', 'projector_t', 'used_as_default_projector_for_assignment_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_assignment_ids AFTER UPDATE OF used_as_default_projector_for_assignment_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_assignment_ids', 'projector_t', 'used_as_default_projector_for_assignment_in_meeting_id');


-- definition trigger not null for meeting.default_projector_mediafile_ids against projector.used_as_default_projector_for_mediafile_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_mediafile_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_mediafile_ids', 'projector_t', 'used_as_default_projector_for_mediafile_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_mediafile_ids AFTER UPDATE OF used_as_default_projector_for_mediafile_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_mediafile_ids', 'projector_t', 'used_as_default_projector_for_mediafile_in_meeting_id');


-- definition trigger not null for meeting.default_projector_message_ids against projector.used_as_default_projector_for_message_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_message_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_message_ids', 'projector_t', 'used_as_default_projector_for_message_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_message_ids AFTER UPDATE OF used_as_default_projector_for_message_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_message_ids', 'projector_t', 'used_as_default_projector_for_message_in_meeting_id');


-- definition trigger not null for meeting.default_projector_countdown_ids against projector.used_as_default_projector_for_countdown_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_countdown_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_countdown_ids', 'projector_t', 'used_as_default_projector_for_countdown_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_countdown_ids AFTER UPDATE OF used_as_default_projector_for_countdown_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_countdown_ids', 'projector_t', 'used_as_default_projector_for_countdown_in_meeting_id');


-- definition trigger not null for meeting.default_projector_assignment_poll_ids against projector.used_as_default_projector_for_assignment_poll_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_assignment_poll_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_assignment_poll_ids', 'projector_t', 'used_as_default_projector_for_assignment_poll_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_assignment_poll_ids AFTER UPDATE OF used_as_default_projector_for_assignment_poll_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_assignment_poll_ids', 'projector_t', 'used_as_default_projector_for_assignment_poll_in_meeting_id');


-- definition trigger not null for meeting.default_projector_motion_poll_ids against projector.used_as_default_projector_for_motion_poll_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_motion_poll_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_motion_poll_ids', 'projector_t', 'used_as_default_projector_for_motion_poll_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_motion_poll_ids AFTER UPDATE OF used_as_default_projector_for_motion_poll_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_motion_poll_ids', 'projector_t', 'used_as_default_projector_for_motion_poll_in_meeting_id');


-- definition trigger not null for meeting.default_projector_poll_ids against projector.used_as_default_projector_for_poll_in_meeting_id
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_default_projector_poll_ids AFTER INSERT ON meeting_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_poll_ids', 'projector_t', 'used_as_default_projector_for_poll_in_meeting_id');

CREATE CONSTRAINT TRIGGER tr_ud_not_null_meeting_default_projector_poll_ids AFTER UPDATE OF used_as_default_projector_for_poll_in_meeting_id OR DELETE ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_1_n('meeting_t', 'default_projector_poll_ids', 'projector_t', 'used_as_default_projector_for_poll_in_meeting_id');




-- Create triggers checking foreign_ids not null for n:m relationships

-- definition trigger not null for meeting_user.group_ids against group.meeting_user_ids through nm_group_meeting_user_ids_meeting_user_t
CREATE CONSTRAINT TRIGGER tr_i_not_null_meeting_user_group_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_n_m('nm_group_meeting_user_ids_meeting_user_t', 'meeting_user_t', 'group_ids', 'meeting_user_id');

CREATE CONSTRAINT TRIGGER tr_d_not_null_meeting_user_group_ids AFTER DELETE ON nm_group_meeting_user_ids_meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_not_null_for_n_m('nm_group_meeting_user_ids_meeting_user_t', 'meeting_user_t', 'group_ids', 'meeting_user_id', 'group_id', 'group', 'meeting_user_ids');




-- Create triggers for constant fields

-- definition trigger prevent_updates for action_worker.user_id
CREATE TRIGGER tr_constant_action_worker_user_id BEFORE UPDATE OF user_id ON action_worker_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('action_worker', 'user_id');


-- definition trigger prevent_updates for agenda_item.content_object_id
CREATE TRIGGER tr_constant_agenda_item_content_object_id BEFORE UPDATE OF content_object_id ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('agenda_item', 'content_object_id');

-- definition trigger prevent_updates for agenda_item.meeting_id
CREATE TRIGGER tr_constant_agenda_item_meeting_id BEFORE UPDATE OF meeting_id ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('agenda_item', 'meeting_id');


-- definition trigger prevent_updates for assignment.sequential_number
CREATE TRIGGER tr_constant_assignment_sequential_number BEFORE UPDATE OF sequential_number ON assignment_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('assignment', 'sequential_number');

-- definition trigger prevent_updates for assignment.meeting_id
CREATE TRIGGER tr_constant_assignment_meeting_id BEFORE UPDATE OF meeting_id ON assignment_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('assignment', 'meeting_id');


-- definition trigger prevent_updates for assignment_candidate.assignment_id
CREATE TRIGGER tr_constant_assignment_candidate_assignment_id BEFORE UPDATE OF assignment_id ON assignment_candidate_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('assignment_candidate', 'assignment_id');

-- definition trigger prevent_updates for assignment_candidate.meeting_id
CREATE TRIGGER tr_constant_assignment_candidate_meeting_id BEFORE UPDATE OF meeting_id ON assignment_candidate_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('assignment_candidate', 'meeting_id');


-- definition trigger prevent_updates for chat_group.meeting_id
CREATE TRIGGER tr_constant_chat_group_meeting_id BEFORE UPDATE OF meeting_id ON chat_group_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('chat_group', 'meeting_id');


-- definition trigger prevent_updates for chat_message.chat_group_id
CREATE TRIGGER tr_constant_chat_message_chat_group_id BEFORE UPDATE OF chat_group_id ON chat_message_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('chat_message', 'chat_group_id');

-- definition trigger prevent_updates for chat_message.meeting_id
CREATE TRIGGER tr_constant_chat_message_meeting_id BEFORE UPDATE OF meeting_id ON chat_message_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('chat_message', 'meeting_id');


-- definition trigger prevent_updates for committee.organization_id
CREATE TRIGGER tr_constant_committee_organization_id BEFORE UPDATE OF organization_id ON committee_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('committee', 'organization_id');


-- definition trigger prevent_updates for gender.organization_id
CREATE TRIGGER tr_constant_gender_organization_id BEFORE UPDATE OF organization_id ON gender_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('gender', 'organization_id');


-- definition trigger prevent_updates for group.meeting_id
CREATE TRIGGER tr_constant_group_meeting_id BEFORE UPDATE OF meeting_id ON group_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('group', 'meeting_id');


-- definition trigger prevent_updates for history_entry.original_model_id
CREATE TRIGGER tr_constant_history_entry_original_model_id BEFORE UPDATE OF original_model_id ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('history_entry', 'original_model_id');

-- definition trigger prevent_updates for history_entry.position_id
CREATE TRIGGER tr_constant_history_entry_position_id BEFORE UPDATE OF position_id ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('history_entry', 'position_id');


-- definition trigger prevent_updates for history_position.original_user_id
CREATE TRIGGER tr_constant_history_position_original_user_id BEFORE UPDATE OF original_user_id ON history_position_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('history_position', 'original_user_id');


-- definition trigger prevent_updates for list_of_speakers.sequential_number
CREATE TRIGGER tr_constant_list_of_speakers_sequential_number BEFORE UPDATE OF sequential_number ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('list_of_speakers', 'sequential_number');

-- definition trigger prevent_updates for list_of_speakers.content_object_id
CREATE TRIGGER tr_constant_list_of_speakers_content_object_id BEFORE UPDATE OF content_object_id ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('list_of_speakers', 'content_object_id');

-- definition trigger prevent_updates for list_of_speakers.meeting_id
CREATE TRIGGER tr_constant_list_of_speakers_meeting_id BEFORE UPDATE OF meeting_id ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('list_of_speakers', 'meeting_id');


-- definition trigger prevent_updates for mediafile.owner_id
CREATE TRIGGER tr_constant_mediafile_owner_id BEFORE UPDATE OF owner_id ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('mediafile', 'owner_id');


-- definition trigger prevent_updates for meeting.language
CREATE TRIGGER tr_constant_meeting_language BEFORE UPDATE OF language ON meeting_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('meeting', 'language');

-- definition trigger prevent_updates for meeting.committee_id
CREATE TRIGGER tr_constant_meeting_committee_id BEFORE UPDATE OF committee_id ON meeting_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('meeting', 'committee_id');


-- definition trigger prevent_updates for meeting_mediafile.meeting_id
CREATE TRIGGER tr_constant_meeting_mediafile_meeting_id BEFORE UPDATE OF meeting_id ON meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('meeting_mediafile', 'meeting_id');


-- definition trigger prevent_updates for meeting_user.user_id
CREATE TRIGGER tr_constant_meeting_user_user_id BEFORE UPDATE OF user_id ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('meeting_user', 'user_id');

-- definition trigger prevent_updates for meeting_user.meeting_id
CREATE TRIGGER tr_constant_meeting_user_meeting_id BEFORE UPDATE OF meeting_id ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('meeting_user', 'meeting_id');


-- definition trigger prevent_updates for motion.sequential_number
CREATE TRIGGER tr_constant_motion_sequential_number BEFORE UPDATE OF sequential_number ON motion_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion', 'sequential_number');

-- definition trigger prevent_updates for motion.meeting_id
CREATE TRIGGER tr_constant_motion_meeting_id BEFORE UPDATE OF meeting_id ON motion_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion', 'meeting_id');


-- definition trigger prevent_updates for motion_block.sequential_number
CREATE TRIGGER tr_constant_motion_block_sequential_number BEFORE UPDATE OF sequential_number ON motion_block_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_block', 'sequential_number');

-- definition trigger prevent_updates for motion_block.meeting_id
CREATE TRIGGER tr_constant_motion_block_meeting_id BEFORE UPDATE OF meeting_id ON motion_block_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_block', 'meeting_id');


-- definition trigger prevent_updates for motion_category.sequential_number
CREATE TRIGGER tr_constant_motion_category_sequential_number BEFORE UPDATE OF sequential_number ON motion_category_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_category', 'sequential_number');

-- definition trigger prevent_updates for motion_category.meeting_id
CREATE TRIGGER tr_constant_motion_category_meeting_id BEFORE UPDATE OF meeting_id ON motion_category_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_category', 'meeting_id');


-- definition trigger prevent_updates for motion_change_recommendation.motion_id
CREATE TRIGGER tr_constant_motion_change_recommendation_motion_id BEFORE UPDATE OF motion_id ON motion_change_recommendation_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_change_recommendation', 'motion_id');

-- definition trigger prevent_updates for motion_change_recommendation.meeting_id
CREATE TRIGGER tr_constant_motion_change_recommendation_meeting_id BEFORE UPDATE OF meeting_id ON motion_change_recommendation_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_change_recommendation', 'meeting_id');


-- definition trigger prevent_updates for motion_comment.motion_id
CREATE TRIGGER tr_constant_motion_comment_motion_id BEFORE UPDATE OF motion_id ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_comment', 'motion_id');

-- definition trigger prevent_updates for motion_comment.section_id
CREATE TRIGGER tr_constant_motion_comment_section_id BEFORE UPDATE OF section_id ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_comment', 'section_id');

-- definition trigger prevent_updates for motion_comment.meeting_id
CREATE TRIGGER tr_constant_motion_comment_meeting_id BEFORE UPDATE OF meeting_id ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_comment', 'meeting_id');


-- definition trigger prevent_updates for motion_comment_section.sequential_number
CREATE TRIGGER tr_constant_motion_comment_section_sequential_number BEFORE UPDATE OF sequential_number ON motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_comment_section', 'sequential_number');

-- definition trigger prevent_updates for motion_comment_section.meeting_id
CREATE TRIGGER tr_constant_motion_comment_section_meeting_id BEFORE UPDATE OF meeting_id ON motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_comment_section', 'meeting_id');


-- definition trigger prevent_updates for motion_editor.motion_id
CREATE TRIGGER tr_constant_motion_editor_motion_id BEFORE UPDATE OF motion_id ON motion_editor_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_editor', 'motion_id');

-- definition trigger prevent_updates for motion_editor.meeting_id
CREATE TRIGGER tr_constant_motion_editor_meeting_id BEFORE UPDATE OF meeting_id ON motion_editor_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_editor', 'meeting_id');


-- definition trigger prevent_updates for motion_state.meeting_id
CREATE TRIGGER tr_constant_motion_state_meeting_id BEFORE UPDATE OF meeting_id ON motion_state_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_state', 'meeting_id');


-- definition trigger prevent_updates for motion_submitter.motion_id
CREATE TRIGGER tr_constant_motion_submitter_motion_id BEFORE UPDATE OF motion_id ON motion_submitter_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_submitter', 'motion_id');

-- definition trigger prevent_updates for motion_submitter.meeting_id
CREATE TRIGGER tr_constant_motion_submitter_meeting_id BEFORE UPDATE OF meeting_id ON motion_submitter_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_submitter', 'meeting_id');


-- definition trigger prevent_updates for motion_supporter.motion_id
CREATE TRIGGER tr_constant_motion_supporter_motion_id BEFORE UPDATE OF motion_id ON motion_supporter_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_supporter', 'motion_id');

-- definition trigger prevent_updates for motion_supporter.meeting_id
CREATE TRIGGER tr_constant_motion_supporter_meeting_id BEFORE UPDATE OF meeting_id ON motion_supporter_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_supporter', 'meeting_id');


-- definition trigger prevent_updates for motion_workflow.sequential_number
CREATE TRIGGER tr_constant_motion_workflow_sequential_number BEFORE UPDATE OF sequential_number ON motion_workflow_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_workflow', 'sequential_number');

-- definition trigger prevent_updates for motion_workflow.meeting_id
CREATE TRIGGER tr_constant_motion_workflow_meeting_id BEFORE UPDATE OF meeting_id ON motion_workflow_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_workflow', 'meeting_id');


-- definition trigger prevent_updates for motion_working_group_speaker.motion_id
CREATE TRIGGER tr_constant_motion_working_group_speaker_motion_id BEFORE UPDATE OF motion_id ON motion_working_group_speaker_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_working_group_speaker', 'motion_id');

-- definition trigger prevent_updates for motion_working_group_speaker.meeting_id
CREATE TRIGGER tr_constant_motion_working_group_speaker_meeting_id BEFORE UPDATE OF meeting_id ON motion_working_group_speaker_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('motion_working_group_speaker', 'meeting_id');


-- definition trigger prevent_updates for option.poll_id
CREATE TRIGGER tr_constant_option_poll_id BEFORE UPDATE OF poll_id ON option_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('option', 'poll_id');

-- definition trigger prevent_updates for option.meeting_id
CREATE TRIGGER tr_constant_option_meeting_id BEFORE UPDATE OF meeting_id ON option_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('option', 'meeting_id');


-- definition trigger prevent_updates for organization_tag.organization_id
CREATE TRIGGER tr_constant_organization_tag_organization_id BEFORE UPDATE OF organization_id ON organization_tag_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('organization_tag', 'organization_id');


-- definition trigger prevent_updates for personal_note.meeting_user_id
CREATE TRIGGER tr_constant_personal_note_meeting_user_id BEFORE UPDATE OF meeting_user_id ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('personal_note', 'meeting_user_id');

-- definition trigger prevent_updates for personal_note.content_object_id
CREATE TRIGGER tr_constant_personal_note_content_object_id BEFORE UPDATE OF content_object_id ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('personal_note', 'content_object_id');

-- definition trigger prevent_updates for personal_note.meeting_id
CREATE TRIGGER tr_constant_personal_note_meeting_id BEFORE UPDATE OF meeting_id ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('personal_note', 'meeting_id');


-- definition trigger prevent_updates for point_of_order_category.meeting_id
CREATE TRIGGER tr_constant_point_of_order_category_meeting_id BEFORE UPDATE OF meeting_id ON point_of_order_category_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('point_of_order_category', 'meeting_id');


-- definition trigger prevent_updates for poll.sequential_number
CREATE TRIGGER tr_constant_poll_sequential_number BEFORE UPDATE OF sequential_number ON poll_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('poll', 'sequential_number');

-- definition trigger prevent_updates for poll.content_object_id
CREATE TRIGGER tr_constant_poll_content_object_id BEFORE UPDATE OF content_object_id ON poll_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('poll', 'content_object_id');

-- definition trigger prevent_updates for poll.meeting_id
CREATE TRIGGER tr_constant_poll_meeting_id BEFORE UPDATE OF meeting_id ON poll_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('poll', 'meeting_id');


-- definition trigger prevent_updates for poll_candidate.poll_candidate_list_id
CREATE TRIGGER tr_constant_poll_candidate_poll_candidate_list_id BEFORE UPDATE OF poll_candidate_list_id ON poll_candidate_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('poll_candidate', 'poll_candidate_list_id');

-- definition trigger prevent_updates for poll_candidate.meeting_id
CREATE TRIGGER tr_constant_poll_candidate_meeting_id BEFORE UPDATE OF meeting_id ON poll_candidate_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('poll_candidate', 'meeting_id');


-- definition trigger prevent_updates for poll_candidate_list.meeting_id
CREATE TRIGGER tr_constant_poll_candidate_list_meeting_id BEFORE UPDATE OF meeting_id ON poll_candidate_list_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('poll_candidate_list', 'meeting_id');


-- definition trigger prevent_updates for projection.content_object_id
CREATE TRIGGER tr_constant_projection_content_object_id BEFORE UPDATE OF content_object_id ON projection_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('projection', 'content_object_id');

-- definition trigger prevent_updates for projection.meeting_id
CREATE TRIGGER tr_constant_projection_meeting_id BEFORE UPDATE OF meeting_id ON projection_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('projection', 'meeting_id');


-- definition trigger prevent_updates for projector.sequential_number
CREATE TRIGGER tr_constant_projector_sequential_number BEFORE UPDATE OF sequential_number ON projector_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('projector', 'sequential_number');

-- definition trigger prevent_updates for projector.meeting_id
CREATE TRIGGER tr_constant_projector_meeting_id BEFORE UPDATE OF meeting_id ON projector_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('projector', 'meeting_id');


-- definition trigger prevent_updates for projector_countdown.meeting_id
CREATE TRIGGER tr_constant_projector_countdown_meeting_id BEFORE UPDATE OF meeting_id ON projector_countdown_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('projector_countdown', 'meeting_id');


-- definition trigger prevent_updates for projector_message.meeting_id
CREATE TRIGGER tr_constant_projector_message_meeting_id BEFORE UPDATE OF meeting_id ON projector_message_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('projector_message', 'meeting_id');


-- definition trigger prevent_updates for speaker.list_of_speakers_id
CREATE TRIGGER tr_constant_speaker_list_of_speakers_id BEFORE UPDATE OF list_of_speakers_id ON speaker_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('speaker', 'list_of_speakers_id');

-- definition trigger prevent_updates for speaker.meeting_id
CREATE TRIGGER tr_constant_speaker_meeting_id BEFORE UPDATE OF meeting_id ON speaker_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('speaker', 'meeting_id');


-- definition trigger prevent_updates for structure_level.meeting_id
CREATE TRIGGER tr_constant_structure_level_meeting_id BEFORE UPDATE OF meeting_id ON structure_level_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('structure_level', 'meeting_id');


-- definition trigger prevent_updates for structure_level_list_of_speakers.meeting_id
CREATE TRIGGER tr_constant_structure_level_list_of_speakers_meeting_id BEFORE UPDATE OF meeting_id ON structure_level_list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('structure_level_list_of_speakers', 'meeting_id');


-- definition trigger prevent_updates for tag.meeting_id
CREATE TRIGGER tr_constant_tag_meeting_id BEFORE UPDATE OF meeting_id ON tag_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('tag', 'meeting_id');


-- definition trigger prevent_updates for theme.organization_id
CREATE TRIGGER tr_constant_theme_organization_id BEFORE UPDATE OF organization_id ON theme_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('theme', 'organization_id');


-- definition trigger prevent_updates for topic.sequential_number
CREATE TRIGGER tr_constant_topic_sequential_number BEFORE UPDATE OF sequential_number ON topic_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('topic', 'sequential_number');

-- definition trigger prevent_updates for topic.meeting_id
CREATE TRIGGER tr_constant_topic_meeting_id BEFORE UPDATE OF meeting_id ON topic_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('topic', 'meeting_id');


-- definition trigger prevent_updates for user.organization_id
CREATE TRIGGER tr_constant_user_organization_id BEFORE UPDATE OF organization_id ON user_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('user', 'organization_id');


-- definition trigger prevent_updates for vote.value
CREATE TRIGGER tr_constant_vote_value BEFORE UPDATE OF value ON vote_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('vote', 'value');

-- definition trigger prevent_updates for vote.user_token
CREATE TRIGGER tr_constant_vote_user_token BEFORE UPDATE OF user_token ON vote_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('vote', 'user_token');

-- definition trigger prevent_updates for vote.option_id
CREATE TRIGGER tr_constant_vote_option_id BEFORE UPDATE OF option_id ON vote_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('vote', 'option_id');

-- definition trigger prevent_updates for vote.meeting_id
CREATE TRIGGER tr_constant_vote_meeting_id BEFORE UPDATE OF meeting_id ON vote_t
FOR EACH ROW EXECUTE FUNCTION prevent_updates('vote', 'meeting_id');



-- Create triggers preventing mirrored duplicates in fields referencing themselves

-- definition trigger unique ids pair for motion.identical_motion_ids
CREATE TRIGGER tr_restrict_unique_ids_pair_motion_identical_motion_ids BEFORE INSERT OR UPDATE ON nm_motion_identical_motion_ids_motion_t
FOR EACH ROW EXECUTE FUNCTION check_unique_ids_pair('identical_motion_id');




-- Create triggers for notify
-- notify triggers for action_worker_t fields
CREATE TRIGGER tr_log_action_worker AFTER INSERT OR UPDATE OR DELETE ON action_worker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('action_worker');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON action_worker_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for agenda_item_t fields
CREATE TRIGGER tr_log_agenda_item AFTER INSERT OR UPDATE OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('agenda_item');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON agenda_item_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- notify trigger for agenda_item_t.content_object_id_motion_id
CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','agenda_item_id');

-- notify trigger for agenda_item_t.content_object_id_motion_block_id
CREATE TRIGGER tr_log_motion_block_content_object_id_motion_block_id AFTER INSERT OR UPDATE OF content_object_id_motion_block_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_block','content_object_id_motion_block_id','agenda_item_id');

-- notify trigger for agenda_item_t.content_object_id_assignment_id
CREATE TRIGGER tr_log_assignment_content_object_id_assignment_id AFTER INSERT OR UPDATE OF content_object_id_assignment_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment','content_object_id_assignment_id','agenda_item_id');

-- notify trigger for agenda_item_t.content_object_id_topic_id
CREATE TRIGGER tr_log_topic_content_object_id_topic_id AFTER INSERT OR UPDATE OF content_object_id_topic_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('topic','content_object_id_topic_id','agenda_item_id');
-- notify trigger for agenda_item_t.parent_id
CREATE TRIGGER tr_log_agenda_item_t_parent_id AFTER INSERT OR UPDATE OF parent_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('agenda_item', 'parent_id', 'child_ids');
-- notify trigger for agenda_item_t.meeting_id
CREATE TRIGGER tr_log_agenda_item_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'agenda_item_ids');

-- notify triggers for assignment_t fields
CREATE TRIGGER tr_log_assignment AFTER INSERT OR UPDATE OR DELETE ON assignment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('assignment');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON assignment_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for assignment_t.meeting_id
CREATE TRIGGER tr_log_assignment_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON assignment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'assignment_ids');

-- notify triggers for assignment_candidate_t fields
CREATE TRIGGER tr_log_assignment_candidate AFTER INSERT OR UPDATE OR DELETE ON assignment_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('assignment_candidate');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON assignment_candidate_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for assignment_candidate_t.assignment_id
CREATE TRIGGER tr_log_assignment_candidate_t_assignment_id AFTER INSERT OR UPDATE OF assignment_id OR DELETE ON assignment_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment', 'assignment_id', 'candidate_ids');
-- notify trigger for assignment_candidate_t.meeting_user_id
CREATE TRIGGER tr_log_assignment_candidate_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON assignment_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'assignment_candidate_ids');
-- notify trigger for assignment_candidate_t.meeting_id
CREATE TRIGGER tr_log_assignment_candidate_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON assignment_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'assignment_candidate_ids');

-- notify triggers for chat_group_t fields
CREATE TRIGGER tr_log_chat_group AFTER INSERT OR UPDATE OR DELETE ON chat_group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('chat_group');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON chat_group_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- notify triggers for chat_group.read_group_ids and group.read_chat_group_ids
CREATE TRIGGER tr_log_nm_chat_group_read_group_ids_group_t AFTER INSERT OR UPDATE OR DELETE ON nm_chat_group_read_group_ids_group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('chat_group','chat_group_id','read_group_ids','group','group_id','read_chat_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_chat_group_read_group_ids_group_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for chat_group.write_group_ids and group.write_chat_group_ids
CREATE TRIGGER tr_log_nm_chat_group_write_group_ids_group_t AFTER INSERT OR UPDATE OR DELETE ON nm_chat_group_write_group_ids_group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('chat_group','chat_group_id','write_group_ids','group','group_id','write_chat_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_chat_group_write_group_ids_group_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
-- notify trigger for chat_group_t.meeting_id
CREATE TRIGGER tr_log_chat_group_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON chat_group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'chat_group_ids');

-- notify triggers for chat_message_t fields
CREATE TRIGGER tr_log_chat_message AFTER INSERT OR UPDATE OR DELETE ON chat_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('chat_message');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON chat_message_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for chat_message_t.meeting_user_id
CREATE TRIGGER tr_log_chat_message_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON chat_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'chat_message_ids');
-- notify trigger for chat_message_t.chat_group_id
CREATE TRIGGER tr_log_chat_message_t_chat_group_id AFTER INSERT OR UPDATE OF chat_group_id OR DELETE ON chat_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('chat_group', 'chat_group_id', 'chat_message_ids');
-- notify trigger for chat_message_t.meeting_id
CREATE TRIGGER tr_log_chat_message_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON chat_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'chat_message_ids');

-- notify triggers for committee_t fields
CREATE TRIGGER tr_log_committee AFTER INSERT OR UPDATE OR DELETE ON committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('committee');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON committee_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for committee_t.default_meeting_id
CREATE TRIGGER tr_log_committee_t_default_meeting_id AFTER INSERT OR UPDATE OF default_meeting_id OR DELETE ON committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'default_meeting_id', 'default_meeting_for_committee_id');

CREATE TRIGGER tr_log_i_committee_user_ids_from_meeting_user_t BEFORE INSERT ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('committee', '', 'SELECT committee_id AS id FROM meeting_t WHERE id = ($1).meeting_id', 'user_ids', 'user_id', '');
CREATE TRIGGER tr_log_d_committee_user_ids_from_meeting_user_t AFTER DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('committee', '', 'SELECT committee_id AS id FROM meeting_t WHERE id = ($1).meeting_id', 'user_ids', 'user_id', '');
CREATE TRIGGER tr_log_i_committee_user_ids_from_meeting_t BEFORE INSERT ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('committee', 'committee_id', '', 'user_ids', '', 'SELECT user_id AS id FROM meeting_user_t WHERE meeting_id = ($1).id');
CREATE TRIGGER tr_log_d_committee_user_ids_from_meeting_t AFTER DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('committee', 'committee_id', '', 'user_ids', '', 'SELECT user_id AS id FROM meeting_user_t WHERE meeting_id = ($1).id');
CREATE TRIGGER tr_log_i_committee_user_ids_from_nm_committee_manager_idd4a2a53 BEFORE INSERT ON nm_committee_manager_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('committee', 'committee_id', '', 'user_ids', 'user_id', '');
CREATE TRIGGER tr_log_d_committee_user_ids_from_nm_committee_manager_id82dfd00 AFTER DELETE ON nm_committee_manager_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('committee', 'committee_id', '', 'user_ids', 'user_id', '');
CREATE TRIGGER tr_log_iu_committee_user_ids_from_user_t BEFORE INSERT OR UPDATE OF home_committee_id ON user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('committee', 'home_committee_id', '', 'user_ids', 'id', '');
CREATE TRIGGER tr_log_ud_committee_user_ids_from_user_t AFTER UPDATE OF home_committee_id OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('committee', 'home_committee_id', '', 'user_ids', 'id', '');


-- notify triggers for committee.manager_ids and user.committee_management_ids
CREATE TRIGGER tr_log_nm_committee_manager_ids_user_t AFTER INSERT OR UPDATE OR DELETE ON nm_committee_manager_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee','committee_id','manager_ids','user','user_id','committee_management_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_committee_manager_ids_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
-- notify trigger for committee_t.parent_id
CREATE TRIGGER tr_log_committee_t_parent_id AFTER INSERT OR UPDATE OF parent_id OR DELETE ON committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee', 'parent_id', 'child_ids');

-- notify triggers for committee.all_child_ids and committee.all_parent_ids
CREATE TRIGGER tr_log_nm_committee_all_child_ids_committee_t AFTER INSERT OR UPDATE OR DELETE ON nm_committee_all_child_ids_committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee','all_parent_id','all_child_ids','committee','all_child_id','all_parent_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_committee_all_child_ids_committee_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for committee.forward_to_committee_ids and committee.receive_forwardings_from_committee_ids
CREATE TRIGGER tr_log_nm_committee_forward_to_committee_ids_committee_t AFTER INSERT OR UPDATE OR DELETE ON nm_committee_forward_to_committee_ids_committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee','receive_forwardings_from_committee_id','forward_to_committee_ids','committee','forward_to_committee_id','receive_forwardings_from_committee_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_committee_forward_to_committee_ids_committee_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
-- notify trigger for committee_t.organization_id
CREATE TRIGGER tr_log_committee_t_organization_id AFTER INSERT OR UPDATE OF organization_id OR DELETE ON committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'organization_id', 'committee_ids');

-- notify triggers for gender_t fields
CREATE TRIGGER tr_log_gender AFTER INSERT OR UPDATE OR DELETE ON gender_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('gender');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gender_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for gender_t.organization_id
CREATE TRIGGER tr_log_gender_t_organization_id AFTER INSERT OR UPDATE OF organization_id OR DELETE ON gender_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'organization_id', 'gender_ids');

-- notify triggers for group_t fields
CREATE TRIGGER tr_log_group AFTER INSERT OR UPDATE OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('group');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON group_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- notify triggers for group.meeting_user_ids and meeting_user.group_ids
CREATE TRIGGER tr_log_nm_group_meeting_user_ids_meeting_user_t AFTER INSERT OR UPDATE OR DELETE ON nm_group_meeting_user_ids_meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','meeting_user_ids','meeting_user','meeting_user_id','group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_meeting_user_ids_meeting_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for group.meeting_mediafile_access_group_ids and meeting_mediafile.access_group_ids
CREATE TRIGGER tr_log_nm_group_mmagi_meeting_mediafile_t AFTER INSERT OR UPDATE OR DELETE ON nm_group_mmagi_meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','meeting_mediafile_access_group_ids','meeting_mediafile','meeting_mediafile_id','access_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_mmagi_meeting_mediafile_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for group.meeting_mediafile_inherited_access_group_ids and meeting_mediafile.inherited_access_group_ids
CREATE TRIGGER tr_log_nm_group_mmiagi_meeting_mediafile_t AFTER INSERT OR UPDATE OR DELETE ON nm_group_mmiagi_meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','meeting_mediafile_inherited_access_group_ids','meeting_mediafile','meeting_mediafile_id','inherited_access_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_mmiagi_meeting_mediafile_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for group.read_comment_section_ids and motion_comment_section.read_group_ids
CREATE TRIGGER tr_log_nm_group_read_comment_section_ids_motion_comment_6e42c77 AFTER INSERT OR UPDATE OR DELETE ON nm_group_read_comment_section_ids_motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','read_comment_section_ids','motion_comment_section','motion_comment_section_id','read_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_read_comment_section_ids_motion_comment_section_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for group.write_comment_section_ids and motion_comment_section.write_group_ids
CREATE TRIGGER tr_log_nm_group_write_comment_section_ids_motion_commentb627a2e AFTER INSERT OR UPDATE OR DELETE ON nm_group_write_comment_section_ids_motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','write_comment_section_ids','motion_comment_section','motion_comment_section_id','write_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_write_comment_section_ids_motion_comment_section_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for group.poll_ids and poll.entitled_group_ids
CREATE TRIGGER tr_log_nm_group_poll_ids_poll_t AFTER INSERT OR UPDATE OR DELETE ON nm_group_poll_ids_poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','poll_ids','poll','poll_id','entitled_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_poll_ids_poll_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
-- notify trigger for group_t.used_as_motion_poll_default_id
CREATE TRIGGER tr_log_group_t_used_as_motion_poll_default_id AFTER INSERT OR UPDATE OF used_as_motion_poll_default_id OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_motion_poll_default_id', 'motion_poll_default_group_ids');
-- notify trigger for group_t.used_as_assignment_poll_default_id
CREATE TRIGGER tr_log_group_t_used_as_assignment_poll_default_id AFTER INSERT OR UPDATE OF used_as_assignment_poll_default_id OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_assignment_poll_default_id', 'assignment_poll_default_group_ids');
-- notify trigger for group_t.used_as_topic_poll_default_id
CREATE TRIGGER tr_log_group_t_used_as_topic_poll_default_id AFTER INSERT OR UPDATE OF used_as_topic_poll_default_id OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_topic_poll_default_id', 'topic_poll_default_group_ids');
-- notify trigger for group_t.used_as_poll_default_id
CREATE TRIGGER tr_log_group_t_used_as_poll_default_id AFTER INSERT OR UPDATE OF used_as_poll_default_id OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_poll_default_id', 'poll_default_group_ids');
-- notify trigger for group_t.meeting_id
CREATE TRIGGER tr_log_group_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'group_ids');

-- notify triggers for history_entry_t fields
CREATE TRIGGER tr_log_history_entry AFTER INSERT OR UPDATE OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('history_entry');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON history_entry_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- notify trigger for history_entry_t.model_id_user_id
CREATE TRIGGER tr_log_user_model_id_user_id AFTER INSERT OR UPDATE OF model_id_user_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user','model_id_user_id','history_entry_ids');

-- notify trigger for history_entry_t.model_id_motion_id
CREATE TRIGGER tr_log_motion_model_id_motion_id AFTER INSERT OR UPDATE OF model_id_motion_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','model_id_motion_id','history_entry_ids');

-- notify trigger for history_entry_t.model_id_assignment_id
CREATE TRIGGER tr_log_assignment_model_id_assignment_id AFTER INSERT OR UPDATE OF model_id_assignment_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment','model_id_assignment_id','history_entry_ids');
-- notify trigger for history_entry_t.position_id
CREATE TRIGGER tr_log_history_entry_t_position_id AFTER INSERT OR UPDATE OF position_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('history_position', 'position_id', 'entry_ids');
-- notify trigger for history_entry_t.meeting_id
CREATE TRIGGER tr_log_history_entry_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'relevant_history_entry_ids');

-- notify triggers for history_position_t fields
CREATE TRIGGER tr_log_history_position AFTER INSERT OR UPDATE OR DELETE ON history_position_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('history_position');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON history_position_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for history_position_t.user_id
CREATE TRIGGER tr_log_history_position_t_user_id AFTER INSERT OR UPDATE OF user_id OR DELETE ON history_position_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user', 'user_id', 'history_position_ids');

-- notify triggers for import_preview_t fields
CREATE TRIGGER tr_log_import_preview AFTER INSERT OR UPDATE OR DELETE ON import_preview_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('import_preview');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON import_preview_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for list_of_speakers_t fields
CREATE TRIGGER tr_log_list_of_speakers AFTER INSERT OR UPDATE OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('list_of_speakers');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON list_of_speakers_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- notify trigger for list_of_speakers_t.content_object_id_motion_id
CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','list_of_speakers_id');

-- notify trigger for list_of_speakers_t.content_object_id_motion_block_id
CREATE TRIGGER tr_log_motion_block_content_object_id_motion_block_id AFTER INSERT OR UPDATE OF content_object_id_motion_block_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_block','content_object_id_motion_block_id','list_of_speakers_id');

-- notify trigger for list_of_speakers_t.content_object_id_assignment_id
CREATE TRIGGER tr_log_assignment_content_object_id_assignment_id AFTER INSERT OR UPDATE OF content_object_id_assignment_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment','content_object_id_assignment_id','list_of_speakers_id');

-- notify trigger for list_of_speakers_t.content_object_id_topic_id
CREATE TRIGGER tr_log_topic_content_object_id_topic_id AFTER INSERT OR UPDATE OF content_object_id_topic_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('topic','content_object_id_topic_id','list_of_speakers_id');

-- notify trigger for list_of_speakers_t.content_object_id_meeting_mediafile_id
CREATE TRIGGER tr_log_meeting_mediafile_content_object_id_meeting_mediafile_id AFTER INSERT OR UPDATE OF content_object_id_meeting_mediafile_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile','content_object_id_meeting_mediafile_id','list_of_speakers_id');
-- notify trigger for list_of_speakers_t.meeting_id
CREATE TRIGGER tr_log_list_of_speakers_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'list_of_speakers_ids');

-- notify triggers for mediafile_t fields
CREATE TRIGGER tr_log_mediafile AFTER INSERT OR UPDATE OR DELETE ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('mediafile');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON mediafile_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for mediafile_t.published_to_meetings_in_organization_id
CREATE TRIGGER tr_log_mediafile_t_published_to_meetings_in_organization_id AFTER INSERT OR UPDATE OF published_to_meetings_in_organization_id OR DELETE ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'published_to_meetings_in_organization_id', 'published_mediafile_ids');
-- notify trigger for mediafile_t.parent_id
CREATE TRIGGER tr_log_mediafile_t_parent_id AFTER INSERT OR UPDATE OF parent_id OR DELETE ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('mediafile', 'parent_id', 'child_ids');

-- notify trigger for mediafile_t.owner_id_meeting_id
CREATE TRIGGER tr_log_meeting_owner_id_meeting_id AFTER INSERT OR UPDATE OF owner_id_meeting_id OR DELETE ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting','owner_id_meeting_id','mediafile_ids');

-- notify trigger for mediafile_t.owner_id_organization_id
CREATE TRIGGER tr_log_organization_owner_id_organization_id AFTER INSERT OR UPDATE OF owner_id_organization_id OR DELETE ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization','owner_id_organization_id','mediafile_ids');

-- notify triggers for meeting_t fields
CREATE TRIGGER tr_log_meeting AFTER INSERT OR UPDATE OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('meeting');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON meeting_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for meeting_t.is_active_in_organization_id
CREATE TRIGGER tr_log_meeting_t_is_active_in_organization_id AFTER INSERT OR UPDATE OF is_active_in_organization_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'is_active_in_organization_id', 'active_meeting_ids');
-- notify trigger for meeting_t.is_archived_in_organization_id
CREATE TRIGGER tr_log_meeting_t_is_archived_in_organization_id AFTER INSERT OR UPDATE OF is_archived_in_organization_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'is_archived_in_organization_id', 'archived_meeting_ids');
-- notify trigger for meeting_t.template_for_organization_id
CREATE TRIGGER tr_log_meeting_t_template_for_organization_id AFTER INSERT OR UPDATE OF template_for_organization_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'template_for_organization_id', 'template_meeting_ids');
-- notify trigger for meeting_t.motions_default_workflow_id
CREATE TRIGGER tr_log_meeting_t_motions_default_workflow_id AFTER INSERT OR UPDATE OF motions_default_workflow_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_workflow', 'motions_default_workflow_id', 'default_workflow_meeting_id');
-- notify trigger for meeting_t.motions_default_amendment_workflow_id
CREATE TRIGGER tr_log_meeting_t_motions_default_amendment_workflow_id AFTER INSERT OR UPDATE OF motions_default_amendment_workflow_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_workflow', 'motions_default_amendment_workflow_id', 'default_amendment_workflow_meeting_id');
-- notify trigger for meeting_t.logo_projector_main_id
CREATE TRIGGER tr_log_meeting_t_logo_projector_main_id AFTER INSERT OR UPDATE OF logo_projector_main_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_projector_main_id', 'used_as_logo_projector_main_in_meeting_id');
-- notify trigger for meeting_t.logo_projector_header_id
CREATE TRIGGER tr_log_meeting_t_logo_projector_header_id AFTER INSERT OR UPDATE OF logo_projector_header_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_projector_header_id', 'used_as_logo_projector_header_in_meeting_id');
-- notify trigger for meeting_t.logo_web_header_id
CREATE TRIGGER tr_log_meeting_t_logo_web_header_id AFTER INSERT OR UPDATE OF logo_web_header_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_web_header_id', 'used_as_logo_web_header_in_meeting_id');
-- notify trigger for meeting_t.logo_pdf_header_l_id
CREATE TRIGGER tr_log_meeting_t_logo_pdf_header_l_id AFTER INSERT OR UPDATE OF logo_pdf_header_l_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_pdf_header_l_id', 'used_as_logo_pdf_header_l_in_meeting_id');
-- notify trigger for meeting_t.logo_pdf_header_r_id
CREATE TRIGGER tr_log_meeting_t_logo_pdf_header_r_id AFTER INSERT OR UPDATE OF logo_pdf_header_r_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_pdf_header_r_id', 'used_as_logo_pdf_header_r_in_meeting_id');
-- notify trigger for meeting_t.logo_pdf_footer_l_id
CREATE TRIGGER tr_log_meeting_t_logo_pdf_footer_l_id AFTER INSERT OR UPDATE OF logo_pdf_footer_l_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_pdf_footer_l_id', 'used_as_logo_pdf_footer_l_in_meeting_id');
-- notify trigger for meeting_t.logo_pdf_footer_r_id
CREATE TRIGGER tr_log_meeting_t_logo_pdf_footer_r_id AFTER INSERT OR UPDATE OF logo_pdf_footer_r_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_pdf_footer_r_id', 'used_as_logo_pdf_footer_r_in_meeting_id');
-- notify trigger for meeting_t.logo_pdf_ballot_paper_id
CREATE TRIGGER tr_log_meeting_t_logo_pdf_ballot_paper_id AFTER INSERT OR UPDATE OF logo_pdf_ballot_paper_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_pdf_ballot_paper_id', 'used_as_logo_pdf_ballot_paper_in_meeting_id');
-- notify trigger for meeting_t.font_regular_id
CREATE TRIGGER tr_log_meeting_t_font_regular_id AFTER INSERT OR UPDATE OF font_regular_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_regular_id', 'used_as_font_regular_in_meeting_id');
-- notify trigger for meeting_t.font_italic_id
CREATE TRIGGER tr_log_meeting_t_font_italic_id AFTER INSERT OR UPDATE OF font_italic_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_italic_id', 'used_as_font_italic_in_meeting_id');
-- notify trigger for meeting_t.font_bold_id
CREATE TRIGGER tr_log_meeting_t_font_bold_id AFTER INSERT OR UPDATE OF font_bold_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_bold_id', 'used_as_font_bold_in_meeting_id');
-- notify trigger for meeting_t.font_bold_italic_id
CREATE TRIGGER tr_log_meeting_t_font_bold_italic_id AFTER INSERT OR UPDATE OF font_bold_italic_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_bold_italic_id', 'used_as_font_bold_italic_in_meeting_id');
-- notify trigger for meeting_t.font_monospace_id
CREATE TRIGGER tr_log_meeting_t_font_monospace_id AFTER INSERT OR UPDATE OF font_monospace_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_monospace_id', 'used_as_font_monospace_in_meeting_id');
-- notify trigger for meeting_t.font_chyron_speaker_name_id
CREATE TRIGGER tr_log_meeting_t_font_chyron_speaker_name_id AFTER INSERT OR UPDATE OF font_chyron_speaker_name_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_chyron_speaker_name_id', 'used_as_font_chyron_speaker_name_in_meeting_id');
-- notify trigger for meeting_t.font_projector_h1_id
CREATE TRIGGER tr_log_meeting_t_font_projector_h1_id AFTER INSERT OR UPDATE OF font_projector_h1_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_projector_h1_id', 'used_as_font_projector_h1_in_meeting_id');
-- notify trigger for meeting_t.font_projector_h2_id
CREATE TRIGGER tr_log_meeting_t_font_projector_h2_id AFTER INSERT OR UPDATE OF font_projector_h2_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_projector_h2_id', 'used_as_font_projector_h2_in_meeting_id');
-- notify trigger for meeting_t.committee_id
CREATE TRIGGER tr_log_meeting_t_committee_id AFTER INSERT OR UPDATE OF committee_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee', 'committee_id', 'meeting_ids');

-- notify triggers for meeting.present_user_ids and user.is_present_in_meeting_ids
CREATE TRIGGER tr_log_nm_meeting_present_user_ids_user_t AFTER INSERT OR UPDATE OR DELETE ON nm_meeting_present_user_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting','meeting_id','present_user_ids','user','user_id','is_present_in_meeting_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_meeting_present_user_ids_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_i_meeting_user_ids_from_meeting_user_t BEFORE INSERT ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('meeting', 'meeting_id', '', 'user_ids', 'user_id', '');
CREATE TRIGGER tr_log_d_meeting_user_ids_from_meeting_user_t AFTER DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('meeting', 'meeting_id', '', 'user_ids', 'user_id', '');

-- notify trigger for meeting_t.reference_projector_id
CREATE TRIGGER tr_log_meeting_t_reference_projector_id AFTER INSERT OR UPDATE OF reference_projector_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector', 'reference_projector_id', 'used_as_reference_projector_meeting_id');
-- notify trigger for meeting_t.list_of_speakers_countdown_id
CREATE TRIGGER tr_log_meeting_t_list_of_speakers_countdown_id AFTER INSERT OR UPDATE OF list_of_speakers_countdown_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector_countdown', 'list_of_speakers_countdown_id', 'used_as_list_of_speakers_countdown_meeting_id');
-- notify trigger for meeting_t.poll_countdown_id
CREATE TRIGGER tr_log_meeting_t_poll_countdown_id AFTER INSERT OR UPDATE OF poll_countdown_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector_countdown', 'poll_countdown_id', 'used_as_poll_countdown_meeting_id');
-- notify trigger for meeting_t.default_group_id
CREATE TRIGGER tr_log_meeting_t_default_group_id AFTER INSERT OR UPDATE OF default_group_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group', 'default_group_id', 'default_group_for_meeting_id');
-- notify trigger for meeting_t.admin_group_id
CREATE TRIGGER tr_log_meeting_t_admin_group_id AFTER INSERT OR UPDATE OF admin_group_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group', 'admin_group_id', 'admin_group_for_meeting_id');
-- notify trigger for meeting_t.anonymous_group_id
CREATE TRIGGER tr_log_meeting_t_anonymous_group_id AFTER INSERT OR UPDATE OF anonymous_group_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group', 'anonymous_group_id', 'anonymous_group_for_meeting_id');

-- notify triggers for meeting_mediafile_t fields
CREATE TRIGGER tr_log_meeting_mediafile AFTER INSERT OR UPDATE OR DELETE ON meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('meeting_mediafile');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON meeting_mediafile_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for meeting_mediafile_t.mediafile_id
CREATE TRIGGER tr_log_meeting_mediafile_t_mediafile_id AFTER INSERT OR UPDATE OF mediafile_id OR DELETE ON meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('mediafile', 'mediafile_id', 'meeting_mediafile_ids');
-- notify trigger for meeting_mediafile_t.meeting_id
CREATE TRIGGER tr_log_meeting_mediafile_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'meeting_mediafile_ids');

-- notify triggers for meeting_mediafile.attachment_ids fields
CREATE TRIGGER tr_log_attachment_id_motion_id_gm_meeting_mediafile_atta25df47a AFTER INSERT OR UPDATE OF attachment_id_motion_id OR DELETE ON gm_meeting_mediafile_attachment_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile','meeting_mediafile_id','attachment_ids','motion','attachment_id_motion_id','attachment_meeting_mediafile_ids');

-- notify triggers for meeting_mediafile.attachment_ids fields
CREATE TRIGGER tr_log_attachment_id_topic_id_gm_meeting_mediafile_attac4e93703 AFTER INSERT OR UPDATE OF attachment_id_topic_id OR DELETE ON gm_meeting_mediafile_attachment_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile','meeting_mediafile_id','attachment_ids','topic','attachment_id_topic_id','attachment_meeting_mediafile_ids');

-- notify triggers for meeting_mediafile.attachment_ids fields
CREATE TRIGGER tr_log_attachment_id_assignment_id_gm_meeting_mediafile_2f214fd AFTER INSERT OR UPDATE OF attachment_id_assignment_id OR DELETE ON gm_meeting_mediafile_attachment_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile','meeting_mediafile_id','attachment_ids','assignment','attachment_id_assignment_id','attachment_meeting_mediafile_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gm_meeting_mediafile_attachment_ids_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for meeting_user_t fields
CREATE TRIGGER tr_log_meeting_user AFTER INSERT OR UPDATE OR DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('meeting_user');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON meeting_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for meeting_user_t.user_id
CREATE TRIGGER tr_log_meeting_user_t_user_id AFTER INSERT OR UPDATE OF user_id OR DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user', 'user_id', 'meeting_user_ids');
-- notify trigger for meeting_user_t.meeting_id
CREATE TRIGGER tr_log_meeting_user_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'meeting_user_ids');
-- notify trigger for meeting_user_t.vote_delegated_to_id
CREATE TRIGGER tr_log_meeting_user_t_vote_delegated_to_id AFTER INSERT OR UPDATE OF vote_delegated_to_id OR DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'vote_delegated_to_id', 'vote_delegations_from_ids');

-- notify triggers for meeting_user.structure_level_ids and structure_level.meeting_user_ids
CREATE TRIGGER tr_log_nm_meeting_user_structure_level_ids_structure_level_t AFTER INSERT OR UPDATE OR DELETE ON nm_meeting_user_structure_level_ids_structure_level_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user','meeting_user_id','structure_level_ids','structure_level','structure_level_id','meeting_user_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_meeting_user_structure_level_ids_structure_level_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for motion_t fields
CREATE TRIGGER tr_log_motion AFTER INSERT OR UPDATE OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_t.lead_motion_id
CREATE TRIGGER tr_log_motion_t_lead_motion_id AFTER INSERT OR UPDATE OF lead_motion_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'lead_motion_id', 'amendment_ids');
-- notify trigger for motion_t.sort_parent_id
CREATE TRIGGER tr_log_motion_t_sort_parent_id AFTER INSERT OR UPDATE OF sort_parent_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'sort_parent_id', 'sort_child_ids');
-- notify trigger for motion_t.origin_id
CREATE TRIGGER tr_log_motion_t_origin_id AFTER INSERT OR UPDATE OF origin_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'origin_id', 'derived_motion_ids');
-- notify trigger for motion_t.origin_meeting_id
CREATE TRIGGER tr_log_motion_t_origin_meeting_id AFTER INSERT OR UPDATE OF origin_meeting_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'origin_meeting_id', 'forwarded_motion_ids');

-- notify triggers for motion.all_derived_motion_ids and motion.all_origin_ids
CREATE TRIGGER tr_log_nm_motion_all_derived_motion_ids_motion_t AFTER INSERT OR UPDATE OR DELETE ON nm_motion_all_derived_motion_ids_motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','all_origin_id','all_derived_motion_ids','motion','all_derived_motion_id','all_origin_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_motion_all_derived_motion_ids_motion_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for motion.identical_motion_ids and motion.identical_motion_ids
CREATE TRIGGER tr_log_nm_motion_identical_motion_ids_motion_t AFTER INSERT OR UPDATE OR DELETE ON nm_motion_identical_motion_ids_motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','identical_motion_id_1','identical_motion_ids','motion','identical_motion_id_2','identical_motion_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_motion_identical_motion_ids_motion_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
-- notify trigger for motion_t.state_id
CREATE TRIGGER tr_log_motion_t_state_id AFTER INSERT OR UPDATE OF state_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_state', 'state_id', 'motion_ids');
-- notify trigger for motion_t.recommendation_id
CREATE TRIGGER tr_log_motion_t_recommendation_id AFTER INSERT OR UPDATE OF recommendation_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_state', 'recommendation_id', 'motion_recommendation_ids');

-- notify triggers for motion.state_extension_reference_ids fields
CREATE TRIGGER tr_log_state_extension_reference_id_motion_id_gm_motion_2720cdc AFTER INSERT OR UPDATE OF state_extension_reference_id_motion_id OR DELETE ON gm_motion_state_extension_reference_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','motion_id','state_extension_reference_ids','motion','state_extension_reference_id_motion_id','referenced_in_motion_state_extension_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gm_motion_state_extension_reference_ids_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify triggers for motion.recommendation_extension_reference_ids fields
CREATE TRIGGER tr_log_recommendation_extension_reference_id_motion_id_g047b2db AFTER INSERT OR UPDATE OF recommendation_extension_reference_id_motion_id OR DELETE ON gm_motion_recommendation_extension_reference_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','motion_id','recommendation_extension_reference_ids','motion','recommendation_extension_reference_id_motion_id','referenced_in_motion_recommendation_extension_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gm_motion_recommendation_extension_reference_ids_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
-- notify trigger for motion_t.category_id
CREATE TRIGGER tr_log_motion_t_category_id AFTER INSERT OR UPDATE OF category_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_category', 'category_id', 'motion_ids');
-- notify trigger for motion_t.block_id
CREATE TRIGGER tr_log_motion_t_block_id AFTER INSERT OR UPDATE OF block_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_block', 'block_id', 'motion_ids');
-- notify trigger for motion_t.meeting_id
CREATE TRIGGER tr_log_motion_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_ids');

-- notify triggers for motion_block_t fields
CREATE TRIGGER tr_log_motion_block AFTER INSERT OR UPDATE OR DELETE ON motion_block_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_block');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_block_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_block_t.meeting_id
CREATE TRIGGER tr_log_motion_block_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_block_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_block_ids');

-- notify triggers for motion_category_t fields
CREATE TRIGGER tr_log_motion_category AFTER INSERT OR UPDATE OR DELETE ON motion_category_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_category');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_category_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_category_t.parent_id
CREATE TRIGGER tr_log_motion_category_t_parent_id AFTER INSERT OR UPDATE OF parent_id OR DELETE ON motion_category_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_category', 'parent_id', 'child_ids');
-- notify trigger for motion_category_t.meeting_id
CREATE TRIGGER tr_log_motion_category_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_category_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_category_ids');

-- notify triggers for motion_change_recommendation_t fields
CREATE TRIGGER tr_log_motion_change_recommendation AFTER INSERT OR UPDATE OR DELETE ON motion_change_recommendation_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_change_recommendation');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_change_recommendation_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_change_recommendation_t.motion_id
CREATE TRIGGER tr_log_motion_change_recommendation_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_change_recommendation_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'change_recommendation_ids');
-- notify trigger for motion_change_recommendation_t.meeting_id
CREATE TRIGGER tr_log_motion_change_recommendation_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_change_recommendation_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_change_recommendation_ids');

-- notify triggers for motion_comment_t fields
CREATE TRIGGER tr_log_motion_comment AFTER INSERT OR UPDATE OR DELETE ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_comment');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_comment_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_comment_t.motion_id
CREATE TRIGGER tr_log_motion_comment_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'comment_ids');
-- notify trigger for motion_comment_t.section_id
CREATE TRIGGER tr_log_motion_comment_t_section_id AFTER INSERT OR UPDATE OF section_id OR DELETE ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_comment_section', 'section_id', 'comment_ids');
-- notify trigger for motion_comment_t.meeting_id
CREATE TRIGGER tr_log_motion_comment_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_comment_ids');

-- notify triggers for motion_comment_section_t fields
CREATE TRIGGER tr_log_motion_comment_section AFTER INSERT OR UPDATE OR DELETE ON motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_comment_section');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_comment_section_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_comment_section_t.meeting_id
CREATE TRIGGER tr_log_motion_comment_section_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_comment_section_ids');

-- notify triggers for motion_editor_t fields
CREATE TRIGGER tr_log_motion_editor AFTER INSERT OR UPDATE OR DELETE ON motion_editor_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_editor');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_editor_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_editor_t.meeting_user_id
CREATE TRIGGER tr_log_motion_editor_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON motion_editor_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'motion_editor_ids');
-- notify trigger for motion_editor_t.motion_id
CREATE TRIGGER tr_log_motion_editor_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_editor_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'editor_ids');
-- notify trigger for motion_editor_t.meeting_id
CREATE TRIGGER tr_log_motion_editor_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_editor_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_editor_ids');

-- notify triggers for motion_state_t fields
CREATE TRIGGER tr_log_motion_state AFTER INSERT OR UPDATE OR DELETE ON motion_state_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_state');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_state_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_state_t.submitter_withdraw_state_id
CREATE TRIGGER tr_log_motion_state_t_submitter_withdraw_state_id AFTER INSERT OR UPDATE OF submitter_withdraw_state_id OR DELETE ON motion_state_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_state', 'submitter_withdraw_state_id', 'submitter_withdraw_back_ids');

-- notify triggers for motion_state.next_state_ids and motion_state.previous_state_ids
CREATE TRIGGER tr_log_nm_motion_state_next_state_ids_motion_state_t AFTER INSERT OR UPDATE OR DELETE ON nm_motion_state_next_state_ids_motion_state_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_state','previous_state_id','next_state_ids','motion_state','next_state_id','previous_state_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_motion_state_next_state_ids_motion_state_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
-- notify trigger for motion_state_t.workflow_id
CREATE TRIGGER tr_log_motion_state_t_workflow_id AFTER INSERT OR UPDATE OF workflow_id OR DELETE ON motion_state_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_workflow', 'workflow_id', 'state_ids');
-- notify trigger for motion_state_t.meeting_id
CREATE TRIGGER tr_log_motion_state_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_state_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_state_ids');

-- notify triggers for motion_submitter_t fields
CREATE TRIGGER tr_log_motion_submitter AFTER INSERT OR UPDATE OR DELETE ON motion_submitter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_submitter');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_submitter_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_submitter_t.meeting_user_id
CREATE TRIGGER tr_log_motion_submitter_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON motion_submitter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'motion_submitter_ids');
-- notify trigger for motion_submitter_t.motion_id
CREATE TRIGGER tr_log_motion_submitter_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_submitter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'submitter_ids');
-- notify trigger for motion_submitter_t.meeting_id
CREATE TRIGGER tr_log_motion_submitter_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_submitter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_submitter_ids');

-- notify triggers for motion_supporter_t fields
CREATE TRIGGER tr_log_motion_supporter AFTER INSERT OR UPDATE OR DELETE ON motion_supporter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_supporter');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_supporter_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_supporter_t.meeting_user_id
CREATE TRIGGER tr_log_motion_supporter_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON motion_supporter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'motion_supporter_ids');
-- notify trigger for motion_supporter_t.motion_id
CREATE TRIGGER tr_log_motion_supporter_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_supporter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'supporter_ids');
-- notify trigger for motion_supporter_t.meeting_id
CREATE TRIGGER tr_log_motion_supporter_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_supporter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_supporter_ids');

-- notify triggers for motion_workflow_t fields
CREATE TRIGGER tr_log_motion_workflow AFTER INSERT OR UPDATE OR DELETE ON motion_workflow_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_workflow');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_workflow_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_workflow_t.first_state_id
CREATE TRIGGER tr_log_motion_workflow_t_first_state_id AFTER INSERT OR UPDATE OF first_state_id OR DELETE ON motion_workflow_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_state', 'first_state_id', 'first_state_of_workflow_id');
-- notify trigger for motion_workflow_t.meeting_id
CREATE TRIGGER tr_log_motion_workflow_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_workflow_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_workflow_ids');

-- notify triggers for motion_working_group_speaker_t fields
CREATE TRIGGER tr_log_motion_working_group_speaker AFTER INSERT OR UPDATE OR DELETE ON motion_working_group_speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_working_group_speaker');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_working_group_speaker_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for motion_working_group_speaker_t.meeting_user_id
CREATE TRIGGER tr_log_motion_working_group_speaker_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON motion_working_group_speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'motion_working_group_speaker_ids');
-- notify trigger for motion_working_group_speaker_t.motion_id
CREATE TRIGGER tr_log_motion_working_group_speaker_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_working_group_speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'working_group_speaker_ids');
-- notify trigger for motion_working_group_speaker_t.meeting_id
CREATE TRIGGER tr_log_motion_working_group_speaker_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_working_group_speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_working_group_speaker_ids');

-- notify triggers for option_t fields
CREATE TRIGGER tr_log_option AFTER INSERT OR UPDATE OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('option');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON option_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for option_t.poll_id
CREATE TRIGGER tr_log_option_t_poll_id AFTER INSERT OR UPDATE OF poll_id OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll', 'poll_id', 'option_ids');

-- notify trigger for option_t.content_object_id_motion_id
CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','option_ids');

-- notify trigger for option_t.content_object_id_user_id
CREATE TRIGGER tr_log_user_content_object_id_user_id AFTER INSERT OR UPDATE OF content_object_id_user_id OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user','content_object_id_user_id','option_ids');

-- notify trigger for option_t.content_object_id_poll_candidate_list_id
CREATE TRIGGER tr_log_poll_candidate_list_content_object_id_poll_candidc235209 AFTER INSERT OR UPDATE OF content_object_id_poll_candidate_list_id OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll_candidate_list','content_object_id_poll_candidate_list_id','option_id');
-- notify trigger for option_t.meeting_id
CREATE TRIGGER tr_log_option_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'option_ids');

-- notify triggers for organization_t fields
CREATE TRIGGER tr_log_organization AFTER INSERT OR UPDATE OR DELETE ON organization_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('organization');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON organization_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for organization_t.theme_id
CREATE TRIGGER tr_log_organization_t_theme_id AFTER INSERT OR UPDATE OF theme_id OR DELETE ON organization_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('theme', 'theme_id', 'theme_for_organization_id');

-- notify triggers for organization_tag_t fields
CREATE TRIGGER tr_log_organization_tag AFTER INSERT OR UPDATE OR DELETE ON organization_tag_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('organization_tag');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON organization_tag_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- notify triggers for organization_tag.tagged_ids fields
CREATE TRIGGER tr_log_tagged_id_committee_id_gm_organization_tag_tagged_ids_t AFTER INSERT OR UPDATE OF tagged_id_committee_id OR DELETE ON gm_organization_tag_tagged_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization_tag','organization_tag_id','tagged_ids','committee','tagged_id_committee_id','organization_tag_ids');

-- notify triggers for organization_tag.tagged_ids fields
CREATE TRIGGER tr_log_tagged_id_meeting_id_gm_organization_tag_tagged_ids_t AFTER INSERT OR UPDATE OF tagged_id_meeting_id OR DELETE ON gm_organization_tag_tagged_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization_tag','organization_tag_id','tagged_ids','meeting','tagged_id_meeting_id','organization_tag_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gm_organization_tag_tagged_ids_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
-- notify trigger for organization_tag_t.organization_id
CREATE TRIGGER tr_log_organization_tag_t_organization_id AFTER INSERT OR UPDATE OF organization_id OR DELETE ON organization_tag_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'organization_id', 'organization_tag_ids');

-- notify triggers for personal_note_t fields
CREATE TRIGGER tr_log_personal_note AFTER INSERT OR UPDATE OR DELETE ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('personal_note');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON personal_note_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for personal_note_t.meeting_user_id
CREATE TRIGGER tr_log_personal_note_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'personal_note_ids');

-- notify trigger for personal_note_t.content_object_id_motion_id
CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','personal_note_ids');
-- notify trigger for personal_note_t.meeting_id
CREATE TRIGGER tr_log_personal_note_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'personal_note_ids');

-- notify triggers for point_of_order_category_t fields
CREATE TRIGGER tr_log_point_of_order_category AFTER INSERT OR UPDATE OR DELETE ON point_of_order_category_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('point_of_order_category');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON point_of_order_category_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for point_of_order_category_t.meeting_id
CREATE TRIGGER tr_log_point_of_order_category_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON point_of_order_category_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'point_of_order_category_ids');

-- notify triggers for poll_t fields
CREATE TRIGGER tr_log_poll AFTER INSERT OR UPDATE OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- notify trigger for poll_t.content_object_id_motion_id
CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','poll_ids');

-- notify trigger for poll_t.content_object_id_assignment_id
CREATE TRIGGER tr_log_assignment_content_object_id_assignment_id AFTER INSERT OR UPDATE OF content_object_id_assignment_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment','content_object_id_assignment_id','poll_ids');

-- notify trigger for poll_t.content_object_id_topic_id
CREATE TRIGGER tr_log_topic_content_object_id_topic_id AFTER INSERT OR UPDATE OF content_object_id_topic_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('topic','content_object_id_topic_id','poll_ids');
-- notify trigger for poll_t.global_option_id
CREATE TRIGGER tr_log_poll_t_global_option_id AFTER INSERT OR UPDATE OF global_option_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('option', 'global_option_id', 'used_as_global_option_in_poll_id');

-- notify triggers for poll.voted_ids and user.poll_voted_ids
CREATE TRIGGER tr_log_nm_poll_voted_ids_user_t AFTER INSERT OR UPDATE OR DELETE ON nm_poll_voted_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll','poll_id','voted_ids','user','user_id','poll_voted_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_poll_voted_ids_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
-- notify trigger for poll_t.meeting_id
CREATE TRIGGER tr_log_poll_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'poll_ids');

-- notify triggers for poll_candidate_t fields
CREATE TRIGGER tr_log_poll_candidate AFTER INSERT OR UPDATE OR DELETE ON poll_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_candidate');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_candidate_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for poll_candidate_t.poll_candidate_list_id
CREATE TRIGGER tr_log_poll_candidate_t_poll_candidate_list_id AFTER INSERT OR UPDATE OF poll_candidate_list_id OR DELETE ON poll_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll_candidate_list', 'poll_candidate_list_id', 'poll_candidate_ids');
-- notify trigger for poll_candidate_t.user_id
CREATE TRIGGER tr_log_poll_candidate_t_user_id AFTER INSERT OR UPDATE OF user_id OR DELETE ON poll_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user', 'user_id', 'poll_candidate_ids');
-- notify trigger for poll_candidate_t.meeting_id
CREATE TRIGGER tr_log_poll_candidate_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON poll_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'poll_candidate_ids');

-- notify triggers for poll_candidate_list_t fields
CREATE TRIGGER tr_log_poll_candidate_list AFTER INSERT OR UPDATE OR DELETE ON poll_candidate_list_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_candidate_list');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_candidate_list_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for poll_candidate_list_t.meeting_id
CREATE TRIGGER tr_log_poll_candidate_list_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON poll_candidate_list_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'poll_candidate_list_ids');

-- notify triggers for projection_t fields
CREATE TRIGGER tr_log_projection AFTER INSERT OR UPDATE OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('projection');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON projection_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for projection_t.current_projector_id
CREATE TRIGGER tr_log_projection_t_current_projector_id AFTER INSERT OR UPDATE OF current_projector_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector', 'current_projector_id', 'current_projection_ids');
-- notify trigger for projection_t.preview_projector_id
CREATE TRIGGER tr_log_projection_t_preview_projector_id AFTER INSERT OR UPDATE OF preview_projector_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector', 'preview_projector_id', 'preview_projection_ids');
-- notify trigger for projection_t.history_projector_id
CREATE TRIGGER tr_log_projection_t_history_projector_id AFTER INSERT OR UPDATE OF history_projector_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector', 'history_projector_id', 'history_projection_ids');

-- notify trigger for projection_t.content_object_id_meeting_id
CREATE TRIGGER tr_log_meeting_content_object_id_meeting_id AFTER INSERT OR UPDATE OF content_object_id_meeting_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting','content_object_id_meeting_id','projection_ids');

-- notify trigger for projection_t.content_object_id_motion_id
CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','projection_ids');

-- notify trigger for projection_t.content_object_id_meeting_mediafile_id
CREATE TRIGGER tr_log_meeting_mediafile_content_object_id_meeting_mediafile_id AFTER INSERT OR UPDATE OF content_object_id_meeting_mediafile_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile','content_object_id_meeting_mediafile_id','projection_ids');

-- notify trigger for projection_t.content_object_id_list_of_speakers_id
CREATE TRIGGER tr_log_list_of_speakers_content_object_id_list_of_speakers_id AFTER INSERT OR UPDATE OF content_object_id_list_of_speakers_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('list_of_speakers','content_object_id_list_of_speakers_id','projection_ids');

-- notify trigger for projection_t.content_object_id_motion_block_id
CREATE TRIGGER tr_log_motion_block_content_object_id_motion_block_id AFTER INSERT OR UPDATE OF content_object_id_motion_block_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_block','content_object_id_motion_block_id','projection_ids');

-- notify trigger for projection_t.content_object_id_assignment_id
CREATE TRIGGER tr_log_assignment_content_object_id_assignment_id AFTER INSERT OR UPDATE OF content_object_id_assignment_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment','content_object_id_assignment_id','projection_ids');

-- notify trigger for projection_t.content_object_id_agenda_item_id
CREATE TRIGGER tr_log_agenda_item_content_object_id_agenda_item_id AFTER INSERT OR UPDATE OF content_object_id_agenda_item_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('agenda_item','content_object_id_agenda_item_id','projection_ids');

-- notify trigger for projection_t.content_object_id_topic_id
CREATE TRIGGER tr_log_topic_content_object_id_topic_id AFTER INSERT OR UPDATE OF content_object_id_topic_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('topic','content_object_id_topic_id','projection_ids');

-- notify trigger for projection_t.content_object_id_poll_id
CREATE TRIGGER tr_log_poll_content_object_id_poll_id AFTER INSERT OR UPDATE OF content_object_id_poll_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll','content_object_id_poll_id','projection_ids');

-- notify trigger for projection_t.content_object_id_projector_message_id
CREATE TRIGGER tr_log_projector_message_content_object_id_projector_message_id AFTER INSERT OR UPDATE OF content_object_id_projector_message_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector_message','content_object_id_projector_message_id','projection_ids');

-- notify trigger for projection_t.content_object_id_projector_countdown_id
CREATE TRIGGER tr_log_projector_countdown_content_object_id_projector_c35fae82 AFTER INSERT OR UPDATE OF content_object_id_projector_countdown_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector_countdown','content_object_id_projector_countdown_id','projection_ids');
-- notify trigger for projection_t.meeting_id
CREATE TRIGGER tr_log_projection_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'all_projection_ids');

-- notify triggers for projector_t fields
CREATE TRIGGER tr_log_projector AFTER INSERT OR UPDATE OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('projector');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON projector_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for projector_t.used_as_default_projector_for_agenda_item_list_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_agenda_a3418fd AFTER INSERT OR UPDATE OF used_as_default_projector_for_agenda_item_list_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_agenda_item_list_in_meeting_id', 'default_projector_agenda_item_list_ids');
-- notify trigger for projector_t.used_as_default_projector_for_topic_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_topic_iccc9ca7 AFTER INSERT OR UPDATE OF used_as_default_projector_for_topic_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_topic_in_meeting_id', 'default_projector_topic_ids');
-- notify trigger for projector_t.used_as_default_projector_for_list_of_speakers_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_list_offcea2e3 AFTER INSERT OR UPDATE OF used_as_default_projector_for_list_of_speakers_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_list_of_speakers_in_meeting_id', 'default_projector_list_of_speakers_ids');
-- notify trigger for projector_t.used_as_default_projector_for_current_los_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_current897012e AFTER INSERT OR UPDATE OF used_as_default_projector_for_current_los_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_current_los_in_meeting_id', 'default_projector_current_los_ids');
-- notify trigger for projector_t.used_as_default_projector_for_motion_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_motion_9cf3618 AFTER INSERT OR UPDATE OF used_as_default_projector_for_motion_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_motion_in_meeting_id', 'default_projector_motion_ids');
-- notify trigger for projector_t.used_as_default_projector_for_amendment_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_amendme4ebfd41 AFTER INSERT OR UPDATE OF used_as_default_projector_for_amendment_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_amendment_in_meeting_id', 'default_projector_amendment_ids');
-- notify trigger for projector_t.used_as_default_projector_for_motion_block_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_motion_1b9d3a7 AFTER INSERT OR UPDATE OF used_as_default_projector_for_motion_block_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_motion_block_in_meeting_id', 'default_projector_motion_block_ids');
-- notify trigger for projector_t.used_as_default_projector_for_assignment_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_assignm9e3b0b3 AFTER INSERT OR UPDATE OF used_as_default_projector_for_assignment_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_assignment_in_meeting_id', 'default_projector_assignment_ids');
-- notify trigger for projector_t.used_as_default_projector_for_mediafile_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_mediafib4f0da8 AFTER INSERT OR UPDATE OF used_as_default_projector_for_mediafile_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_mediafile_in_meeting_id', 'default_projector_mediafile_ids');
-- notify trigger for projector_t.used_as_default_projector_for_message_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_message28c0ca6 AFTER INSERT OR UPDATE OF used_as_default_projector_for_message_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_message_in_meeting_id', 'default_projector_message_ids');
-- notify trigger for projector_t.used_as_default_projector_for_countdown_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_countdoe67f735 AFTER INSERT OR UPDATE OF used_as_default_projector_for_countdown_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_countdown_in_meeting_id', 'default_projector_countdown_ids');
-- notify trigger for projector_t.used_as_default_projector_for_assignment_poll_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_assignmf3a7b0f AFTER INSERT OR UPDATE OF used_as_default_projector_for_assignment_poll_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_assignment_poll_in_meeting_id', 'default_projector_assignment_poll_ids');
-- notify trigger for projector_t.used_as_default_projector_for_motion_poll_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_motion_c48d3bb AFTER INSERT OR UPDATE OF used_as_default_projector_for_motion_poll_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_motion_poll_in_meeting_id', 'default_projector_motion_poll_ids');
-- notify trigger for projector_t.used_as_default_projector_for_poll_in_meeting_id
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_poll_inf6f7d63 AFTER INSERT OR UPDATE OF used_as_default_projector_for_poll_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_poll_in_meeting_id', 'default_projector_poll_ids');
-- notify trigger for projector_t.meeting_id
CREATE TRIGGER tr_log_projector_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'projector_ids');

-- notify triggers for projector_countdown_t fields
CREATE TRIGGER tr_log_projector_countdown AFTER INSERT OR UPDATE OR DELETE ON projector_countdown_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('projector_countdown');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON projector_countdown_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for projector_countdown_t.meeting_id
CREATE TRIGGER tr_log_projector_countdown_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON projector_countdown_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'projector_countdown_ids');

-- notify triggers for projector_message_t fields
CREATE TRIGGER tr_log_projector_message AFTER INSERT OR UPDATE OR DELETE ON projector_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('projector_message');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON projector_message_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for projector_message_t.meeting_id
CREATE TRIGGER tr_log_projector_message_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON projector_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'projector_message_ids');

-- notify triggers for speaker_t fields
CREATE TRIGGER tr_log_speaker AFTER INSERT OR UPDATE OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('speaker');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON speaker_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for speaker_t.list_of_speakers_id
CREATE TRIGGER tr_log_speaker_t_list_of_speakers_id AFTER INSERT OR UPDATE OF list_of_speakers_id OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('list_of_speakers', 'list_of_speakers_id', 'speaker_ids');
-- notify trigger for speaker_t.structure_level_list_of_speakers_id
CREATE TRIGGER tr_log_speaker_t_structure_level_list_of_speakers_id AFTER INSERT OR UPDATE OF structure_level_list_of_speakers_id OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('structure_level_list_of_speakers', 'structure_level_list_of_speakers_id', 'speaker_ids');
-- notify trigger for speaker_t.meeting_user_id
CREATE TRIGGER tr_log_speaker_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'speaker_ids');
-- notify trigger for speaker_t.point_of_order_category_id
CREATE TRIGGER tr_log_speaker_t_point_of_order_category_id AFTER INSERT OR UPDATE OF point_of_order_category_id OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('point_of_order_category', 'point_of_order_category_id', 'speaker_ids');
-- notify trigger for speaker_t.meeting_id
CREATE TRIGGER tr_log_speaker_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'speaker_ids');

-- notify triggers for structure_level_t fields
CREATE TRIGGER tr_log_structure_level AFTER INSERT OR UPDATE OR DELETE ON structure_level_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('structure_level');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON structure_level_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for structure_level_t.meeting_id
CREATE TRIGGER tr_log_structure_level_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON structure_level_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'structure_level_ids');

-- notify triggers for structure_level_list_of_speakers_t fields
CREATE TRIGGER tr_log_structure_level_list_of_speakers AFTER INSERT OR UPDATE OR DELETE ON structure_level_list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('structure_level_list_of_speakers');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON structure_level_list_of_speakers_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for structure_level_list_of_speakers_t.structure_level_id
CREATE TRIGGER tr_log_structure_level_list_of_speakers_t_structure_level_id AFTER INSERT OR UPDATE OF structure_level_id OR DELETE ON structure_level_list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('structure_level', 'structure_level_id', 'structure_level_list_of_speakers_ids');
-- notify trigger for structure_level_list_of_speakers_t.list_of_speakers_id
CREATE TRIGGER tr_log_structure_level_list_of_speakers_t_list_of_speakers_id AFTER INSERT OR UPDATE OF list_of_speakers_id OR DELETE ON structure_level_list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('list_of_speakers', 'list_of_speakers_id', 'structure_level_list_of_speakers_ids');
-- notify trigger for structure_level_list_of_speakers_t.meeting_id
CREATE TRIGGER tr_log_structure_level_list_of_speakers_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON structure_level_list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'structure_level_list_of_speakers_ids');

-- notify triggers for tag_t fields
CREATE TRIGGER tr_log_tag AFTER INSERT OR UPDATE OR DELETE ON tag_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('tag');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON tag_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


-- notify triggers for tag.tagged_ids fields
CREATE TRIGGER tr_log_tagged_id_agenda_item_id_gm_tag_tagged_ids_t AFTER INSERT OR UPDATE OF tagged_id_agenda_item_id OR DELETE ON gm_tag_tagged_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('tag','tag_id','tagged_ids','agenda_item','tagged_id_agenda_item_id','tag_ids');

-- notify triggers for tag.tagged_ids fields
CREATE TRIGGER tr_log_tagged_id_assignment_id_gm_tag_tagged_ids_t AFTER INSERT OR UPDATE OF tagged_id_assignment_id OR DELETE ON gm_tag_tagged_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('tag','tag_id','tagged_ids','assignment','tagged_id_assignment_id','tag_ids');

-- notify triggers for tag.tagged_ids fields
CREATE TRIGGER tr_log_tagged_id_motion_id_gm_tag_tagged_ids_t AFTER INSERT OR UPDATE OF tagged_id_motion_id OR DELETE ON gm_tag_tagged_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('tag','tag_id','tagged_ids','motion','tagged_id_motion_id','tag_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gm_tag_tagged_ids_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
-- notify trigger for tag_t.meeting_id
CREATE TRIGGER tr_log_tag_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON tag_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'tag_ids');

-- notify triggers for theme_t fields
CREATE TRIGGER tr_log_theme AFTER INSERT OR UPDATE OR DELETE ON theme_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('theme');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON theme_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for theme_t.organization_id
CREATE TRIGGER tr_log_theme_t_organization_id AFTER INSERT OR UPDATE OF organization_id OR DELETE ON theme_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'organization_id', 'theme_ids');

-- notify triggers for topic_t fields
CREATE TRIGGER tr_log_topic AFTER INSERT OR UPDATE OR DELETE ON topic_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('topic');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON topic_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for topic_t.meeting_id
CREATE TRIGGER tr_log_topic_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON topic_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'topic_ids');

-- notify triggers for user_t fields
CREATE TRIGGER tr_log_user AFTER INSERT OR UPDATE OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('user');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for user_t.gender_id
CREATE TRIGGER tr_log_user_t_gender_id AFTER INSERT OR UPDATE OF gender_id OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('gender', 'gender_id', 'user_ids');

CREATE TRIGGER tr_log_i_user_committee_ids_from_meeting_user_t BEFORE INSERT ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('user', 'user_id', '', 'committee_ids', '', 'SELECT committee_id AS id FROM meeting_t WHERE id = ($1).meeting_id');
CREATE TRIGGER tr_log_d_user_committee_ids_from_meeting_user_t AFTER DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('user', 'user_id', '', 'committee_ids', '', 'SELECT committee_id AS id FROM meeting_t WHERE id = ($1).meeting_id');
CREATE TRIGGER tr_log_i_user_committee_ids_from_meeting_t BEFORE INSERT ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('user', '', 'SELECT user_id AS id FROM meeting_user_t WHERE meeting_id = ($1).id', 'committee_ids', 'committee_id', '');
CREATE TRIGGER tr_log_d_user_committee_ids_from_meeting_t AFTER DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('user', '', 'SELECT user_id AS id FROM meeting_user_t WHERE meeting_id = ($1).id', 'committee_ids', 'committee_id', '');
CREATE TRIGGER tr_log_i_user_committee_ids_from_nm_committee_manager_id3c34791 BEFORE INSERT ON nm_committee_manager_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('user', 'user_id', '', 'committee_ids', 'committee_id', '');
CREATE TRIGGER tr_log_d_user_committee_ids_from_nm_committee_manager_id8cfd923 AFTER DELETE ON nm_committee_manager_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('user', 'user_id', '', 'committee_ids', 'committee_id', '');
CREATE TRIGGER tr_log_iu_user_committee_ids_from_user_t BEFORE INSERT OR UPDATE OF home_committee_id ON user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('user', 'id', '', 'committee_ids', 'home_committee_id', '');
CREATE TRIGGER tr_log_ud_user_committee_ids_from_user_t AFTER UPDATE OF home_committee_id OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('user', 'id', '', 'committee_ids', 'home_committee_id', '');

-- notify trigger for user_t.home_committee_id
CREATE TRIGGER tr_log_user_t_home_committee_id AFTER INSERT OR UPDATE OF home_committee_id OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee', 'home_committee_id', 'native_user_ids');

CREATE TRIGGER tr_log_i_user_meeting_ids_from_meeting_user_t BEFORE INSERT ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('user', 'user_id', '', 'meeting_ids', 'meeting_id', '');
CREATE TRIGGER tr_log_d_user_meeting_ids_from_meeting_user_t AFTER DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('user', 'user_id', '', 'meeting_ids', 'meeting_id', '');

-- notify trigger for user_t.organization_id
CREATE TRIGGER tr_log_user_t_organization_id AFTER INSERT OR UPDATE OF organization_id OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'organization_id', 'user_ids');

-- notify triggers for vote_t fields
CREATE TRIGGER tr_log_vote AFTER INSERT OR UPDATE OR DELETE ON vote_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('vote');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON vote_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

-- notify trigger for vote_t.option_id
CREATE TRIGGER tr_log_vote_t_option_id AFTER INSERT OR UPDATE OF option_id OR DELETE ON vote_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('option', 'option_id', 'vote_ids');
-- notify trigger for vote_t.user_id
CREATE TRIGGER tr_log_vote_t_user_id AFTER INSERT OR UPDATE OF user_id OR DELETE ON vote_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user', 'user_id', 'vote_ids');
-- notify trigger for vote_t.delegated_user_id
CREATE TRIGGER tr_log_vote_t_delegated_user_id AFTER INSERT OR UPDATE OF delegated_user_id OR DELETE ON vote_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user', 'delegated_user_id', 'delegated_vote_ids');
-- notify trigger for vote_t.meeting_id
CREATE TRIGGER tr_log_vote_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON vote_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'vote_ids');



-- Create triggers checking equal_fields settings in relations

CREATE CONSTRAINT TRIGGER equal_meeting_id_on_agenda_item_t_content_object_id_motion_id AFTER INSERT ON agenda_item_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('agenda_item', 'motion', 'content_object_id_motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_agenda_item_id AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('agenda_item', 'motion', 'content_object_id_motion_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_agenda_item_t_content_object_id_moti4dd35ce AFTER INSERT ON agenda_item_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('agenda_item', 'motion_block', 'content_object_id_motion_block_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_block_t_agenda_item_id AFTER INSERT ON motion_block_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('agenda_item', 'motion_block', 'content_object_id_motion_block_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_agenda_item_t_content_object_id_assieb89ee8 AFTER INSERT ON agenda_item_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('agenda_item', 'assignment', 'content_object_id_assignment_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_assignment_t_agenda_item_id AFTER INSERT ON assignment_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('agenda_item', 'assignment', 'content_object_id_assignment_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_agenda_item_t_content_object_id_topic_id AFTER INSERT ON agenda_item_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('agenda_item', 'topic', 'content_object_id_topic_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_topic_t_agenda_item_id AFTER INSERT ON topic_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('agenda_item', 'topic', 'content_object_id_topic_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_agenda_item_t_parent_id AFTER INSERT OR UPDATE OF parent_id ON agenda_item_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('agenda_item', 'agenda_item', 'parent_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_agenda_item_t_child_ids AFTER INSERT ON agenda_item_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('agenda_item', 'agenda_item', 'parent_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_assignment_candidate_t_assignment_id AFTER INSERT ON assignment_candidate_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('assignment_candidate', 'assignment', 'assignment_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_assignment_t_candidate_ids AFTER INSERT ON assignment_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('assignment_candidate', 'assignment', 'assignment_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_assignment_candidate_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id ON assignment_candidate_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('assignment_candidate', 'meeting_user', 'meeting_user_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_assignment_candidate_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('assignment_candidate', 'meeting_user', 'meeting_user_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_chat_group_t_read_group_ids AFTER INSERT ON chat_group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_chat_group_read_group_ids_group_t', 'chat_group_id', 'chat_group', 'group_id', 'group', 'meeting_id', 'read_group_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_read_chat_group_ids AFTER INSERT ON group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_chat_group_read_group_ids_group_t', 'group_id', 'group', 'chat_group_id', 'chat_group', 'meeting_id', 'read_chat_group_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_chat_group_t_read_group_ids_intermediate AFTER INSERT ON nm_chat_group_read_group_ids_group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('chat_group_id', 'chat_group', 'group_id', 'group', 'meeting_id', 'read_group_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_chat_group_t_write_group_ids AFTER INSERT ON chat_group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_chat_group_write_group_ids_group_t', 'chat_group_id', 'chat_group', 'group_id', 'group', 'meeting_id', 'write_group_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_write_chat_group_ids AFTER INSERT ON group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_chat_group_write_group_ids_group_t', 'group_id', 'group', 'chat_group_id', 'chat_group', 'meeting_id', 'write_chat_group_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_chat_group_t_write_group_ids_intermediate AFTER INSERT ON nm_chat_group_write_group_ids_group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('chat_group_id', 'chat_group', 'group_id', 'group', 'meeting_id', 'write_group_ids');



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_chat_message_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id ON chat_message_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('chat_message', 'meeting_user', 'meeting_user_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_chat_message_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('chat_message', 'meeting_user', 'meeting_user_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_chat_message_t_chat_group_id AFTER INSERT ON chat_message_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('chat_message', 'chat_group', 'chat_group_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_chat_group_t_chat_message_ids AFTER INSERT ON chat_group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('chat_message', 'chat_group', 'chat_group_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_meeting_user_ids AFTER INSERT ON group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_group_meeting_user_ids_meeting_user_t', 'group_id', 'group', 'meeting_user_id', 'meeting_user', 'meeting_id', 'meeting_user_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_group_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_group_meeting_user_ids_meeting_user_t', 'meeting_user_id', 'meeting_user', 'group_id', 'group', 'meeting_id', 'group_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_meeting_user_ids_intermediate AFTER INSERT ON nm_group_meeting_user_ids_meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('group_id', 'group', 'meeting_user_id', 'meeting_user', 'meeting_id', 'meeting_user_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_meeting_mediafile_access_group_ids AFTER INSERT ON group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_group_mmagi_meeting_mediafile_t', 'group_id', 'group', 'meeting_mediafile_id', 'meeting_mediafile', 'meeting_id', 'meeting_mediafile_access_group_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_mediafile_t_access_group_ids AFTER INSERT ON meeting_mediafile_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_group_mmagi_meeting_mediafile_t', 'meeting_mediafile_id', 'meeting_mediafile', 'group_id', 'group', 'meeting_id', 'access_group_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_meeting_mediafile_access_gro550f457 AFTER INSERT ON nm_group_mmagi_meeting_mediafile_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('group_id', 'group', 'meeting_mediafile_id', 'meeting_mediafile', 'meeting_id', 'meeting_mediafile_access_group_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_read_comment_section_ids AFTER INSERT ON group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_group_read_comment_section_ids_motion_comment_section_t', 'group_id', 'group', 'motion_comment_section_id', 'motion_comment_section', 'meeting_id', 'read_comment_section_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_comment_section_t_read_group_ids AFTER INSERT ON motion_comment_section_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_group_read_comment_section_ids_motion_comment_section_t', 'motion_comment_section_id', 'motion_comment_section', 'group_id', 'group', 'meeting_id', 'read_group_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_read_comment_section_ids_intee20888 AFTER INSERT ON nm_group_read_comment_section_ids_motion_comment_section_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('group_id', 'group', 'motion_comment_section_id', 'motion_comment_section', 'meeting_id', 'read_comment_section_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_write_comment_section_ids AFTER INSERT ON group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_group_write_comment_section_ids_motion_comment_section_t', 'group_id', 'group', 'motion_comment_section_id', 'motion_comment_section', 'meeting_id', 'write_comment_section_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_comment_section_t_write_group_ids AFTER INSERT ON motion_comment_section_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_group_write_comment_section_ids_motion_comment_section_t', 'motion_comment_section_id', 'motion_comment_section', 'group_id', 'group', 'meeting_id', 'write_group_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_write_comment_section_ids_in069881a AFTER INSERT ON nm_group_write_comment_section_ids_motion_comment_section_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('group_id', 'group', 'motion_comment_section_id', 'motion_comment_section', 'meeting_id', 'write_comment_section_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_poll_ids AFTER INSERT ON group_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_group_poll_ids_poll_t', 'group_id', 'group', 'poll_id', 'poll', 'meeting_id', 'poll_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_poll_t_entitled_group_ids AFTER INSERT ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_group_poll_ids_poll_t', 'poll_id', 'poll', 'group_id', 'group', 'meeting_id', 'entitled_group_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_group_t_poll_ids_intermediate AFTER INSERT ON nm_group_poll_ids_poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('group_id', 'group', 'poll_id', 'poll', 'meeting_id', 'poll_ids');



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_list_of_speakers_t_content_object_id15e708c AFTER INSERT ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('list_of_speakers', 'motion', 'content_object_id_motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_list_of_speakers_id AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('list_of_speakers', 'motion', 'content_object_id_motion_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_list_of_speakers_t_content_object_id76189b9 AFTER INSERT ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('list_of_speakers', 'motion_block', 'content_object_id_motion_block_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_block_t_list_of_speakers_id AFTER INSERT ON motion_block_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('list_of_speakers', 'motion_block', 'content_object_id_motion_block_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_list_of_speakers_t_content_object_id8e13f04 AFTER INSERT ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('list_of_speakers', 'assignment', 'content_object_id_assignment_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_assignment_t_list_of_speakers_id AFTER INSERT ON assignment_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('list_of_speakers', 'assignment', 'content_object_id_assignment_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_list_of_speakers_t_content_object_id06f0c1e AFTER INSERT ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('list_of_speakers', 'topic', 'content_object_id_topic_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_topic_t_list_of_speakers_id AFTER INSERT ON topic_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('list_of_speakers', 'topic', 'content_object_id_topic_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_list_of_speakers_t_content_object_ide897434 AFTER INSERT ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('list_of_speakers', 'meeting_mediafile', 'content_object_id_meeting_mediafile_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_mediafile_t_list_of_speakers_id AFTER INSERT ON meeting_mediafile_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('list_of_speakers', 'meeting_mediafile', 'content_object_id_meeting_mediafile_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_owner_id_on_mediafile_t_parent_id AFTER INSERT OR UPDATE OF parent_id ON mediafile_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('mediafile', 'mediafile', 'parent_id', 'owner_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_owner_id_on_mediafile_t_child_ids AFTER INSERT ON mediafile_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('mediafile', 'mediafile', 'parent_id', 'owner_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_mediafile_t_attachment_ids_motion_t AFTER INSERT ON meeting_mediafile_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_meeting_mediafile_attachment_ids_t', 'meeting_mediafile_id', 'meeting_mediafile', 'attachment_id_motion_id', 'motion', 'meeting_id', 'attachment_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_attachment_meeting_mediafile_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_meeting_mediafile_attachment_ids_t', 'attachment_id_motion_id', 'motion', 'meeting_mediafile_id', 'meeting_mediafile', 'meeting_id', 'attachment_meeting_mediafile_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_mediafile_t_attachment_ids_m4e89aaf AFTER INSERT ON gm_meeting_mediafile_attachment_ids_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('meeting_mediafile_id', 'meeting_mediafile', 'attachment_id_motion_id', 'motion', 'meeting_id', 'attachment_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_mediafile_t_attachment_ids_topic_t AFTER INSERT ON meeting_mediafile_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_meeting_mediafile_attachment_ids_t', 'meeting_mediafile_id', 'meeting_mediafile', 'attachment_id_topic_id', 'topic', 'meeting_id', 'attachment_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_topic_t_attachment_meeting_mediafile_ids AFTER INSERT ON topic_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_meeting_mediafile_attachment_ids_t', 'attachment_id_topic_id', 'topic', 'meeting_mediafile_id', 'meeting_mediafile', 'meeting_id', 'attachment_meeting_mediafile_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_mediafile_t_attachment_ids_t3e058c9 AFTER INSERT ON gm_meeting_mediafile_attachment_ids_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('meeting_mediafile_id', 'meeting_mediafile', 'attachment_id_topic_id', 'topic', 'meeting_id', 'attachment_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_mediafile_t_attachment_ids_a02016b9 AFTER INSERT ON meeting_mediafile_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_meeting_mediafile_attachment_ids_t', 'meeting_mediafile_id', 'meeting_mediafile', 'attachment_id_assignment_id', 'assignment', 'meeting_id', 'attachment_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_assignment_t_attachment_meeting_media9bbdf7 AFTER INSERT ON assignment_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_meeting_mediafile_attachment_ids_t', 'attachment_id_assignment_id', 'assignment', 'meeting_mediafile_id', 'meeting_mediafile', 'meeting_id', 'attachment_meeting_mediafile_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_mediafile_t_attachment_ids_a29e0815 AFTER INSERT ON gm_meeting_mediafile_attachment_ids_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('meeting_mediafile_id', 'meeting_mediafile', 'attachment_id_assignment_id', 'assignment', 'meeting_id', 'attachment_ids');



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_vote_delegated_to_id AFTER INSERT OR UPDATE OF vote_delegated_to_id ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('meeting_user', 'meeting_user', 'vote_delegated_to_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_vote_delegations_from_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('meeting_user', 'meeting_user', 'vote_delegated_to_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_structure_level_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_meeting_user_structure_level_ids_structure_level_t', 'meeting_user_id', 'meeting_user', 'structure_level_id', 'structure_level', 'meeting_id', 'structure_level_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_structure_level_t_meeting_user_ids AFTER INSERT ON structure_level_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_meeting_user_structure_level_ids_structure_level_t', 'structure_level_id', 'structure_level', 'meeting_user_id', 'meeting_user', 'meeting_id', 'meeting_user_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_structure_level_ids_i91a9439 AFTER INSERT ON nm_meeting_user_structure_level_ids_structure_level_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('meeting_user_id', 'meeting_user', 'structure_level_id', 'structure_level', 'meeting_id', 'structure_level_ids');



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_lead_motion_id AFTER INSERT OR UPDATE OF lead_motion_id ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion', 'lead_motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_amendment_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion', 'lead_motion_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_sort_parent_id AFTER INSERT OR UPDATE OF sort_parent_id ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion', 'sort_parent_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_sort_child_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion', 'sort_parent_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_state_id AFTER INSERT OR UPDATE OF state_id ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion_state', 'state_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_state_t_motion_ids AFTER INSERT ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion_state', 'state_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_recommendation_id AFTER INSERT OR UPDATE OF recommendation_id ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion_state', 'recommendation_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_state_t_motion_recommendation_ids AFTER INSERT ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion_state', 'recommendation_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_state_extension_reference_ia334c80 AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_motion_state_extension_reference_ids_t', 'motion_id', 'motion', 'state_extension_reference_id_motion_id', 'motion', 'meeting_id', 'state_extension_reference_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_referenced_in_motion_state_cb2bfc0 AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_motion_state_extension_reference_ids_t', 'state_extension_reference_id_motion_id', 'motion', 'motion_id', 'motion', 'meeting_id', 'referenced_in_motion_state_extension_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_state_extension_reference_i05b20ae AFTER INSERT ON gm_motion_state_extension_reference_ids_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('motion_id', 'motion', 'state_extension_reference_id_motion_id', 'motion', 'meeting_id', 'state_extension_reference_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_recommendation_extension_re94d51da AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_motion_recommendation_extension_reference_ids_t', 'motion_id', 'motion', 'recommendation_extension_reference_id_motion_id', 'motion', 'meeting_id', 'recommendation_extension_reference_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_referenced_in_motion_recomm09d2a9c AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_motion_recommendation_extension_reference_ids_t', 'recommendation_extension_reference_id_motion_id', 'motion', 'motion_id', 'motion', 'meeting_id', 'referenced_in_motion_recommendation_extension_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_recommendation_extension_rebcec849 AFTER INSERT ON gm_motion_recommendation_extension_reference_ids_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('motion_id', 'motion', 'recommendation_extension_reference_id_motion_id', 'motion', 'meeting_id', 'recommendation_extension_reference_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_category_id AFTER INSERT OR UPDATE OF category_id ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion_category', 'category_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_category_t_motion_ids AFTER INSERT ON motion_category_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion_category', 'category_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_block_id AFTER INSERT OR UPDATE OF block_id ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion_block', 'block_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_block_t_motion_ids AFTER INSERT ON motion_block_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion', 'motion_block', 'block_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_category_t_parent_id AFTER INSERT OR UPDATE OF parent_id ON motion_category_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_category', 'motion_category', 'parent_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_category_t_child_ids AFTER INSERT ON motion_category_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_category', 'motion_category', 'parent_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_change_recommendation_t_motion_id AFTER INSERT ON motion_change_recommendation_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_change_recommendation', 'motion', 'motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_change_recommendation_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_change_recommendation', 'motion', 'motion_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_comment_t_motion_id AFTER INSERT ON motion_comment_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_comment', 'motion', 'motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_comment_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_comment', 'motion', 'motion_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_comment_t_section_id AFTER INSERT ON motion_comment_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_comment', 'motion_comment_section', 'section_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_comment_section_t_comment_ids AFTER INSERT ON motion_comment_section_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_comment', 'motion_comment_section', 'section_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_editor_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id ON motion_editor_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_editor', 'meeting_user', 'meeting_user_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_motion_editor_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_editor', 'meeting_user', 'meeting_user_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_editor_t_motion_id AFTER INSERT ON motion_editor_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_editor', 'motion', 'motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_editor_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_editor', 'motion', 'motion_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_state_t_submitter_withdraw_state_id AFTER INSERT OR UPDATE OF submitter_withdraw_state_id ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_state', 'motion_state', 'submitter_withdraw_state_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_state_t_submitter_withdraw_back_ids AFTER INSERT ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_state', 'motion_state', 'submitter_withdraw_state_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_workflow_id_on_motion_state_t_submitter_withdraw_state_id AFTER INSERT OR UPDATE OF submitter_withdraw_state_id, workflow_id ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_state', 'motion_state', 'submitter_withdraw_state_id', 'workflow_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_workflow_id_on_motion_state_t_submitter_withdraw_back_ids AFTER INSERT OR UPDATE OF workflow_id ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_state', 'motion_state', 'submitter_withdraw_state_id', 'workflow_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_state_t_next_state_ids AFTER INSERT ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_motion_state_next_state_ids_motion_state_t', 'previous_state_id', 'motion_state', 'next_state_id', 'motion_state', 'meeting_id', 'next_state_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_state_t_previous_state_ids AFTER INSERT ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_motion_state_next_state_ids_motion_state_t', 'next_state_id', 'motion_state', 'previous_state_id', 'motion_state', 'meeting_id', 'previous_state_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_state_t_next_state_ids_intermediate AFTER INSERT ON nm_motion_state_next_state_ids_motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('previous_state_id', 'motion_state', 'next_state_id', 'motion_state', 'meeting_id', 'next_state_ids');


CREATE CONSTRAINT TRIGGER equal_workflow_id_on_motion_state_t_next_state_ids AFTER INSERT OR UPDATE OF workflow_id ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_motion_state_next_state_ids_motion_state_t', 'previous_state_id', 'motion_state', 'next_state_id', 'motion_state', 'workflow_id', 'next_state_ids');
CREATE CONSTRAINT TRIGGER equal_workflow_id_on_motion_state_t_previous_state_ids AFTER INSERT OR UPDATE OF workflow_id ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('nm_motion_state_next_state_ids_motion_state_t', 'next_state_id', 'motion_state', 'previous_state_id', 'motion_state', 'workflow_id', 'previous_state_ids');
CREATE CONSTRAINT TRIGGER equal_workflow_id_on_motion_state_t_next_state_ids_intermediate AFTER INSERT ON nm_motion_state_next_state_ids_motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('previous_state_id', 'motion_state', 'next_state_id', 'motion_state', 'workflow_id', 'next_state_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_state_t_workflow_id AFTER INSERT OR UPDATE OF workflow_id ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_state', 'motion_workflow', 'workflow_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_workflow_t_state_ids AFTER INSERT ON motion_workflow_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_state', 'motion_workflow', 'workflow_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_submitter_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id ON motion_submitter_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_submitter', 'meeting_user', 'meeting_user_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_motion_submitter_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_submitter', 'meeting_user', 'meeting_user_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_submitter_t_motion_id AFTER INSERT ON motion_submitter_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_submitter', 'motion', 'motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_submitter_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_submitter', 'motion', 'motion_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_supporter_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id ON motion_supporter_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_supporter', 'meeting_user', 'meeting_user_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_motion_supporter_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_supporter', 'meeting_user', 'meeting_user_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_supporter_t_motion_id AFTER INSERT ON motion_supporter_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_supporter', 'motion', 'motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_supporter_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_supporter', 'motion', 'motion_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_workflow_t_first_state_id AFTER INSERT OR UPDATE OF first_state_id ON motion_workflow_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_workflow', 'motion_state', 'first_state_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_state_t_first_state_of_workflow_id AFTER INSERT ON motion_state_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_workflow', 'motion_state', 'first_state_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_working_group_speaker_t_meeti339019b AFTER INSERT OR UPDATE OF meeting_user_id ON motion_working_group_speaker_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_working_group_speaker', 'meeting_user', 'meeting_user_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_motion_working_group_bf2dd11 AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_working_group_speaker', 'meeting_user', 'meeting_user_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_working_group_speaker_t_motion_id AFTER INSERT ON motion_working_group_speaker_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_working_group_speaker', 'motion', 'motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_working_group_speaker_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('motion_working_group_speaker', 'motion', 'motion_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_option_t_poll_id AFTER INSERT ON option_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('option', 'poll', 'poll_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_poll_t_option_ids AFTER INSERT ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('option', 'poll', 'poll_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_option_t_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id ON option_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('option', 'motion', 'content_object_id_motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_option_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('option', 'motion', 'content_object_id_motion_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_option_t_content_object_id_poll_cand57125c5 AFTER INSERT OR UPDATE OF content_object_id ON option_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('option', 'poll_candidate_list', 'content_object_id_poll_candidate_list_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_poll_candidate_list_t_option_id AFTER INSERT ON poll_candidate_list_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('option', 'poll_candidate_list', 'content_object_id_poll_candidate_list_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_personal_note_t_meeting_user_id AFTER INSERT ON personal_note_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('personal_note', 'meeting_user', 'meeting_user_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_personal_note_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('personal_note', 'meeting_user', 'meeting_user_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_personal_note_t_content_object_id_motion_id AFTER INSERT ON personal_note_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('personal_note', 'motion', 'content_object_id_motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_personal_note_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('personal_note', 'motion', 'content_object_id_motion_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_poll_t_content_object_id_motion_id AFTER INSERT ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll', 'motion', 'content_object_id_motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_poll_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll', 'motion', 'content_object_id_motion_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_poll_t_content_object_id_assignment_id AFTER INSERT ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll', 'assignment', 'content_object_id_assignment_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_assignment_t_poll_ids AFTER INSERT ON assignment_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll', 'assignment', 'content_object_id_assignment_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_poll_t_content_object_id_topic_id AFTER INSERT ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll', 'topic', 'content_object_id_topic_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_topic_t_poll_ids AFTER INSERT ON topic_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll', 'topic', 'content_object_id_topic_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_poll_t_global_option_id AFTER INSERT OR UPDATE OF global_option_id ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll', 'option', 'global_option_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_option_t_used_as_global_option_in_poll_id AFTER INSERT ON option_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll', 'option', 'global_option_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_poll_candidate_t_poll_candidate_list_id AFTER INSERT ON poll_candidate_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll_candidate', 'poll_candidate_list', 'poll_candidate_list_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_poll_candidate_list_t_poll_candidate_ids AFTER INSERT ON poll_candidate_list_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('poll_candidate', 'poll_candidate_list', 'poll_candidate_list_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_current_projector_id AFTER INSERT OR UPDATE OF current_projector_id ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'projector', 'current_projector_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projector_t_current_projection_ids AFTER INSERT ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'projector', 'current_projector_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_preview_projector_id AFTER INSERT OR UPDATE OF preview_projector_id ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'projector', 'preview_projector_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projector_t_preview_projection_ids AFTER INSERT ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'projector', 'preview_projector_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_history_projector_id AFTER INSERT OR UPDATE OF history_projector_id ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'projector', 'history_projector_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projector_t_history_projection_ids AFTER INSERT ON projector_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'projector', 'history_projector_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_meeting_id AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_meeting_id_for_meeting('projection', 'content_object_id_meeting_id');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_motion_id AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'motion', 'content_object_id_motion_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_projection_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'motion', 'content_object_id_motion_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_meeti1e00bfd AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'meeting_mediafile', 'content_object_id_meeting_mediafile_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_mediafile_t_projection_ids AFTER INSERT ON meeting_mediafile_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'meeting_mediafile', 'content_object_id_meeting_mediafile_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_list_b1d0522 AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'list_of_speakers', 'content_object_id_list_of_speakers_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_list_of_speakers_t_projection_ids AFTER INSERT ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'list_of_speakers', 'content_object_id_list_of_speakers_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_motiofc26eda AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'motion_block', 'content_object_id_motion_block_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_block_t_projection_ids AFTER INSERT ON motion_block_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'motion_block', 'content_object_id_motion_block_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_assig83f4402 AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'assignment', 'content_object_id_assignment_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_assignment_t_projection_ids AFTER INSERT ON assignment_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'assignment', 'content_object_id_assignment_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_agend9ca4c9d AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'agenda_item', 'content_object_id_agenda_item_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_agenda_item_t_projection_ids AFTER INSERT ON agenda_item_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'agenda_item', 'content_object_id_agenda_item_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_topic_id AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'topic', 'content_object_id_topic_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_topic_t_projection_ids AFTER INSERT ON topic_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'topic', 'content_object_id_topic_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_poll_id AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'poll', 'content_object_id_poll_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_poll_t_projection_ids AFTER INSERT ON poll_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'poll', 'content_object_id_poll_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_proje49e908a AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'projector_message', 'content_object_id_projector_message_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projector_message_t_projection_ids AFTER INSERT ON projector_message_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'projector_message', 'content_object_id_projector_message_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projection_t_content_object_id_proje0cc49a1 AFTER INSERT ON projection_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'projector_countdown', 'content_object_id_projector_countdown_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_projector_countdown_t_projection_ids AFTER INSERT ON projector_countdown_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('projection', 'projector_countdown', 'content_object_id_projector_countdown_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_speaker_t_list_of_speakers_id AFTER INSERT ON speaker_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('speaker', 'list_of_speakers', 'list_of_speakers_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_list_of_speakers_t_speaker_ids AFTER INSERT ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('speaker', 'list_of_speakers', 'list_of_speakers_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_speaker_t_structure_level_list_of_sp9ebc874 AFTER INSERT OR UPDATE OF structure_level_list_of_speakers_id ON speaker_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('speaker', 'structure_level_list_of_speakers', 'structure_level_list_of_speakers_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_structure_level_list_of_speakers_t_s3419e66 AFTER INSERT ON structure_level_list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('speaker', 'structure_level_list_of_speakers', 'structure_level_list_of_speakers_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_speaker_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id ON speaker_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('speaker', 'meeting_user', 'meeting_user_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_meeting_user_t_speaker_ids AFTER INSERT ON meeting_user_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('speaker', 'meeting_user', 'meeting_user_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_speaker_t_point_of_order_category_id AFTER INSERT OR UPDATE OF point_of_order_category_id ON speaker_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('speaker', 'point_of_order_category', 'point_of_order_category_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_point_of_order_category_t_speaker_ids AFTER INSERT ON point_of_order_category_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('speaker', 'point_of_order_category', 'point_of_order_category_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_structure_level_list_of_speakers_t_s9bddf8d AFTER INSERT OR UPDATE OF structure_level_id ON structure_level_list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('structure_level_list_of_speakers', 'structure_level', 'structure_level_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_structure_level_t_structure_level_lice7955c AFTER INSERT ON structure_level_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('structure_level_list_of_speakers', 'structure_level', 'structure_level_id', 'meeting_id', TRUE);


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_structure_level_list_of_speakers_t_lf3ea816 AFTER INSERT OR UPDATE OF list_of_speakers_id ON structure_level_list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('structure_level_list_of_speakers', 'list_of_speakers', 'list_of_speakers_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_list_of_speakers_t_structure_level_lb63ec40 AFTER INSERT ON list_of_speakers_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('structure_level_list_of_speakers', 'list_of_speakers', 'list_of_speakers_id', 'meeting_id', TRUE);



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_tag_t_tagged_ids_agenda_item_t AFTER INSERT ON tag_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_tag_tagged_ids_t', 'tag_id', 'tag', 'tagged_id_agenda_item_id', 'agenda_item', 'meeting_id', 'tagged_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_agenda_item_t_tag_ids AFTER INSERT ON agenda_item_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_tag_tagged_ids_t', 'tagged_id_agenda_item_id', 'agenda_item', 'tag_id', 'tag', 'meeting_id', 'tag_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_tag_t_tagged_ids_agenda_item_t_intermediate AFTER INSERT ON gm_tag_tagged_ids_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('tag_id', 'tag', 'tagged_id_agenda_item_id', 'agenda_item', 'meeting_id', 'tagged_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_tag_t_tagged_ids_assignment_t AFTER INSERT ON tag_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_tag_tagged_ids_t', 'tag_id', 'tag', 'tagged_id_assignment_id', 'assignment', 'meeting_id', 'tagged_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_assignment_t_tag_ids AFTER INSERT ON assignment_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_tag_tagged_ids_t', 'tagged_id_assignment_id', 'assignment', 'tag_id', 'tag', 'meeting_id', 'tag_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_tag_t_tagged_ids_assignment_t_intermediate AFTER INSERT ON gm_tag_tagged_ids_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('tag_id', 'tag', 'tagged_id_assignment_id', 'assignment', 'meeting_id', 'tagged_ids');


CREATE CONSTRAINT TRIGGER equal_meeting_id_on_tag_t_tagged_ids_motion_t AFTER INSERT ON tag_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_tag_tagged_ids_t', 'tag_id', 'tag', 'tagged_id_motion_id', 'motion', 'meeting_id', 'tagged_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_motion_t_tag_ids AFTER INSERT ON motion_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_multi('gm_tag_tagged_ids_t', 'tagged_id_motion_id', 'motion', 'tag_id', 'tag', 'meeting_id', 'tag_ids');
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_tag_t_tagged_ids_motion_t_intermediate AFTER INSERT ON gm_tag_tagged_ids_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals_intermediate('tag_id', 'tag', 'tagged_id_motion_id', 'motion', 'meeting_id', 'tagged_ids');



CREATE CONSTRAINT TRIGGER equal_meeting_id_on_vote_t_option_id AFTER INSERT ON vote_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('vote', 'option', 'option_id', 'meeting_id', FALSE);
CREATE CONSTRAINT TRIGGER equal_meeting_id_on_option_t_vote_ids AFTER INSERT ON option_t INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION check_equals('vote', 'option', 'option_id', 'meeting_id', TRUE);


