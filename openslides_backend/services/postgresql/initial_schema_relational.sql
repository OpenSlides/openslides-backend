
-- schema_relational.sql for initial database setup OpenSlides
-- Code generated. DO NOT EDIT.
-- MODELS_YML_CHECKSUM = 'd9e38d61c6f4557dbfda3a3daa39848a'


-- ENUM definitions

CREATE TYPE enum_languages AS ENUM ('en', 'de', 'it', 'es', 'ru', 'cs', 'fr');

CREATE TYPE enum_ballot_paper_selection AS ENUM ('NUMBER_OF_DELEGATES', 'NUMBER_OF_ALL_PARTICIPANTS', 'CUSTOM_NUMBER');

CREATE TYPE enum_poll_backends AS ENUM ('long', 'fast');

CREATE TYPE enum_onehundred_percent_bases AS ENUM ('Y', 'YN', 'YNA', 'N', 'valid', 'cast', 'entitled', 'entitled_present', 'disabled');

CREATE TYPE enum_action_worker_state AS ENUM ('running', 'end', 'aborted');

CREATE TYPE enum_agenda_item_type AS ENUM ('common', 'internal', 'hidden');

CREATE TYPE enum_assignment_phase AS ENUM ('search', 'voting', 'finished');

CREATE TYPE enum_group_permissions AS ENUM ('agenda_item.can_manage', 'agenda_item.can_see', 'agenda_item.can_see_internal', 'assignment.can_manage', 'assignment.can_manage_polls', 'assignment.can_nominate_other', 'assignment.can_nominate_self', 'assignment.can_see', 'chat.can_manage', 'list_of_speakers.can_be_speaker', 'list_of_speakers.can_manage', 'list_of_speakers.can_see', 'list_of_speakers.can_manage_moderator_notes', 'list_of_speakers.can_see_moderator_notes', 'mediafile.can_manage', 'mediafile.can_see', 'meeting.can_manage_logos_and_fonts', 'meeting.can_manage_settings', 'meeting.can_see_autopilot', 'meeting.can_see_frontpage', 'meeting.can_see_history', 'meeting.can_see_livestream', 'motion.can_create', 'motion.can_create_amendments', 'motion.can_forward', 'motion.can_manage', 'motion.can_manage_metadata', 'motion.can_manage_polls', 'motion.can_see', 'motion.can_see_internal', 'motion.can_see_origin', 'motion.can_support', 'poll.can_manage', 'poll.can_see_progress', 'projector.can_manage', 'projector.can_see', 'tag.can_manage', 'user.can_manage', 'user.can_manage_presence', 'user.can_see_sensitive_data', 'user.can_see', 'user.can_update', 'user.can_edit_own_delegation');

CREATE TYPE enum_import_preview_name AS ENUM ('account', 'participant', 'topic', 'committee', 'motion');

CREATE TYPE enum_import_preview_state AS ENUM ('warning', 'error', 'done');

CREATE TYPE enum_meeting_applause_type AS ENUM ('applause-type-bar', 'applause-type-particles');

CREATE TYPE enum_meeting_export_csv_encoding AS ENUM ('utf-8', 'iso-8859-15');

CREATE TYPE enum_meeting_export_pdf_pagenumber_alignment AS ENUM ('left', 'right', 'center');

CREATE TYPE enum_meeting_export_pdf_pagesize AS ENUM ('A4', 'A5');

CREATE TYPE enum_meeting_agenda_numeral_system AS ENUM ('arabic', 'roman');

CREATE TYPE enum_meeting_agenda_item_creation AS ENUM ('always', 'never', 'default_yes', 'default_no');

CREATE TYPE enum_meeting_agenda_new_items_default_visibility AS ENUM ('common', 'internal', 'hidden');

CREATE TYPE enum_meeting_motions_default_line_numbering AS ENUM ('outside', 'inline', 'none');

CREATE TYPE enum_meeting_motions_recommendation_text_mode AS ENUM ('original', 'changed', 'diff', 'agreed');

CREATE TYPE enum_meeting_motions_default_sorting AS ENUM ('number', 'weight');

CREATE TYPE enum_meeting_motions_number_type AS ENUM ('per_category', 'serially_numbered', 'manually');

CREATE TYPE enum_meeting_motions_amendments_text_mode AS ENUM ('freestyle', 'fulltext', 'paragraph');

CREATE TYPE enum_meeting_motion_poll_projection_name_order_first AS ENUM ('first_name', 'last_name');

CREATE TYPE enum_meeting_users_pdf_wlan_encryption AS ENUM ('', 'WEP', 'WPA', 'nopass');

CREATE TYPE enum_motion_change_recommendation_type AS ENUM ('replacement', 'insertion', 'deletion', 'other');

CREATE TYPE enum_motion_state_css_class AS ENUM ('grey', 'red', 'green', 'lightblue', 'yellow');

CREATE TYPE enum_motion_state_restrictions AS ENUM ('motion.can_see_internal', 'motion.can_manage_metadata', 'motion.can_manage', 'is_submitter');

CREATE TYPE enum_motion_state_merge_amendment_into_final AS ENUM ('do_not_merge', 'undefined', 'do_merge');

CREATE TYPE enum_poll_type AS ENUM ('analog', 'named', 'pseudoanonymous', 'cryptographic');

CREATE TYPE enum_poll_pollmethod AS ENUM ('Y', 'YN', 'YNA', 'N');

CREATE TYPE enum_poll_state AS ENUM ('created', 'started', 'finished', 'published');

CREATE TYPE enum_speaker_speech_state AS ENUM ('contribution', 'pro', 'contra', 'intervention', 'interposed_question');

CREATE TYPE enum_user_organization_management_level AS ENUM ('superadmin', 'can_manage_organization', 'can_manage_users');



-- Function and meta table definitions

CREATE EXTENSION hstore;  -- included in standard postgres-installations, check for alpine

CREATE FUNCTION generate_sequence()
RETURNS trigger
AS $sequences_trigger$
-- Creates a sequence for the id given by depend_field NEW data if it doesn't exist.
-- Writes the next value to for this sequence to NEW.
-- In case a number is given in actual_column of the NEW record that is used
-- and the corresponding sequence increased if necessary.
-- Usage with 3 parameters IN TRIGGER DEFINITION:
-- table_name: table this is treated for
-- actual_column: column that will be filled with the actual value
-- depend_field: field that differentiates the sequences. usually meeting_id
DECLARE
    table_name TEXT := TG_ARGV[0];
    actual_column TEXT := TG_ARGV[1];
    depend_field TEXT := TG_ARGV[2];
    depend_field_id INTEGER;
    sequence_name TEXT;
    sequence_value INTEGER;
    sequence_max INTEGER;
BEGIN
    depend_field_id := hstore(NEW) -> (depend_field);
    sequence_name := table_name || '_' || depend_field || depend_field_id || '_' || actual_column || '_seq';
    EXECUTE format('CREATE SEQUENCE IF NOT EXISTS %I OWNED BY %I.%I', sequence_name, table_name, actual_column);
    sequence_value := hstore(NEW) -> actual_column;
    IF sequence_value IS NULL THEN
        sequence_value := nextval(sequence_name);
    ELSE
        EXECUTE format('SELECT last_value FROM %I', sequence_name) INTO sequence_max;
        -- <= because the unused sequence starts with last_value=1 and is_called=f and needs to be written to.
        IF sequence_max <= sequence_value THEN
            SELECT setval(sequence_name, sequence_value) INTO sequence_value;
        END IF;
    END IF;
    RETURN populate_record(NEW, format('%s=>%s',actual_column, sequence_value)::hstore);
END;
$sequences_trigger$
LANGUAGE plpgsql;

CREATE TABLE os_notify_log_t (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    operation varchar(32),
    fqid varchar(256) NOT NULL,
    updated_fields varchar(63)[],
    xact_id xid8,
    timestamp timestamptz,
    CONSTRAINT unique_fqid_xact_id_operation UNIQUE (operation,fqid,xact_id)
);

CREATE TABLE version (
    migration_index INTEGER PRIMARY KEY,
    migration_state TEXT,
    replace_tables JSONB
);

-- Log functions

CREATE OR REPLACE PROCEDURE log_field_change(
    operation_var TEXT,
    fqid_var TEXT,
    fields TEXT[]
) AS
$log_field_change$
BEGIN
    INSERT INTO os_notify_log_t (operation, fqid, xact_id, timestamp, updated_fields)
    VALUES (operation_var, fqid_var, pg_current_xact_id(), now(), fields)
    ON CONFLICT (operation, fqid, xact_id) DO UPDATE SET updated_fields = (
        SELECT ARRAY(
            SELECT DISTINCT e
            FROM unnest(COALESCE(os_notify_log_t.updated_fields, '{}'::varchar[])) AS e
            UNION
            SELECT DISTINCT e
            FROM unnest(COALESCE(EXCLUDED.updated_fields, '{}'::varchar[])) AS e
        )
    );
END;
$log_field_change$ LANGUAGE plpgsql;

CREATE FUNCTION log_modified_models() RETURNS trigger AS $log_modified_trigger$
DECLARE
    escaped_table_name varchar;
    operation_var TEXT;
    fqid_var TEXT;
    updated_fields_var varchar(63)[];
    old_hstore hstore;
    new_hstore hstore;
BEGIN
    escaped_table_name := TG_ARGV[0];
    operation_var := LOWER(TG_OP);

    -- Determine fqid (use OLD for deletes)
    fqid_var := escaped_table_name || '/' || NEW.id;
    IF (TG_OP = 'DELETE') THEN
        fqid_var := escaped_table_name || '/' || OLD.id;
    END IF;

    updated_fields_var := NULL;
    IF (TG_OP = 'UPDATE') THEN
        old_hstore := hstore(OLD);
        new_hstore := hstore(NEW);
        updated_fields_var := akeys((new_hstore - old_hstore) || (old_hstore - new_hstore));
    END IF;

    CALL log_field_change(operation_var, fqid_var, updated_fields_var);

    RETURN NULL;  -- returning NULL because AFTER TRIGGER return value is ignored
END;
$log_modified_trigger$ LANGUAGE plpgsql;

CREATE FUNCTION notify_transaction_end() RETURNS trigger AS $notify_trigger$
DECLARE
    payload TEXT;
    body_content_text TEXT;
BEGIN
    -- Running the trigger for the first time in a transaction creates the table and after committing the transaction the table is dropped.
    -- Every next run of the trigger in this transaction raises a notice that the table exists. Setting the log_min_messages to notice increases the noise because of such messages.
    CREATE LOCAL TEMPORARY TABLE
    IF NOT EXISTS tbl_notify_counter_tx_once (
        "id" integer NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY
    ) ON COMMIT DROP;

    -- If running for the first time, the transaction id is send via os_notify.
    IF NOT EXISTS (SELECT * FROM tbl_notify_counter_tx_once) THEN
        INSERT INTO tbl_notify_counter_tx_once DEFAULT VALUES;
        payload := '{"xactId":' ||
            pg_current_xact_id() ||
            '}';
        PERFORM pg_notify('os_notify', payload);
    END IF;

    RETURN NULL;  -- returning NULL because AFTER TRIGGER return value is ignored
END;
$notify_trigger$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION log_modified_related_models()
RETURNS trigger AS $log_modified_related_trigger$
DECLARE
    fqid_var TEXT;
    ref_column TEXT;
    fk_field TEXT;
    foreign_table TEXT;
    foreign_id TEXT;
    i INTEGER := 0;
BEGIN

    WHILE i < TG_NARGS LOOP
        foreign_table := TG_ARGV[i];
        ref_column := TG_ARGV[i+1];
        fk_field := TG_ARGV[i+2];

        IF (TG_OP = 'DELETE') THEN
            EXECUTE format('SELECT ($1).%I', ref_column) INTO foreign_id USING OLD;
        ELSE
            EXECUTE format('SELECT ($1).%I', ref_column) INTO foreign_id USING NEW;
        END IF;

        IF foreign_id IS NOT NULL THEN
            fqid_var := foreign_table || '/' || foreign_id;
            CALL log_field_change('update', fqid_var, ARRAY[fk_field]);
        END IF;

        --when update there must be a notification for the old foreign_fqid
        IF (TG_OP = 'UPDATE') THEN
            EXECUTE format('SELECT ($1).%I', ref_column) INTO foreign_id USING OLD;
            IF foreign_id IS NOT NULL THEN
                fqid_var := foreign_table || '/' || foreign_id;
                CALL log_field_change('update', fqid_var, ARRAY[fk_field]);
            END IF;
        END IF;

        i := i + 3;
    END LOOP;

    RETURN NULL;  -- returning NULL because AFTER TRIGGER return value is ignored
END;
$log_modified_related_trigger$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION log_iu_modified_calculated_id_array_field()
RETURNS trigger AS $log_modified_calculated_id_array_field_trigger$
-- Expects in this order:
-- 0. log_collection – Target collection for the log entry
-- 1. log_collection_id_column – Column used to fetch the 'log_collection' id
--    (ignored if 'log_collection_id_sql' is provided => may be NULL)
-- 2. log_collection_id_sql – Custom SQL to fetch the 'log_collection' id
-- 3. log_field – Field to be logged
-- 4. added_item_column – Column used to fetch the value added to 'log_field'
--    (ignored if 'added_item_sql' is provided => may be NULL)
-- 5. added_item_sql – Custom SQL to fetch the value added to 'log_field'
DECLARE
    log_collection TEXT := TG_ARGV[0];
    log_collection_id_column TEXT := TG_ARGV[1];
    log_collection_id_sql TEXT := TG_ARGV[2];
    log_field TEXT := TG_ARGV[3];
    added_item_column TEXT := TG_ARGV[4];
    added_item_sql TEXT := TG_ARGV[5];

    new_hstore hstore := hstore(NEW);
    log_collection_id INTEGER;
    added_item INTEGER;
    old_log_field_value INTEGER[];
    fqid_var TEXT;
BEGIN
    -- No related log_collection instance -> return
    IF (log_collection_id_sql <> '') THEN
        EXECUTE log_collection_id_sql INTO log_collection_id USING NEW;
    ELSE
        log_collection_id := new_hstore -> log_collection_id_column;
    END IF;

    IF log_collection_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- No value in column used for log_field -> return
    -- Value deletion on update is processed in after-trigger
    IF (added_item_sql <> '') THEN
        EXECUTE added_item_sql INTO added_item USING NEW;
    ELSE
        added_item := new_hstore -> added_item_column;
    END IF;

    IF added_item IS NULL THEN
        RETURN NEW;
    END IF;

    -- Add log entry only if log_field value actually changes
    EXECUTE format('SELECT %I from %I where id = %L', log_field, log_collection, log_collection_id) INTO old_log_field_value;
    IF old_log_field_value IS NULL OR NOT (added_item = ANY(old_log_field_value)) THEN
        fqid_var := log_collection || '/' || log_collection_id;
        CALL log_field_change('update', fqid_var, ARRAY[log_field]);
    END IF;

    RETURN NEW;
END;
$log_modified_calculated_id_array_field_trigger$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION log_ud_modified_calculated_id_array_field()
RETURNS trigger AS $log_modified_calculated_id_array_field_trigger$
-- Expects in this order:
-- 0. log_collection – Target collection for the log entry
-- 1. log_collection_id_column – Column used to fetch the 'log_collection' id
--    (ignored if 'log_collection_id_sql' is provided => may be NULL)
-- 2. log_collection_id_sql – Custom SQL to fetch the 'log_collection' id
-- 3. log_field – Field to be logged
-- 4. deleted_item_column – Column used to fetch the value deleted from 'log_field'
--    (ignored if 'deleted_item_sql' is provided => may be NULL)
-- 5. deleted_item_sql – Custom SQL to fetch the value deleted from 'log_field'
DECLARE
    log_collection TEXT := TG_ARGV[0];
    log_collection_id_column TEXT := TG_ARGV[1];
    log_collection_id_sql TEXT := TG_ARGV[2];
    log_field TEXT := TG_ARGV[3];
    deleted_item_column TEXT := TG_ARGV[4];
    deleted_item_sql TEXT := TG_ARGV[5];

    old_hstore hstore := hstore(OLD);
    log_collection_id INTEGER;
    deleted_item INTEGER;
    new_log_field_value INTEGER[];
    fqid_var TEXT;
BEGIN
    -- No related log_collection instance -> return
    IF (log_collection_id_sql <> '') THEN
        EXECUTE log_collection_id_sql INTO log_collection_id USING OLD;
    ELSE
        log_collection_id := old_hstore -> log_collection_id_column;
    END IF;

    IF log_collection_id IS NULL THEN
        RETURN NULL;
    END IF;

    -- No value in column used for log_field -> return
    -- Value adding on update is processed in before-trigger
    IF (deleted_item_sql <> '') THEN
        EXECUTE deleted_item_sql INTO deleted_item USING OLD;
    ELSE
        deleted_item := old_hstore -> deleted_item_column;
    END IF;

    IF deleted_item IS NULL THEN
        RETURN NULL;
    END IF;

    -- Add log entry only if log_field value actually changes
    EXECUTE format('SELECT %I from %I where id = %L', log_field, log_collection, log_collection_id) INTO new_log_field_value;
    IF new_log_field_value IS NULL OR NOT (deleted_item = ANY(new_log_field_value)) THEN
        fqid_var := log_collection || '/' || log_collection_id;
        CALL log_field_change('update', fqid_var, ARRAY[log_field]);
    END IF;

    RETURN NULL;
END;
$log_modified_calculated_id_array_field_trigger$ LANGUAGE plpgsql;

-- Validation triggers

CREATE OR REPLACE FUNCTION is_timezone( tz TEXT ) RETURNS BOOLEAN as $$
DECLARE
    is_valid BOOLEAN;
BEGIN
    IF tz IS NULL THEN
        RETURN TRUE;
    END IF;

    SELECT EXISTS (SELECT 1 FROM pg_timezone_names WHERE name=tz) INTO is_valid;
    RETURN is_valid;
END;
$$ language plpgsql STABLE;

CREATE FUNCTION check_unique_ids_pair()
RETURNS trigger
AS $unique_ids_pair_trigger$
-- usage with 1 parameter IN TRIGGER DEFINITION:
-- base_column_name: name of write fields before adding numeric suffixes
-- Guards against mirrored duplicates by skipping one of the pairs.
DECLARE
    base_column_name text;
    value_1 integer;
    value_2 integer;
BEGIN
    base_column_name := TG_ARGV[0];
    value_1 := hstore(NEW) -> (base_column_name || '_1');
    value_2 := hstore(NEW) -> (base_column_name || '_2');

    IF (value_1 > value_2) THEN
        RETURN NULL;
    END IF;

    RETURN NEW;
END;
$unique_ids_pair_trigger$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION prevent_writes() RETURNS trigger AS $read_only_trigger$
BEGIN
    RAISE EXCEPTION 'Table % is currently read-only.', TG_TABLE_NAME;
END;
$read_only_trigger$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION prevent_updates() RETURNS trigger AS $constant_field_trigger$
DECLARE
    collection TEXT := TG_ARGV[0];
    constant_column TEXT := TG_ARGV[1];
    old_value TEXT := hstore(OLD) -> constant_column;
    new_value TEXT := hstore(NEW) -> constant_column;
BEGIN
    IF old_value IS DISTINCT FROM new_value THEN
        RAISE EXCEPTION 'Constant value constraint violated for %/%: % can not be updated.', collection, NEW.id, constant_column;
    END IF;
    RETURN NEW;
END;
$constant_field_trigger$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION raise_equality_exception_conditionally(check_column TEXT, ref_column TEXT, own_collection TEXT, own_id INTEGER, own_equal_val TEXT, foreign_collection TEXT, foreign_id INTEGER, foreign_equal_val TEXT)
RETURNS void AS $equality_exception$
DECLARE
    own_fqid TEXT;
    foreign_fqid TEXT;
BEGIN
    IF foreign_id IS NOT NULL AND own_id IS NOT NULL THEN
        IF foreign_equal_val IS DISTINCT FROM own_equal_val THEN
            foreign_fqid := foreign_collection || '/' || foreign_id;
            IF check_column = 'meeting_id' THEN
                RAISE EXCEPTION 'The following models do not belong to meeting %: [''%'']', own_equal_val, foreign_fqid;
            END IF;
            foreign_fqid := foreign_fqid  || '/' || check_column;
            own_fqid := own_collection || '/' || own_id || '/' || check_column;
            RAISE EXCEPTION 'The relation % requires the following fields to be equal:% %: % % %: %', ref_column, chr(10), own_fqid, own_equal_val, chr(10), foreign_fqid, foreign_equal_val;
        END IF;
    END IF;
END;
$equality_exception$ LANGUAGE plpgsql;

-- expects in this order:
-- * own table name,
-- * referenced table name,
-- * field in own table for which the check was triggered
-- * field that is supposed to be equal
-- * if new is the back relations table
CREATE OR REPLACE FUNCTION check_equals()
RETURNS trigger AS $check_equals_trigger$
DECLARE
    ref_column TEXT;
    check_column TEXT;
    foreign_collection TEXT;
    foreign_id INTEGER;
    foreign_equal_val TEXT;
    own_id INTEGER;
    own_equal_val TEXT;
    own_collection TEXT;
    from_back_relation BOOLEAN;
    i INTEGER := 0;
BEGIN

    WHILE i < TG_NARGS LOOP
        own_collection := TG_ARGV[i];
        foreign_collection := TG_ARGV[i+1];
        ref_column := TG_ARGV[i+2];
        check_column := TG_ARGV[i+3];
        from_back_relation := TG_ARGV[i+4];

        IF from_back_relation IS TRUE THEN
            EXECUTE format(
                'SELECT ($1).id, ($1).%I',
                check_column
            ) INTO foreign_id, foreign_equal_val USING NEW;
            EXECUTE format(
                'SELECT "id", %I
                FROM %I
                WHERE %I = %L',
                check_column,
                own_collection,
                ref_column,
                foreign_id
            ) INTO own_id, own_equal_val;
        ELSE
            EXECUTE format(
                'SELECT ($1).id, ($1).%I, ($1).%I',
                check_column,
                ref_column
            ) INTO own_id, own_equal_val, foreign_id USING NEW;
            EXECUTE format(
                'SELECT %I
                FROM %I
                WHERE "id" = %L',
                check_column,
                foreign_collection,
                foreign_id
            ) INTO foreign_equal_val;
        END IF;

        PERFORM raise_equality_exception_conditionally(
            check_column,
            ref_column,
            own_collection,
            own_id,
            own_equal_val,
            foreign_collection,
            foreign_id,
            foreign_equal_val
        );

        i := i + 5;
    END LOOP;

    RETURN NULL;  -- returning NULL because AFTER TRIGGER return value is ignored
END;
$check_equals_trigger$ LANGUAGE plpgsql;

-- expects in this order:
-- * intermediate table name,
-- * column referencing calling table in intermediate table
-- * calling table name
-- * column referencing other table in intermediate table
-- * other table name
-- * field that is supposed to be equal
-- * collection definitions-defined name for the relation on the side for which the check was triggered
CREATE OR REPLACE FUNCTION check_equals_multi()
RETURNS trigger AS $check_equals_multi_trigger$
DECLARE
    ref_column TEXT;
    check_column TEXT;
    foreign_collection_reference TEXT;
    foreign_collection TEXT;
    foreign_id INTEGER;
    foreign_equal_val TEXT;
    intermediate_table TEXT;
    own_id INTEGER;
    own_equal_val TEXT;
    own_collection_reference TEXT;
    own_collection TEXT;
    i INTEGER := 0;
    row record;
BEGIN

    WHILE i < TG_NARGS LOOP
        intermediate_table := TG_ARGV[i];
        own_collection_reference := TG_ARGV[i+1];
        own_collection := TG_ARGV[i+2];
        foreign_collection_reference := TG_ARGV[i+3];
        foreign_collection := TG_ARGV[i+4];
        check_column := TG_ARGV[i+5];
        ref_column := TG_ARGV[i+6];

        own_id = NEW.id;
        FOR row in EXECUTE format('
            SELECT a.%I AS a_val, c.id AS c_id, c.%I AS c_val
            FROM %I a
                JOIN %I b ON b.%I = a.id
                JOIN %I c ON b.%I = c.id
            WHERE a.id = %L',
            check_column,
            check_column,
            own_collection,
            intermediate_table,
            own_collection_reference,
            foreign_collection,
            foreign_collection_reference,
            own_id
        ) LOOP
            own_equal_val := row.a_val;
            foreign_id := row.c_id;
            foreign_equal_val := row.c_val;

            PERFORM raise_equality_exception_conditionally(
                check_column,
                ref_column,
                own_collection,
                own_id,
                own_equal_val,
                foreign_collection,
                foreign_id,
                foreign_equal_val
            );
        END LOOP;

        i := i + 7;
    END LOOP;

    RETURN NULL;  -- returning NULL because AFTER TRIGGER return value is ignored
END;
$check_equals_multi_trigger$ LANGUAGE plpgsql;

-- expects in this order:
-- * intermediate table name,
-- * column referencing table1 in intermediate table
-- * table1 name
-- * column referencing table2 in intermediate table
-- * table2 name
-- * field that is supposed to be equal
-- * collection definitions-defined name for the relation on the side for which the check was triggered
CREATE OR REPLACE FUNCTION check_equals_intermediate()
RETURNS trigger AS $check_equals_intermediate_trigger$
DECLARE
    ref_column TEXT;
    check_column TEXT;
    foreign_collection_reference TEXT;
    foreign_collection TEXT;
    foreign_id INTEGER;
    foreign_equal_val TEXT;
    own_id INTEGER;
    own_equal_val TEXT;
    own_collection_reference TEXT;
    own_collection TEXT;
    i INTEGER := 0;
BEGIN

    WHILE i < TG_NARGS LOOP
        own_collection_reference := TG_ARGV[i];
        own_collection := TG_ARGV[i+1];
        foreign_collection_reference := TG_ARGV[i+2];
        foreign_collection := TG_ARGV[i+3];
        check_column := TG_ARGV[i+4];
        ref_column := TG_ARGV[i+5];

        EXECUTE format(
            'SELECT id, %I
            FROM %I
            WHERE id = ($1).%I',
            check_column,
            own_collection,
            own_collection_reference
        ) INTO own_id, own_equal_val USING NEW;
        EXECUTE format(
            'SELECT id, %I
            FROM %I
            WHERE id = ($1).%I',
            check_column,
            foreign_collection,
            foreign_collection_reference
        ) INTO foreign_id, foreign_equal_val USING NEW;

        PERFORM raise_equality_exception_conditionally(
            check_column,
            ref_column,
            own_collection,
            own_id,
            own_equal_val,
            foreign_collection,
            foreign_id,
            foreign_equal_val
        );

        i := i + 6;
    END LOOP;

    RETURN NULL;  -- returning NULL because AFTER TRIGGER return value is ignored
END;
$check_equals_intermediate_trigger$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_equals_meeting_id_for_meeting()
RETURNS trigger AS $check_equals_meeting_id_for_meeting$
DECLARE
    table_name TEXT;
    ref_column TEXT;
    id INTEGER;
    meeting_id INTEGER;
    reference_id TEXT;
    i INTEGER := 0;
BEGIN
    WHILE i < TG_NARGS LOOP
        table_name := TG_ARGV[i];
        ref_column := TG_ARGV[i+1];
        EXECUTE format(
            'SELECT ($1).id, ($1).meeting_id, ($1).%I',
            ref_column
        ) INTO id, meeting_id, reference_id USING NEW;

        IF reference_id IS NOT NULL THEN
            PERFORM raise_equality_exception_conditionally(
                'meeting_id',
                ref_column,
                table_name,
                id,
                reference_id,
                'meeting',
                meeting_id,
                meeting_id::TEXT
            );
        END IF;

        i := i + 2;
    END LOOP;

    RETURN NULL;  -- returning NULL because AFTER TRIGGER return value is ignored
END;
$check_equals_meeting_id_for_meeting$ LANGUAGE plpgsql;


CREATE FUNCTION check_not_null_for_1_1() RETURNS trigger AS $not_null_trigger$
-- Parameters required for all operation types
--   0. own_collection – name of the view on which the trigger is defined
--   1. own_column – column in `own_table` referencing
--      `foreign_table`
--
-- Parameter needed for extended error message generation for 'UPDATE' and
-- 'DELETE' (can be empty on INSERT)
--   2. foreign_collection – name of collection of the triggered table that
--      will be used to SELECT
--   3. foreign_column – column in the foreign table referencing
--      `own_table`
DECLARE
    -- Parameters from TRIGGER DEFINITION
    -- Always required
    own_collection TEXT := TG_ARGV[0];
    own_column TEXT := TG_ARGV[1];

    -- Only for TG_OP in ('UPDATE', 'DELETE')
    foreign_collection TEXT := TG_ARGV[2];
    foreign_column TEXT := TG_ARGV[3];

    -- Calculated parameters
    own_id INTEGER;
    foreign_id INTEGER;
    counted INTEGER;
    error_message TEXT;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- in case of INSERT the view is checked on itself so the own id is applicable
        own_id := NEW.id;
    ELSE
        own_id := hstore(OLD) -> foreign_column;
        EXECUTE format('SELECT 1 FROM %I WHERE "id" = %L', own_collection, own_id) INTO counted;
        IF (counted IS NULL) THEN
            -- if the earlier referenced row was deleted (in the same transaction) we can quit.
            RETURN NULL;
        END IF;
    END IF;

    EXECUTE format('SELECT %I FROM %I WHERE id = %L', own_column, own_collection, own_id) INTO counted;
    IF (counted is NULL) THEN
        error_message := format('Trigger %s: NOT NULL CONSTRAINT VIOLATED for %s/%s/%s', TG_NAME, own_collection, own_id, own_column);
        IF TG_OP IN ('UPDATE', 'DELETE') THEN
            foreign_id := OLD.id;
            error_message := error_message || format(' from relationship before %s/%s/%s', foreign_collection, foreign_id, foreign_column);
        END IF;
        RAISE EXCEPTION '%', error_message;
    END IF;
    RETURN NULL;  -- returning NULL because AFTER TRIGGER return value is ignored
END;
$not_null_trigger$ language plpgsql;

CREATE FUNCTION check_not_null_for_1_n() RETURNS trigger AS $not_null_trigger$
-- Parameters required for all operation types
--   0. own_table – name of the table on which the trigger is defined
--   1. own_column – column in `own_table` referencing
--      `foreign_table`
--   2. foreign_table – name of the triggered table, that will be used to SELECT
--   3. foreign_column – column in the foreign table referencing
--      `own_table`
DECLARE
    -- Parameters from TRIGGER DEFINITION
    -- Always required
    own_table TEXT := TG_ARGV[0];
    own_column TEXT := TG_ARGV[1];
    foreign_table TEXT := TG_ARGV[2];
    foreign_column TEXT := TG_ARGV[3];

    -- Calculated parameters
    own_collection TEXT;
    foreign_collection TEXT;
    own_id INTEGER;
    foreign_id INTEGER;
    counted INTEGER;
    error_message TEXT;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- in case of INSERT the view is checked on itself so the own id is applicable
        own_id := NEW.id;
    ELSE
        own_id := hstore(OLD) -> foreign_column;
        EXECUTE format('SELECT 1 FROM %I WHERE "id" = %L', own_table, own_id) INTO counted;
        IF (counted IS NULL) THEN
            -- if the earlier referenced row was deleted (in the same transaction) we can quit.
            RETURN NULL;
        END IF;
    END IF;

    EXECUTE format('SELECT 1 FROM %I WHERE %I = %L', foreign_table, foreign_column, own_id) INTO counted;
    IF (counted is NULL) THEN
        own_collection := SUBSTRING(own_table FOR LENGTH(own_table) - 2);
        error_message := format('Trigger %s: NOT NULL CONSTRAINT VIOLATED for %s/%s/%s', TG_NAME, own_collection, own_id, own_column);
        IF TG_OP IN ('UPDATE', 'DELETE') THEN
            foreign_collection := SUBSTRING(foreign_table FOR LENGTH(foreign_table) - 2);
            foreign_id := OLD.id;
            error_message := error_message || format(' from relationship before %s/%s/%s', foreign_collection, foreign_id, foreign_column);
        END IF;
        RAISE EXCEPTION '%', error_message;
    END IF;
    RETURN NULL;  -- returning NULL because AFTER TRIGGER return value is ignored
END;
$not_null_trigger$ language plpgsql;

CREATE FUNCTION check_not_null_for_n_m() RETURNS trigger AS $not_null_trigger$
-- Parameters required for both INSERT and DELETE operations
--   0. intermediate_table_name – name of the n:m table
--   1. own_table – name of the table on which the trigger is defined
--   2. own_column – column in `own_table` referencing
--      `foreign_collection`
--   3. intermediate_table_own_key – column in the n:m table referencing
--      `own_table`
--
-- Parameters needed for extended error message generation for 'DELETE'
-- (can be empty on INSERT)
--   4. intermediate_table_foreign_key – column in the n:m table referencing
--      the foreign table
--   5. foreign_collection – name of the collection of the foreign table
--   6. foreign_column – column in the foreign table referencing
--      `own_collection`
DECLARE
    -- Parameters from TRIGGER DEFINITION
    -- Always required
    intermediate_table_name TEXT := TG_ARGV[0];
    own_table TEXT := TG_ARGV[1];
    own_column TEXT := TG_ARGV[2];
    intermediate_table_own_key TEXT := TG_ARGV[3];

    -- Only for TG_OP = 'DELETE'
    intermediate_table_foreign_key TEXT := TG_ARGV[4];
    foreign_collection TEXT := TG_ARGV[5];
    foreign_column TEXT := TG_ARGV[6];

    -- Calculated parameters
    own_collection TEXT;
    own_id INTEGER;
    foreign_id INTEGER;
    counted INTEGER;
    error_message TEXT;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- in case of INSERT the view is checked on itself so the own id is applicable
        own_id := NEW.id;
    ELSE
        own_id := hstore(OLD) -> intermediate_table_own_key;
        EXECUTE format('SELECT 1 FROM %I WHERE "id" = %L', own_table, own_id) INTO counted;
        IF (counted IS NULL) THEN
            -- if the earlier referenced row was deleted (in the same transaction) we can quit.
            RETURN NULL;
        END IF;
    END IF;

    EXECUTE format('SELECT 1 FROM %I WHERE %I = %L', intermediate_table_name, intermediate_table_own_key, own_id) INTO counted;
    IF (counted is NULL) THEN
        own_collection := SUBSTRING(own_table FOR LENGTH(own_table) - 2);
        error_message := format('Trigger %s: NOT NULL CONSTRAINT VIOLATED for %s/%s/%s', TG_NAME, own_collection, own_id, own_column);
        IF (TG_OP = 'DELETE') THEN
            foreign_id := hstore(OLD) -> intermediate_table_foreign_key;
            error_message := error_message || format(' from relationship before %s/%s/%s', foreign_collection, foreign_id, foreign_column);
        END IF;
        RAISE EXCEPTION '%', error_message;
    END IF;
    RETURN NULL;  -- returning NULL because AFTER TRIGGER return value is ignored
END;
$not_null_trigger$ language plpgsql;


-- Table definitions

CREATE TABLE action_worker_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_action_worker_name NOT NULL,
    state enum_action_worker_state
        CONSTRAINT required_action_worker_state NOT NULL,
    created timestamptz
        CONSTRAINT required_action_worker_created NOT NULL,
    timestamp timestamptz
        CONSTRAINT required_action_worker_timestamp NOT NULL,
    result jsonb,
    user_id integer
        CONSTRAINT required_action_worker_user_id NOT NULL
);



comment on column action_worker_t.user_id is 'Id of the calling user. If the action is called via internal route, the value will be -1.';


CREATE TABLE agenda_item_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    item_number varchar(256),
    comment varchar(256),
    closed boolean
        CONSTRAINT default_agenda_item_closed DEFAULT False,
    type enum_agenda_item_type
        CONSTRAINT default_agenda_item_type DEFAULT 'common',
    duration integer
        CONSTRAINT minimum_agenda_item_duration CHECK (duration >= 0),
    is_internal boolean,
    is_hidden boolean,
    level integer,
    weight integer,
    content_object_id varchar(100)
        CONSTRAINT required_agenda_item_content_object_id NOT NULL,
    content_object_id_motion_id integer
        CONSTRAINT unique_agenda_item_content_object_id_motion_id UNIQUE
        CONSTRAINT generated_always_as_agenda_item_content_object_id_motion_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'motion' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_motion_block_id integer
        CONSTRAINT unique_agenda_item_content_object_id_motion_block_id UNIQUE
        CONSTRAINT generated_always_as_agenda_item_content_object_id_motion6edbb3a GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'motion_block' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_assignment_id integer
        CONSTRAINT unique_agenda_item_content_object_id_assignment_id UNIQUE
        CONSTRAINT generated_always_as_agenda_item_content_object_id_assignment_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'assignment' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_topic_id integer
        CONSTRAINT unique_agenda_item_content_object_id_topic_id UNIQUE
        CONSTRAINT generated_always_as_agenda_item_content_object_id_topic_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'topic' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    CONSTRAINT valid_agenda_item_content_object_id_part1 CHECK (split_part(content_object_id, '/', 1) IN ('motion','motion_block','assignment','topic')),
    parent_id integer,
    meeting_id integer
        CONSTRAINT required_agenda_item_meeting_id NOT NULL
);



comment on column agenda_item_t.duration is 'Given in seconds';
comment on column agenda_item_t.is_internal is 'Calculated by the server';
comment on column agenda_item_t.is_hidden is 'Calculated by the server';
comment on column agenda_item_t.level is 'Calculated by the server';


CREATE TABLE assignment_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    title varchar(256)
        CONSTRAINT required_assignment_title NOT NULL,
    description text,
    open_posts integer
        CONSTRAINT minimum_assignment_open_posts CHECK (open_posts >= 0)
        CONSTRAINT default_assignment_open_posts DEFAULT 0,
    phase enum_assignment_phase
        CONSTRAINT default_assignment_phase DEFAULT 'search',
    default_poll_description text,
    number_poll_candidates boolean,
    sequential_number integer
        CONSTRAINT required_assignment_sequential_number NOT NULL,
    CONSTRAINT unique_assignment_sequential_number_meeting_id UNIQUE (sequential_number, meeting_id),
    meeting_id integer
        CONSTRAINT required_assignment_meeting_id NOT NULL
);



comment on column assignment_t.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE assignment_candidate_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    weight integer
        CONSTRAINT default_assignment_candidate_weight DEFAULT 10000,
    assignment_id integer
        CONSTRAINT required_assignment_candidate_assignment_id NOT NULL,
    meeting_user_id integer,
    meeting_id integer
        CONSTRAINT required_assignment_candidate_meeting_id NOT NULL
);




CREATE TABLE chat_group_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_chat_group_name NOT NULL,
    weight integer
        CONSTRAINT default_chat_group_weight DEFAULT 10000,
    meeting_id integer
        CONSTRAINT required_chat_group_meeting_id NOT NULL,
    CONSTRAINT unique_chat_group_meeting_id_name UNIQUE (meeting_id, name)
);




CREATE TABLE chat_message_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    content text
        CONSTRAINT required_chat_message_content NOT NULL,
    created timestamptz
        CONSTRAINT required_chat_message_created NOT NULL,
    meeting_user_id integer,
    chat_group_id integer
        CONSTRAINT required_chat_message_chat_group_id NOT NULL,
    meeting_id integer
        CONSTRAINT required_chat_message_meeting_id NOT NULL
);




CREATE TABLE committee_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_committee_name NOT NULL,
    description text,
    external_id varchar(256)
        CONSTRAINT unique_committee_external_id UNIQUE,
    default_meeting_id integer
        CONSTRAINT unique_committee_default_meeting_id UNIQUE,
    parent_id integer,
    organization_id integer
        CONSTRAINT required_committee_organization_id NOT NULL
        CONSTRAINT default_committee_organization_id DEFAULT 1
);




CREATE TABLE gender_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_gender_name NOT NULL
        CONSTRAINT unique_gender_name UNIQUE,
    organization_id integer
        CONSTRAINT required_gender_organization_id NOT NULL
        CONSTRAINT default_gender_organization_id DEFAULT 1
);




CREATE TABLE group_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    external_id varchar(256),
    name varchar(256)
        CONSTRAINT required_group_name NOT NULL,
    permissions enum_group_permissions[],
    weight integer,
    used_as_motion_poll_default_id integer,
    used_as_assignment_poll_default_id integer,
    used_as_topic_poll_default_id integer,
    used_as_poll_default_id integer,
    meeting_id integer
        CONSTRAINT required_group_meeting_id NOT NULL,
    CONSTRAINT unique_group_meeting_id_external_id UNIQUE (meeting_id, external_id)
);




CREATE TABLE history_entry_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    entries text[],
    original_model_id varchar(256),
    model_id varchar(100),
    model_id_user_id integer
        CONSTRAINT generated_always_as_history_entry_model_id_user_id GENERATED ALWAYS AS (CASE WHEN split_part(model_id, '/', 1) = 'user' THEN cast(split_part(model_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    model_id_motion_id integer
        CONSTRAINT generated_always_as_history_entry_model_id_motion_id GENERATED ALWAYS AS (CASE WHEN split_part(model_id, '/', 1) = 'motion' THEN cast(split_part(model_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    model_id_assignment_id integer
        CONSTRAINT generated_always_as_history_entry_model_id_assignment_id GENERATED ALWAYS AS (CASE WHEN split_part(model_id, '/', 1) = 'assignment' THEN cast(split_part(model_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    CONSTRAINT valid_history_entry_model_id_part1 CHECK (split_part(model_id, '/', 1) IN ('user','motion','assignment')),
    position_id integer
        CONSTRAINT required_history_entry_position_id NOT NULL,
    meeting_id integer
);




CREATE TABLE history_position_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    timestamp timestamptz,
    original_user_id integer,
    user_id integer
);




CREATE TABLE import_preview_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name enum_import_preview_name
        CONSTRAINT required_import_preview_name NOT NULL,
    state enum_import_preview_state
        CONSTRAINT required_import_preview_state NOT NULL,
    created timestamptz
        CONSTRAINT required_import_preview_created NOT NULL,
    result jsonb
);




CREATE TABLE list_of_speakers_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    closed boolean
        CONSTRAINT default_list_of_speakers_closed DEFAULT False,
    sequential_number integer
        CONSTRAINT required_list_of_speakers_sequential_number NOT NULL,
    CONSTRAINT unique_list_of_speakers_sequential_number_meeting_id UNIQUE (sequential_number, meeting_id),
    moderator_notes text,
    content_object_id varchar(100)
        CONSTRAINT required_list_of_speakers_content_object_id NOT NULL,
    content_object_id_motion_id integer
        CONSTRAINT unique_list_of_speakers_content_object_id_motion_id UNIQUE
        CONSTRAINT generated_always_as_list_of_speakers_content_object_id_m4822372 GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'motion' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_motion_block_id integer
        CONSTRAINT unique_list_of_speakers_content_object_id_motion_block_id UNIQUE
        CONSTRAINT generated_always_as_list_of_speakers_content_object_id_m50027ab GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'motion_block' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_assignment_id integer
        CONSTRAINT unique_list_of_speakers_content_object_id_assignment_id UNIQUE
        CONSTRAINT generated_always_as_list_of_speakers_content_object_id_abe56f76 GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'assignment' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_topic_id integer
        CONSTRAINT unique_list_of_speakers_content_object_id_topic_id UNIQUE
        CONSTRAINT generated_always_as_list_of_speakers_content_object_id_topic_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'topic' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_meeting_mediafile_id integer
        CONSTRAINT unique_list_of_speakers_content_object_id_meeting_mediafile_id UNIQUE
        CONSTRAINT generated_always_as_list_of_speakers_content_object_id_m07d8b8d GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'meeting_mediafile' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    CONSTRAINT valid_list_of_speakers_content_object_id_part1 CHECK (split_part(content_object_id, '/', 1) IN ('motion','motion_block','assignment','topic','meeting_mediafile')),
    meeting_id integer
        CONSTRAINT required_list_of_speakers_meeting_id NOT NULL
);



comment on column list_of_speakers_t.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE mediafile_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    title varchar(256)
        CONSTRAINT required_mediafile_title NOT NULL,
    is_directory boolean,
    filesize integer,
    filename varchar(256),
    mimetype varchar(256),
    pdf_information jsonb,
    create_timestamp timestamptz,
    token varchar(256)
        CONSTRAINT unique_mediafile_token UNIQUE,
    published_to_meetings_in_organization_id integer,
    parent_id integer,
    owner_id varchar(100)
        CONSTRAINT required_mediafile_owner_id NOT NULL,
    owner_id_meeting_id integer
        CONSTRAINT generated_always_as_mediafile_owner_id_meeting_id GENERATED ALWAYS AS (CASE WHEN split_part(owner_id, '/', 1) = 'meeting' THEN cast(split_part(owner_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    owner_id_organization_id integer
        CONSTRAINT generated_always_as_mediafile_owner_id_organization_id GENERATED ALWAYS AS (CASE WHEN split_part(owner_id, '/', 1) = 'organization' THEN cast(split_part(owner_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    CONSTRAINT valid_mediafile_owner_id_part1 CHECK (split_part(owner_id, '/', 1) IN ('meeting','organization')),
    CONSTRAINT unique_mediafile_title_parent_id_owner_id UNIQUE NULLS NOT DISTINCT (title, parent_id, owner_id)
);



comment on column mediafile_t.title is 'Title and parent_id must be unique.';
comment on column mediafile_t.filesize is 'In bytes, not the human readable format anymore.';
comment on column mediafile_t.filename is 'The uploaded filename. Will be used for downloading. Only writeable on create.';


CREATE TABLE meeting_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    external_id varchar(256)
        CONSTRAINT unique_meeting_external_id UNIQUE,
    welcome_title varchar(256)
        CONSTRAINT default_meeting_welcome_title DEFAULT 'Welcome to OpenSlides',
    welcome_text text
        CONSTRAINT default_meeting_welcome_text DEFAULT 'Space for your welcome text.',
    name varchar(200)
        CONSTRAINT required_meeting_name NOT NULL
        CONSTRAINT default_meeting_name DEFAULT 'OpenSlides',
    is_active_in_organization_id integer,
    is_archived_in_organization_id integer,
    description varchar(100),
    location varchar(256),
    time_zone text
        CONSTRAINT timezone_meeting_time_zone CHECK (is_timezone(time_zone)),
    start_time timestamptz,
    end_time timestamptz,
    locked_from_inside boolean,
    imported_at timestamptz,
    language enum_languages
        CONSTRAINT default_meeting_language DEFAULT 'en',
    jitsi_domain varchar(256),
    jitsi_room_name varchar(256),
    jitsi_room_password varchar(256),
    template_for_organization_id integer,
    enable_anonymous boolean
        CONSTRAINT default_meeting_enable_anonymous DEFAULT False,
    custom_translations jsonb,
    conference_show boolean
        CONSTRAINT default_meeting_conference_show DEFAULT False,
    conference_auto_connect boolean
        CONSTRAINT default_meeting_conference_auto_connect DEFAULT False,
    conference_los_restriction boolean
        CONSTRAINT default_meeting_conference_los_restriction DEFAULT True,
    conference_stream_url varchar(256),
    conference_stream_poster_url varchar(256),
    conference_open_microphone boolean
        CONSTRAINT default_meeting_conference_open_microphone DEFAULT False,
    conference_open_video boolean
        CONSTRAINT default_meeting_conference_open_video DEFAULT False,
    conference_auto_connect_next_speakers integer
        CONSTRAINT default_meeting_conference_auto_connect_next_speakers DEFAULT 0,
    conference_enable_helpdesk boolean
        CONSTRAINT default_meeting_conference_enable_helpdesk DEFAULT False,
    applause_enable boolean
        CONSTRAINT default_meeting_applause_enable DEFAULT False,
    applause_type enum_meeting_applause_type
        CONSTRAINT default_meeting_applause_type DEFAULT 'applause-type-bar',
    applause_show_level boolean
        CONSTRAINT default_meeting_applause_show_level DEFAULT False,
    applause_min_amount integer
        CONSTRAINT minimum_meeting_applause_min_amount CHECK (applause_min_amount >= 0)
        CONSTRAINT default_meeting_applause_min_amount DEFAULT 1,
    applause_max_amount integer
        CONSTRAINT minimum_meeting_applause_max_amount CHECK (applause_max_amount >= 0)
        CONSTRAINT default_meeting_applause_max_amount DEFAULT 0,
    applause_timeout integer
        CONSTRAINT minimum_meeting_applause_timeout CHECK (applause_timeout >= 0)
        CONSTRAINT default_meeting_applause_timeout DEFAULT 5,
    applause_particle_image_url varchar(256),
    projector_countdown_default_time integer
        CONSTRAINT required_meeting_projector_countdown_default_time NOT NULL
        CONSTRAINT default_meeting_projector_countdown_default_time DEFAULT 60,
    projector_countdown_warning_time integer
        CONSTRAINT required_meeting_projector_countdown_warning_time NOT NULL
        CONSTRAINT minimum_meeting_projector_countdown_warning_time CHECK (projector_countdown_warning_time >= 0)
        CONSTRAINT default_meeting_projector_countdown_warning_time DEFAULT 0,
    export_csv_encoding enum_meeting_export_csv_encoding
        CONSTRAINT default_meeting_export_csv_encoding DEFAULT 'utf-8',
    export_csv_separator varchar(256)
        CONSTRAINT default_meeting_export_csv_separator DEFAULT ';',
    export_pdf_pagenumber_alignment enum_meeting_export_pdf_pagenumber_alignment
        CONSTRAINT default_meeting_export_pdf_pagenumber_alignment DEFAULT 'center',
    export_pdf_fontsize integer
        CONSTRAINT minimum_meeting_export_pdf_fontsize CHECK (export_pdf_fontsize >= 10)
        CONSTRAINT maximum_meeting_export_pdf_fontsize CHECK (export_pdf_fontsize <= 12)
        CONSTRAINT default_meeting_export_pdf_fontsize DEFAULT 10,
    export_pdf_line_height double precision
        CONSTRAINT minimum_meeting_export_pdf_line_height CHECK (export_pdf_line_height >= 1.0)
        CONSTRAINT default_meeting_export_pdf_line_height DEFAULT 1.25,
    export_pdf_page_margin_left integer
        CONSTRAINT minimum_meeting_export_pdf_page_margin_left CHECK (export_pdf_page_margin_left >= 0)
        CONSTRAINT default_meeting_export_pdf_page_margin_left DEFAULT 20,
    export_pdf_page_margin_top integer
        CONSTRAINT minimum_meeting_export_pdf_page_margin_top CHECK (export_pdf_page_margin_top >= 0)
        CONSTRAINT default_meeting_export_pdf_page_margin_top DEFAULT 25,
    export_pdf_page_margin_right integer
        CONSTRAINT minimum_meeting_export_pdf_page_margin_right CHECK (export_pdf_page_margin_right >= 0)
        CONSTRAINT default_meeting_export_pdf_page_margin_right DEFAULT 20,
    export_pdf_page_margin_bottom integer
        CONSTRAINT minimum_meeting_export_pdf_page_margin_bottom CHECK (export_pdf_page_margin_bottom >= 0)
        CONSTRAINT default_meeting_export_pdf_page_margin_bottom DEFAULT 20,
    export_pdf_pagesize enum_meeting_export_pdf_pagesize
        CONSTRAINT default_meeting_export_pdf_pagesize DEFAULT 'A4',
    agenda_show_subtitles boolean
        CONSTRAINT default_meeting_agenda_show_subtitles DEFAULT False,
    agenda_enable_numbering boolean
        CONSTRAINT default_meeting_agenda_enable_numbering DEFAULT True,
    agenda_number_prefix varchar(20),
    agenda_numeral_system enum_meeting_agenda_numeral_system
        CONSTRAINT default_meeting_agenda_numeral_system DEFAULT 'arabic',
    agenda_item_creation enum_meeting_agenda_item_creation
        CONSTRAINT default_meeting_agenda_item_creation DEFAULT 'default_no',
    agenda_new_items_default_visibility enum_meeting_agenda_new_items_default_visibility
        CONSTRAINT default_meeting_agenda_new_items_default_visibility DEFAULT 'internal',
    agenda_show_internal_items_on_projector boolean
        CONSTRAINT default_meeting_agenda_show_internal_items_on_projector DEFAULT False,
    agenda_show_topic_navigation_on_detail_view boolean
        CONSTRAINT default_meeting_agenda_show_topic_navigation_on_detail_view DEFAULT False,
    list_of_speakers_amount_last_on_projector integer
        CONSTRAINT minimum_meeting_list_of_speakers_amount_last_on_projector CHECK (list_of_speakers_amount_last_on_projector >= -1)
        CONSTRAINT default_meeting_list_of_speakers_amount_last_on_projector DEFAULT 0,
    list_of_speakers_amount_next_on_projector integer
        CONSTRAINT minimum_meeting_list_of_speakers_amount_next_on_projector CHECK (list_of_speakers_amount_next_on_projector >= -1)
        CONSTRAINT default_meeting_list_of_speakers_amount_next_on_projector DEFAULT -1,
    list_of_speakers_couple_countdown boolean
        CONSTRAINT default_meeting_list_of_speakers_couple_countdown DEFAULT True,
    list_of_speakers_show_amount_of_speakers_on_slide boolean
        CONSTRAINT default_meeting_list_of_speakers_show_amount_of_speakersebf4b44 DEFAULT True,
    list_of_speakers_present_users_only boolean
        CONSTRAINT default_meeting_list_of_speakers_present_users_only DEFAULT False,
    list_of_speakers_show_first_contribution boolean
        CONSTRAINT default_meeting_list_of_speakers_show_first_contribution DEFAULT False,
    list_of_speakers_hide_contribution_count boolean
        CONSTRAINT default_meeting_list_of_speakers_hide_contribution_count DEFAULT False,
    list_of_speakers_allow_multiple_speakers boolean
        CONSTRAINT default_meeting_list_of_speakers_allow_multiple_speakers DEFAULT False,
    list_of_speakers_enable_point_of_order_speakers boolean
        CONSTRAINT default_meeting_list_of_speakers_enable_point_of_order_speakers DEFAULT True,
    list_of_speakers_can_create_point_of_order_for_others boolean
        CONSTRAINT default_meeting_list_of_speakers_can_create_point_of_ord50d63fe DEFAULT False,
    list_of_speakers_enable_point_of_order_categories boolean
        CONSTRAINT default_meeting_list_of_speakers_enable_point_of_order_c1167331 DEFAULT False,
    list_of_speakers_closing_disables_point_of_order boolean
        CONSTRAINT default_meeting_list_of_speakers_closing_disables_point_c59619b DEFAULT False,
    list_of_speakers_enable_pro_contra_speech boolean
        CONSTRAINT default_meeting_list_of_speakers_enable_pro_contra_speech DEFAULT False,
    list_of_speakers_can_set_contribution_self boolean
        CONSTRAINT default_meeting_list_of_speakers_can_set_contribution_self DEFAULT False,
    list_of_speakers_speaker_note_for_everyone boolean
        CONSTRAINT default_meeting_list_of_speakers_speaker_note_for_everyone DEFAULT True,
    list_of_speakers_initially_closed boolean
        CONSTRAINT default_meeting_list_of_speakers_initially_closed DEFAULT False,
    list_of_speakers_default_structure_level_time integer
        CONSTRAINT minimum_meeting_list_of_speakers_default_structure_level_time CHECK (list_of_speakers_default_structure_level_time >= 0),
    list_of_speakers_enable_interposed_question boolean,
    list_of_speakers_intervention_time integer,
    motions_default_workflow_id integer
        CONSTRAINT required_meeting_motions_default_workflow_id NOT NULL
        CONSTRAINT unique_meeting_motions_default_workflow_id UNIQUE,
    motions_default_amendment_workflow_id integer
        CONSTRAINT required_meeting_motions_default_amendment_workflow_id NOT NULL
        CONSTRAINT unique_meeting_motions_default_amendment_workflow_id UNIQUE,
    motions_preamble text
        CONSTRAINT default_meeting_motions_preamble DEFAULT 'The assembly may decide:',
    motions_default_line_numbering enum_meeting_motions_default_line_numbering
        CONSTRAINT default_meeting_motions_default_line_numbering DEFAULT 'outside',
    motions_line_length integer
        CONSTRAINT minimum_meeting_motions_line_length CHECK (motions_line_length >= 40)
        CONSTRAINT default_meeting_motions_line_length DEFAULT 85,
    motions_reason_required boolean
        CONSTRAINT default_meeting_motions_reason_required DEFAULT False,
    motions_origin_motion_toggle_default boolean
        CONSTRAINT default_meeting_motions_origin_motion_toggle_default DEFAULT False,
    motions_enable_origin_motion_display boolean
        CONSTRAINT default_meeting_motions_enable_origin_motion_display DEFAULT False,
    motions_enable_text_on_projector boolean
        CONSTRAINT default_meeting_motions_enable_text_on_projector DEFAULT True,
    motions_enable_reason_on_projector boolean
        CONSTRAINT default_meeting_motions_enable_reason_on_projector DEFAULT False,
    motions_enable_sidebox_on_projector boolean
        CONSTRAINT default_meeting_motions_enable_sidebox_on_projector DEFAULT False,
    motions_enable_recommendation_on_projector boolean
        CONSTRAINT default_meeting_motions_enable_recommendation_on_projector DEFAULT True,
    motions_hide_metadata_background boolean
        CONSTRAINT default_meeting_motions_hide_metadata_background DEFAULT False,
    motions_show_referring_motions boolean
        CONSTRAINT default_meeting_motions_show_referring_motions DEFAULT True,
    motions_show_sequential_number boolean
        CONSTRAINT default_meeting_motions_show_sequential_number DEFAULT True,
    motions_create_enable_additional_submitter_text boolean,
    motions_recommendations_by varchar(256),
    motions_block_slide_columns integer
        CONSTRAINT minimum_meeting_motions_block_slide_columns CHECK (motions_block_slide_columns >= 1),
    motions_recommendation_text_mode enum_meeting_motions_recommendation_text_mode
        CONSTRAINT default_meeting_motions_recommendation_text_mode DEFAULT 'diff',
    motions_default_sorting enum_meeting_motions_default_sorting
        CONSTRAINT default_meeting_motions_default_sorting DEFAULT 'number',
    motions_number_type enum_meeting_motions_number_type
        CONSTRAINT default_meeting_motions_number_type DEFAULT 'per_category',
    motions_number_min_digits integer
        CONSTRAINT default_meeting_motions_number_min_digits DEFAULT 2,
    motions_number_with_blank boolean
        CONSTRAINT default_meeting_motions_number_with_blank DEFAULT False,
    motions_amendments_enabled boolean
        CONSTRAINT default_meeting_motions_amendments_enabled DEFAULT True,
    motions_amendments_in_main_list boolean
        CONSTRAINT default_meeting_motions_amendments_in_main_list DEFAULT True,
    motions_amendments_of_amendments boolean
        CONSTRAINT default_meeting_motions_amendments_of_amendments DEFAULT False,
    motions_amendments_prefix varchar(256)
        CONSTRAINT default_meeting_motions_amendments_prefix DEFAULT '-Ä',
    motions_amendments_text_mode enum_meeting_motions_amendments_text_mode
        CONSTRAINT default_meeting_motions_amendments_text_mode DEFAULT 'paragraph',
    motions_amendments_multiple_paragraphs boolean
        CONSTRAINT default_meeting_motions_amendments_multiple_paragraphs DEFAULT True,
    motions_supporters_min_amount integer
        CONSTRAINT minimum_meeting_motions_supporters_min_amount CHECK (motions_supporters_min_amount >= 0)
        CONSTRAINT default_meeting_motions_supporters_min_amount DEFAULT 0,
    motions_enable_editor boolean,
    motions_enable_working_group_speaker boolean,
    motions_export_title varchar(256)
        CONSTRAINT default_meeting_motions_export_title DEFAULT 'Motions',
    motions_export_preamble text,
    motions_export_submitter_recommendation boolean
        CONSTRAINT default_meeting_motions_export_submitter_recommendation DEFAULT True,
    motions_export_follow_recommendation boolean
        CONSTRAINT default_meeting_motions_export_follow_recommendation DEFAULT False,
    motions_enable_restricted_editor_for_manager boolean,
    motions_enable_restricted_editor_for_non_manager boolean,
    motion_poll_ballot_paper_selection enum_ballot_paper_selection
        CONSTRAINT default_meeting_motion_poll_ballot_paper_selection DEFAULT 'CUSTOM_NUMBER',
    motion_poll_ballot_paper_number integer
        CONSTRAINT default_meeting_motion_poll_ballot_paper_number DEFAULT 8,
    motion_poll_default_type varchar(256)
        CONSTRAINT default_meeting_motion_poll_default_type DEFAULT 'pseudoanonymous',
    motion_poll_default_method varchar(256)
        CONSTRAINT default_meeting_motion_poll_default_method DEFAULT 'YNA',
    motion_poll_default_onehundred_percent_base enum_onehundred_percent_bases
        CONSTRAINT default_meeting_motion_poll_default_onehundred_percent_base DEFAULT 'YNA',
    motion_poll_default_backend enum_poll_backends
        CONSTRAINT default_meeting_motion_poll_default_backend DEFAULT 'fast',
    motion_poll_projection_name_order_first enum_meeting_motion_poll_projection_name_order_first
        CONSTRAINT required_meeting_motion_poll_projection_name_order_first NOT NULL
        CONSTRAINT default_meeting_motion_poll_projection_name_order_first DEFAULT 'last_name',
    motion_poll_projection_max_columns integer
        CONSTRAINT required_meeting_motion_poll_projection_max_columns NOT NULL
        CONSTRAINT default_meeting_motion_poll_projection_max_columns DEFAULT 6,
    users_enable_presence_view boolean
        CONSTRAINT default_meeting_users_enable_presence_view DEFAULT False,
    users_enable_vote_weight boolean
        CONSTRAINT default_meeting_users_enable_vote_weight DEFAULT False,
    users_allow_self_set_present boolean
        CONSTRAINT default_meeting_users_allow_self_set_present DEFAULT True,
    users_pdf_welcometitle varchar(256)
        CONSTRAINT default_meeting_users_pdf_welcometitle DEFAULT 'Welcome to OpenSlides',
    users_pdf_welcometext text
        CONSTRAINT default_meeting_users_pdf_welcometext DEFAULT '[Place for your welcome and help text.]',
    users_pdf_wlan_ssid varchar(256),
    users_pdf_wlan_password varchar(256),
    users_pdf_wlan_encryption enum_meeting_users_pdf_wlan_encryption
        CONSTRAINT default_meeting_users_pdf_wlan_encryption DEFAULT 'WPA',
    users_email_sender varchar(256)
        CONSTRAINT default_meeting_users_email_sender DEFAULT 'OpenSlides',
    users_email_replyto varchar(256),
    users_email_subject varchar(256)
        CONSTRAINT default_meeting_users_email_subject DEFAULT 'OpenSlides access data',
    users_email_body text
        CONSTRAINT default_meeting_users_email_body DEFAULT 'Dear {name},

this is your personal OpenSlides login:

{url}
Username: {username}
Password: {password}


This email was generated automatically.',
    users_enable_vote_delegations boolean,
    users_forbid_delegator_in_list_of_speakers boolean,
    users_forbid_delegator_as_submitter boolean,
    users_forbid_delegator_as_supporter boolean,
    users_forbid_delegator_to_vote boolean,
    assignments_export_title varchar(256)
        CONSTRAINT default_meeting_assignments_export_title DEFAULT 'Elections',
    assignments_export_preamble text,
    assignment_poll_ballot_paper_selection enum_ballot_paper_selection
        CONSTRAINT default_meeting_assignment_poll_ballot_paper_selection DEFAULT 'CUSTOM_NUMBER',
    assignment_poll_ballot_paper_number integer
        CONSTRAINT default_meeting_assignment_poll_ballot_paper_number DEFAULT 8,
    assignment_poll_add_candidates_to_list_of_speakers boolean
        CONSTRAINT default_meeting_assignment_poll_add_candidates_to_list_od04213d DEFAULT False,
    assignment_poll_enable_max_votes_per_option boolean
        CONSTRAINT default_meeting_assignment_poll_enable_max_votes_per_option DEFAULT False,
    assignment_poll_sort_poll_result_by_votes boolean
        CONSTRAINT default_meeting_assignment_poll_sort_poll_result_by_votes DEFAULT True,
    assignment_poll_default_type varchar(256)
        CONSTRAINT default_meeting_assignment_poll_default_type DEFAULT 'pseudoanonymous',
    assignment_poll_default_method varchar(256)
        CONSTRAINT default_meeting_assignment_poll_default_method DEFAULT 'Y',
    assignment_poll_default_onehundred_percent_base enum_onehundred_percent_bases
        CONSTRAINT default_meeting_assignment_poll_default_onehundred_percent_base DEFAULT 'valid',
    assignment_poll_default_backend enum_poll_backends
        CONSTRAINT default_meeting_assignment_poll_default_backend DEFAULT 'fast',
    poll_ballot_paper_selection enum_ballot_paper_selection,
    poll_ballot_paper_number integer,
    poll_sort_poll_result_by_votes boolean,
    poll_default_type varchar(256)
        CONSTRAINT default_meeting_poll_default_type DEFAULT 'analog',
    poll_default_method varchar(256),
    poll_default_onehundred_percent_base enum_onehundred_percent_bases
        CONSTRAINT default_meeting_poll_default_onehundred_percent_base DEFAULT 'YNA',
    poll_default_backend enum_poll_backends
        CONSTRAINT default_meeting_poll_default_backend DEFAULT 'fast',
    poll_default_live_voting_enabled boolean
        CONSTRAINT default_meeting_poll_default_live_voting_enabled DEFAULT False,
    poll_couple_countdown boolean
        CONSTRAINT default_meeting_poll_couple_countdown DEFAULT True,
    logo_projector_main_id integer
        CONSTRAINT unique_meeting_logo_projector_main_id UNIQUE,
    logo_projector_header_id integer
        CONSTRAINT unique_meeting_logo_projector_header_id UNIQUE,
    logo_web_header_id integer
        CONSTRAINT unique_meeting_logo_web_header_id UNIQUE,
    logo_pdf_header_l_id integer
        CONSTRAINT unique_meeting_logo_pdf_header_l_id UNIQUE,
    logo_pdf_header_r_id integer
        CONSTRAINT unique_meeting_logo_pdf_header_r_id UNIQUE,
    logo_pdf_footer_l_id integer
        CONSTRAINT unique_meeting_logo_pdf_footer_l_id UNIQUE,
    logo_pdf_footer_r_id integer
        CONSTRAINT unique_meeting_logo_pdf_footer_r_id UNIQUE,
    logo_pdf_ballot_paper_id integer
        CONSTRAINT unique_meeting_logo_pdf_ballot_paper_id UNIQUE,
    font_regular_id integer
        CONSTRAINT unique_meeting_font_regular_id UNIQUE,
    font_italic_id integer
        CONSTRAINT unique_meeting_font_italic_id UNIQUE,
    font_bold_id integer
        CONSTRAINT unique_meeting_font_bold_id UNIQUE,
    font_bold_italic_id integer
        CONSTRAINT unique_meeting_font_bold_italic_id UNIQUE,
    font_monospace_id integer
        CONSTRAINT unique_meeting_font_monospace_id UNIQUE,
    font_chyron_speaker_name_id integer
        CONSTRAINT unique_meeting_font_chyron_speaker_name_id UNIQUE,
    font_projector_h1_id integer
        CONSTRAINT unique_meeting_font_projector_h1_id UNIQUE,
    font_projector_h2_id integer
        CONSTRAINT unique_meeting_font_projector_h2_id UNIQUE,
    committee_id integer
        CONSTRAINT required_meeting_committee_id NOT NULL,
    reference_projector_id integer
        CONSTRAINT required_meeting_reference_projector_id NOT NULL
        CONSTRAINT unique_meeting_reference_projector_id UNIQUE,
    list_of_speakers_countdown_id integer
        CONSTRAINT unique_meeting_list_of_speakers_countdown_id UNIQUE,
    poll_countdown_id integer
        CONSTRAINT unique_meeting_poll_countdown_id UNIQUE,
    default_group_id integer
        CONSTRAINT required_meeting_default_group_id NOT NULL
        CONSTRAINT unique_meeting_default_group_id UNIQUE,
    admin_group_id integer
        CONSTRAINT unique_meeting_admin_group_id UNIQUE,
    anonymous_group_id integer
        CONSTRAINT unique_meeting_anonymous_group_id UNIQUE
);



comment on column meeting_t.is_active_in_organization_id is 'Backrelation and boolean flag at once';
comment on column meeting_t.is_archived_in_organization_id is 'Backrelation and boolean flag at once';
comment on column meeting_t.list_of_speakers_default_structure_level_time is '0 disables structure level countdowns.';
comment on column meeting_t.list_of_speakers_intervention_time is '0 disables intervention speakers.';
comment on column meeting_t.poll_default_live_voting_enabled is 'Defines default "poll.live_voting_enabled" option suggested to user. Is not used in the validations.';


CREATE TABLE meeting_mediafile_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    mediafile_id integer
        CONSTRAINT required_meeting_mediafile_mediafile_id NOT NULL,
    meeting_id integer
        CONSTRAINT required_meeting_mediafile_meeting_id NOT NULL,
    is_public boolean
        CONSTRAINT required_meeting_mediafile_is_public NOT NULL,
    CONSTRAINT unique_meeting_mediafile_mediafile_id_meeting_id UNIQUE (mediafile_id, meeting_id)
);



comment on column meeting_mediafile_t.is_public is 'Calculated in actions. Used to discern whether the (meeting-)mediafile can be seen by everyone, because, in the case of inherited_access_group_ids == [], it would otherwise not be clear. inherited_access_group_ids == [] can have two causes: cancelling access groups (=> is_public := false) or no access groups at all (=> is_public := true)';


CREATE TABLE meeting_user_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    comment text,
    number varchar(256),
    about_me text,
    vote_weight decimal(16,6)
        CONSTRAINT minimum_meeting_user_vote_weight CHECK (vote_weight >= 0.000001),
    locked_out boolean,
    user_id integer
        CONSTRAINT required_meeting_user_user_id NOT NULL,
    meeting_id integer
        CONSTRAINT required_meeting_user_meeting_id NOT NULL,
    vote_delegated_to_id integer,
    CONSTRAINT unique_meeting_user_meeting_id_user_id UNIQUE (meeting_id, user_id)
);




CREATE TABLE motion_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    number varchar(256),
    number_value integer,
    sequential_number integer
        CONSTRAINT required_motion_sequential_number NOT NULL,
    CONSTRAINT unique_motion_sequential_number_meeting_id UNIQUE (sequential_number, meeting_id),
    title varchar(256)
        CONSTRAINT required_motion_title NOT NULL,
    diff_version varchar(256),
    text text,
    text_hash varchar(256),
    amendment_paragraphs jsonb,
    modified_final_version text,
    reason text,
    category_weight integer
        CONSTRAINT default_motion_category_weight DEFAULT 10000,
    state_extension varchar(256),
    recommendation_extension varchar(256),
    sort_weight integer
        CONSTRAINT default_motion_sort_weight DEFAULT 10000,
    created timestamptz,
    last_modified timestamptz,
    workflow_timestamp timestamptz,
    start_line_number integer
        CONSTRAINT minimum_motion_start_line_number CHECK (start_line_number >= 1)
        CONSTRAINT default_motion_start_line_number DEFAULT 1,
    forwarded timestamptz,
    additional_submitter varchar(256),
    marked_forwarded boolean,
    lead_motion_id integer,
    sort_parent_id integer,
    origin_id integer,
    origin_meeting_id integer,
    state_id integer
        CONSTRAINT required_motion_state_id NOT NULL,
    recommendation_id integer,
    category_id integer,
    block_id integer,
    meeting_id integer
        CONSTRAINT required_motion_meeting_id NOT NULL,
    CONSTRAINT unique_motion_meeting_id_number UNIQUE (meeting_id, number)
);



comment on column motion_t.number_value is 'The number value of this motion. This number is auto-generated and read-only.';
comment on column motion_t.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';
comment on column motion_t.marked_forwarded is 'Forwarded amendments can be marked as such. This is just optional, however. Forwarded amendments can also have this field set to false.';


CREATE TABLE motion_block_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    title varchar(256)
        CONSTRAINT required_motion_block_title NOT NULL,
    internal boolean,
    sequential_number integer
        CONSTRAINT required_motion_block_sequential_number NOT NULL,
    CONSTRAINT unique_motion_block_sequential_number_meeting_id UNIQUE (sequential_number, meeting_id),
    meeting_id integer
        CONSTRAINT required_motion_block_meeting_id NOT NULL
);



comment on column motion_block_t.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE motion_category_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_motion_category_name NOT NULL,
    prefix varchar(256),
    weight integer
        CONSTRAINT default_motion_category_weight DEFAULT 10000,
    level integer,
    sequential_number integer
        CONSTRAINT required_motion_category_sequential_number NOT NULL,
    CONSTRAINT unique_motion_category_sequential_number_meeting_id UNIQUE (sequential_number, meeting_id),
    parent_id integer,
    meeting_id integer
        CONSTRAINT required_motion_category_meeting_id NOT NULL
);



comment on column motion_category_t.level is 'Calculated field.';
comment on column motion_category_t.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE motion_change_recommendation_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    rejected boolean
        CONSTRAINT default_motion_change_recommendation_rejected DEFAULT False,
    internal boolean
        CONSTRAINT default_motion_change_recommendation_internal DEFAULT False,
    type enum_motion_change_recommendation_type
        CONSTRAINT default_motion_change_recommendation_type DEFAULT 'replacement',
    other_description varchar(256),
    line_from integer
        CONSTRAINT required_motion_change_recommendation_line_from NOT NULL
        CONSTRAINT minimum_motion_change_recommendation_line_from CHECK (line_from >= 0),
    line_to integer
        CONSTRAINT required_motion_change_recommendation_line_to NOT NULL
        CONSTRAINT minimum_motion_change_recommendation_line_to CHECK (line_to >= 0),
    text text,
    creation_time timestamptz,
    motion_id integer
        CONSTRAINT required_motion_change_recommendation_motion_id NOT NULL,
    meeting_id integer
        CONSTRAINT required_motion_change_recommendation_meeting_id NOT NULL
);




CREATE TABLE motion_comment_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    comment text
        CONSTRAINT required_motion_comment_comment NOT NULL,
    motion_id integer
        CONSTRAINT required_motion_comment_motion_id NOT NULL,
    section_id integer
        CONSTRAINT required_motion_comment_section_id NOT NULL,
    meeting_id integer
        CONSTRAINT required_motion_comment_meeting_id NOT NULL,
    CONSTRAINT unique_motion_comment_motion_id_section_id UNIQUE (motion_id, section_id)
);




CREATE TABLE motion_comment_section_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_motion_comment_section_name NOT NULL,
    weight integer
        CONSTRAINT default_motion_comment_section_weight DEFAULT 10000,
    sequential_number integer
        CONSTRAINT required_motion_comment_section_sequential_number NOT NULL,
    CONSTRAINT unique_motion_comment_section_sequential_number_meeting_id UNIQUE (sequential_number, meeting_id),
    submitter_can_write boolean,
    meeting_id integer
        CONSTRAINT required_motion_comment_section_meeting_id NOT NULL
);



comment on column motion_comment_section_t.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE motion_editor_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    weight integer,
    meeting_user_id integer,
    motion_id integer
        CONSTRAINT required_motion_editor_motion_id NOT NULL,
    meeting_id integer
        CONSTRAINT required_motion_editor_meeting_id NOT NULL,
    CONSTRAINT unique_motion_editor_meeting_user_id_motion_id UNIQUE (meeting_user_id, motion_id)
);




CREATE TABLE motion_state_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_motion_state_name NOT NULL,
    weight integer
        CONSTRAINT required_motion_state_weight NOT NULL,
    recommendation_label varchar(256),
    is_internal boolean,
    css_class enum_motion_state_css_class
        CONSTRAINT required_motion_state_css_class NOT NULL
        CONSTRAINT default_motion_state_css_class DEFAULT 'lightblue',
    restrictions enum_motion_state_restrictions[]
        CONSTRAINT default_motion_state_restrictions DEFAULT '{}',
    allow_support boolean
        CONSTRAINT default_motion_state_allow_support DEFAULT False,
    allow_create_poll boolean
        CONSTRAINT default_motion_state_allow_create_poll DEFAULT False,
    allow_submitter_edit boolean
        CONSTRAINT default_motion_state_allow_submitter_edit DEFAULT False,
    set_number boolean
        CONSTRAINT default_motion_state_set_number DEFAULT True,
    show_state_extension_field boolean
        CONSTRAINT default_motion_state_show_state_extension_field DEFAULT False,
    show_recommendation_extension_field boolean
        CONSTRAINT default_motion_state_show_recommendation_extension_field DEFAULT False,
    merge_amendment_into_final enum_motion_state_merge_amendment_into_final
        CONSTRAINT default_motion_state_merge_amendment_into_final DEFAULT 'undefined',
    allow_motion_forwarding boolean
        CONSTRAINT default_motion_state_allow_motion_forwarding DEFAULT False,
    allow_amendment_forwarding boolean,
    set_workflow_timestamp boolean
        CONSTRAINT default_motion_state_set_workflow_timestamp DEFAULT False,
    state_button_label varchar(256),
    submitter_withdraw_state_id integer,
    workflow_id integer
        CONSTRAINT required_motion_state_workflow_id NOT NULL,
    meeting_id integer
        CONSTRAINT required_motion_state_meeting_id NOT NULL,
    CONSTRAINT unique_motion_state_name_workflow_id UNIQUE (name, workflow_id)
);




CREATE TABLE motion_submitter_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    weight integer,
    meeting_user_id integer,
    motion_id integer
        CONSTRAINT required_motion_submitter_motion_id NOT NULL,
    meeting_id integer
        CONSTRAINT required_motion_submitter_meeting_id NOT NULL,
    CONSTRAINT unique_motion_submitter_meeting_user_id_motion_id UNIQUE (meeting_user_id, motion_id)
);




CREATE TABLE motion_supporter_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    meeting_user_id integer,
    motion_id integer
        CONSTRAINT required_motion_supporter_motion_id NOT NULL,
    meeting_id integer
        CONSTRAINT required_motion_supporter_meeting_id NOT NULL,
    CONSTRAINT unique_motion_supporter_meeting_user_id_motion_id UNIQUE (meeting_user_id, motion_id)
);




CREATE TABLE motion_workflow_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_motion_workflow_name NOT NULL,
    sequential_number integer
        CONSTRAINT required_motion_workflow_sequential_number NOT NULL,
    CONSTRAINT unique_motion_workflow_sequential_number_meeting_id UNIQUE (sequential_number, meeting_id),
    first_state_id integer
        CONSTRAINT required_motion_workflow_first_state_id NOT NULL
        CONSTRAINT unique_motion_workflow_first_state_id UNIQUE,
    meeting_id integer
        CONSTRAINT required_motion_workflow_meeting_id NOT NULL
);



comment on column motion_workflow_t.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE motion_working_group_speaker_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    weight integer,
    meeting_user_id integer,
    motion_id integer
        CONSTRAINT required_motion_working_group_speaker_motion_id NOT NULL,
    meeting_id integer
        CONSTRAINT required_motion_working_group_speaker_meeting_id NOT NULL,
    CONSTRAINT unique_motion_working_group_speaker_meeting_user_id_motion_id UNIQUE (meeting_user_id, motion_id)
);




CREATE TABLE option_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    weight integer
        CONSTRAINT default_option_weight DEFAULT 10000,
    text text,
    yes decimal(16,6),
    no decimal(16,6),
    abstain decimal(16,6),
    poll_id integer,
    content_object_id varchar(100),
    content_object_id_motion_id integer
        CONSTRAINT generated_always_as_option_content_object_id_motion_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'motion' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_user_id integer
        CONSTRAINT generated_always_as_option_content_object_id_user_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'user' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_poll_candidate_list_id integer
        CONSTRAINT unique_option_content_object_id_poll_candidate_list_id UNIQUE
        CONSTRAINT generated_always_as_option_content_object_id_poll_candidd7449d9 GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'poll_candidate_list' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    CONSTRAINT valid_option_content_object_id_part1 CHECK (split_part(content_object_id, '/', 1) IN ('motion','user','poll_candidate_list')),
    meeting_id integer
        CONSTRAINT required_option_meeting_id NOT NULL,
    CONSTRAINT unique_option_content_object_id_poll_id UNIQUE (content_object_id, poll_id)
);




CREATE TABLE organization_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256),
    description text,
    legal_notice text,
    privacy_policy text,
    login_text text,
    reset_password_verbose_errors boolean,
    disable_forward_with_attachments boolean,
    restrict_edit_forward_committees boolean,
    enable_electronic_voting boolean,
    enable_chat boolean,
    limit_of_meetings integer
        CONSTRAINT minimum_organization_limit_of_meetings CHECK (limit_of_meetings >= 0)
        CONSTRAINT default_organization_limit_of_meetings DEFAULT 0,
    limit_of_users integer
        CONSTRAINT minimum_organization_limit_of_users CHECK (limit_of_users >= 0)
        CONSTRAINT default_organization_limit_of_users DEFAULT 0,
    default_language enum_languages
        CONSTRAINT default_organization_default_language DEFAULT 'en',
    time_zone text
        CONSTRAINT timezone_organization_time_zone CHECK (is_timezone(time_zone)),
    require_duplicate_from boolean,
    enable_anonymous boolean,
    restrict_editing_same_level_committee_admins boolean,
    saml_enabled boolean,
    saml_login_button_text varchar(256)
        CONSTRAINT default_organization_saml_login_button_text DEFAULT 'SAML login',
    saml_attr_mapping jsonb,
    saml_metadata_idp text,
    saml_metadata_sp text,
    saml_private_key text,
    theme_id integer
        CONSTRAINT required_organization_theme_id NOT NULL
        CONSTRAINT unique_organization_theme_id UNIQUE,
    users_email_sender varchar(256)
        CONSTRAINT default_organization_users_email_sender DEFAULT 'OpenSlides',
    users_email_replyto varchar(256),
    users_email_subject varchar(256)
        CONSTRAINT default_organization_users_email_subject DEFAULT 'OpenSlides access data',
    users_email_body text
        CONSTRAINT default_organization_users_email_body DEFAULT 'Dear {name},

this is your personal OpenSlides login:

{url}
Username: {username}
Password: {password}


This email was generated automatically.',
    url varchar(256)
        CONSTRAINT default_organization_url DEFAULT 'https://example.com'
);



comment on column organization_t.limit_of_meetings is 'Maximum of active meetings for the whole organization. 0 means no limitation at all';
comment on column organization_t.limit_of_users is 'Maximum of active users for the whole organization. 0 means no limitation at all';


CREATE TABLE organization_tag_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_organization_tag_name NOT NULL,
    color varchar(7)
        CONSTRAINT color_organization_tag_color CHECK (color is null or color ~* '^#[a-f0-9]{6}$')
        CONSTRAINT required_organization_tag_color NOT NULL,
    organization_id integer
        CONSTRAINT required_organization_tag_organization_id NOT NULL
        CONSTRAINT default_organization_tag_organization_id DEFAULT 1
);




CREATE TABLE personal_note_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    note text,
    star boolean,
    meeting_user_id integer
        CONSTRAINT required_personal_note_meeting_user_id NOT NULL,
    content_object_id varchar(100)
        CONSTRAINT required_personal_note_content_object_id NOT NULL,
    content_object_id_motion_id integer
        CONSTRAINT generated_always_as_personal_note_content_object_id_motion_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'motion' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    CONSTRAINT valid_personal_note_content_object_id_part1 CHECK (split_part(content_object_id, '/', 1) IN ('motion')),
    meeting_id integer
        CONSTRAINT required_personal_note_meeting_id NOT NULL,
    CONSTRAINT unique_personal_note_meeting_user_id_content_object_id UNIQUE (meeting_user_id, content_object_id)
);




CREATE TABLE point_of_order_category_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    text varchar(256)
        CONSTRAINT required_point_of_order_category_text NOT NULL,
    rank integer
        CONSTRAINT required_point_of_order_category_rank NOT NULL,
    meeting_id integer
        CONSTRAINT required_point_of_order_category_meeting_id NOT NULL
);




CREATE TABLE poll_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    title varchar(256)
        CONSTRAINT required_poll_title NOT NULL,
    description varchar(256),
    type enum_poll_type
        CONSTRAINT required_poll_type NOT NULL,
    backend enum_poll_backends
        CONSTRAINT required_poll_backend NOT NULL
        CONSTRAINT default_poll_backend DEFAULT 'fast',
    is_pseudoanonymized boolean,
    pollmethod enum_poll_pollmethod
        CONSTRAINT required_poll_pollmethod NOT NULL,
    state enum_poll_state
        CONSTRAINT default_poll_state DEFAULT 'created',
    min_votes_amount integer
        CONSTRAINT minimum_poll_min_votes_amount CHECK (min_votes_amount >= 1)
        CONSTRAINT default_poll_min_votes_amount DEFAULT 1,
    max_votes_amount integer
        CONSTRAINT minimum_poll_max_votes_amount CHECK (max_votes_amount >= 1)
        CONSTRAINT default_poll_max_votes_amount DEFAULT 1,
    max_votes_per_option integer
        CONSTRAINT minimum_poll_max_votes_per_option CHECK (max_votes_per_option >= 1)
        CONSTRAINT default_poll_max_votes_per_option DEFAULT 1,
    global_yes boolean
        CONSTRAINT default_poll_global_yes DEFAULT False,
    global_no boolean
        CONSTRAINT default_poll_global_no DEFAULT False,
    global_abstain boolean
        CONSTRAINT default_poll_global_abstain DEFAULT False,
    onehundred_percent_base enum_onehundred_percent_bases
        CONSTRAINT required_poll_onehundred_percent_base NOT NULL
        CONSTRAINT default_poll_onehundred_percent_base DEFAULT 'disabled',
    votesvalid decimal(16,6),
    votesinvalid decimal(16,6),
    votescast decimal(16,6),
    entitled_users_at_stop jsonb,
    live_voting_enabled boolean
        CONSTRAINT default_poll_live_voting_enabled DEFAULT False,
    sequential_number integer
        CONSTRAINT required_poll_sequential_number NOT NULL,
    CONSTRAINT unique_poll_sequential_number_meeting_id UNIQUE (sequential_number, meeting_id),
    content_object_id varchar(100)
        CONSTRAINT required_poll_content_object_id NOT NULL,
    content_object_id_motion_id integer
        CONSTRAINT generated_always_as_poll_content_object_id_motion_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'motion' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_assignment_id integer
        CONSTRAINT generated_always_as_poll_content_object_id_assignment_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'assignment' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_topic_id integer
        CONSTRAINT generated_always_as_poll_content_object_id_topic_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'topic' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    CONSTRAINT valid_poll_content_object_id_part1 CHECK (split_part(content_object_id, '/', 1) IN ('motion','assignment','topic')),
    global_option_id integer
        CONSTRAINT unique_poll_global_option_id UNIQUE,
    meeting_id integer
        CONSTRAINT required_poll_meeting_id NOT NULL
);



comment on column poll_t.live_voting_enabled is 'If true, the vote service sends the votes of the users to the autoupdate service.';
comment on column poll_t.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';

/*
 Fields without SQL definition for table poll

    poll/live_votes: type:JSON is marked as a calculated field and not generated in schema

*/

CREATE TABLE poll_candidate_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    poll_candidate_list_id integer
        CONSTRAINT required_poll_candidate_poll_candidate_list_id NOT NULL,
    user_id integer,
    weight integer
        CONSTRAINT required_poll_candidate_weight NOT NULL,
    meeting_id integer
        CONSTRAINT required_poll_candidate_meeting_id NOT NULL
);




CREATE TABLE poll_candidate_list_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    meeting_id integer
        CONSTRAINT required_poll_candidate_list_meeting_id NOT NULL
);




CREATE TABLE projection_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    options jsonb,
    stable boolean
        CONSTRAINT default_projection_stable DEFAULT False,
    weight integer,
    type varchar(256),
    current_projector_id integer,
    preview_projector_id integer,
    history_projector_id integer,
    content_object_id varchar(100)
        CONSTRAINT required_projection_content_object_id NOT NULL,
    content_object_id_meeting_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_meeting_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'meeting' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_motion_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_motion_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'motion' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_meeting_mediafile_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_meeting51b9977 GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'meeting_mediafile' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_list_of_speakers_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_list_of6e51c6f GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'list_of_speakers' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_motion_block_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_motion_31fedd3 GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'motion_block' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_assignment_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_assignment_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'assignment' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_agenda_item_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_agenda_item_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'agenda_item' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_topic_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_topic_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'topic' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_poll_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_poll_id GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'poll' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_projector_message_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_project05617d4 GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'projector_message' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    content_object_id_projector_countdown_id integer
        CONSTRAINT generated_always_as_projection_content_object_id_project708e3f9 GENERATED ALWAYS AS (CASE WHEN split_part(content_object_id, '/', 1) = 'projector_countdown' THEN cast(split_part(content_object_id, '/', 2) AS INTEGER) ELSE null END) STORED,
    CONSTRAINT valid_projection_content_object_id_part1 CHECK (split_part(content_object_id, '/', 1) IN ('meeting','motion','meeting_mediafile','list_of_speakers','motion_block','assignment','agenda_item','topic','poll','projector_message','projector_countdown')),
    meeting_id integer
        CONSTRAINT required_projection_meeting_id NOT NULL
);



/*
 Fields without SQL definition for table projection

    projection/content: type:JSON is marked as a calculated field and not generated in schema

*/

CREATE TABLE projector_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_projector_name NOT NULL,
    is_internal boolean
        CONSTRAINT default_projector_is_internal DEFAULT False,
    scale integer
        CONSTRAINT default_projector_scale DEFAULT 0,
    scroll integer
        CONSTRAINT minimum_projector_scroll CHECK (scroll >= 0)
        CONSTRAINT default_projector_scroll DEFAULT 0,
    width integer
        CONSTRAINT minimum_projector_width CHECK (width >= 1)
        CONSTRAINT default_projector_width DEFAULT 1200,
    aspect_ratio_numerator integer
        CONSTRAINT minimum_projector_aspect_ratio_numerator CHECK (aspect_ratio_numerator >= 1)
        CONSTRAINT default_projector_aspect_ratio_numerator DEFAULT 16,
    aspect_ratio_denominator integer
        CONSTRAINT minimum_projector_aspect_ratio_denominator CHECK (aspect_ratio_denominator >= 1)
        CONSTRAINT default_projector_aspect_ratio_denominator DEFAULT 9,
    color varchar(7)
        CONSTRAINT color_projector_color CHECK (color is null or color ~* '^#[a-f0-9]{6}$')
        CONSTRAINT default_projector_color DEFAULT '#000000',
    background_color varchar(7)
        CONSTRAINT color_projector_background_color CHECK (background_color is null or background_color ~* '^#[a-f0-9]{6}$')
        CONSTRAINT default_projector_background_color DEFAULT '#ffffff',
    header_background_color varchar(7)
        CONSTRAINT color_projector_header_background_color CHECK (header_background_color is null or header_background_color ~* '^#[a-f0-9]{6}$')
        CONSTRAINT default_projector_header_background_color DEFAULT '#317796',
    header_font_color varchar(7)
        CONSTRAINT color_projector_header_font_color CHECK (header_font_color is null or header_font_color ~* '^#[a-f0-9]{6}$')
        CONSTRAINT default_projector_header_font_color DEFAULT '#f5f5f5',
    header_h1_color varchar(7)
        CONSTRAINT color_projector_header_h1_color CHECK (header_h1_color is null or header_h1_color ~* '^#[a-f0-9]{6}$')
        CONSTRAINT default_projector_header_h1_color DEFAULT '#317796',
    chyron_background_color varchar(7)
        CONSTRAINT color_projector_chyron_background_color CHECK (chyron_background_color is null or chyron_background_color ~* '^#[a-f0-9]{6}$')
        CONSTRAINT default_projector_chyron_background_color DEFAULT '#317796',
    chyron_background_color_2 varchar(7)
        CONSTRAINT color_projector_chyron_background_color_2 CHECK (chyron_background_color_2 is null or chyron_background_color_2 ~* '^#[a-f0-9]{6}$')
        CONSTRAINT default_projector_chyron_background_color_2 DEFAULT '#134768',
    chyron_font_color varchar(7)
        CONSTRAINT color_projector_chyron_font_color CHECK (chyron_font_color is null or chyron_font_color ~* '^#[a-f0-9]{6}$')
        CONSTRAINT default_projector_chyron_font_color DEFAULT '#ffffff',
    chyron_font_color_2 varchar(7)
        CONSTRAINT color_projector_chyron_font_color_2 CHECK (chyron_font_color_2 is null or chyron_font_color_2 ~* '^#[a-f0-9]{6}$')
        CONSTRAINT default_projector_chyron_font_color_2 DEFAULT '#ffffff',
    show_header_footer boolean
        CONSTRAINT default_projector_show_header_footer DEFAULT True,
    show_title boolean
        CONSTRAINT default_projector_show_title DEFAULT True,
    show_logo boolean
        CONSTRAINT default_projector_show_logo DEFAULT True,
    show_clock boolean
        CONSTRAINT default_projector_show_clock DEFAULT True,
    sequential_number integer
        CONSTRAINT required_projector_sequential_number NOT NULL,
    CONSTRAINT unique_projector_sequential_number_meeting_id UNIQUE (sequential_number, meeting_id),
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
    meeting_id integer
        CONSTRAINT required_projector_meeting_id NOT NULL
);



comment on column projector_t.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE projector_countdown_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    title varchar(256)
        CONSTRAINT required_projector_countdown_title NOT NULL,
    description varchar(256)
        CONSTRAINT default_projector_countdown_description DEFAULT '',
    default_time integer,
    countdown_time double precision
        CONSTRAINT default_projector_countdown_countdown_time DEFAULT 60,
    running boolean
        CONSTRAINT default_projector_countdown_running DEFAULT False,
    meeting_id integer
        CONSTRAINT required_projector_countdown_meeting_id NOT NULL,
    CONSTRAINT unique_projector_countdown_meeting_id_title UNIQUE (meeting_id, title)
);




CREATE TABLE projector_message_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    message text
        CONSTRAINT required_projector_message_message NOT NULL,
    meeting_id integer
        CONSTRAINT required_projector_message_meeting_id NOT NULL
);




CREATE TABLE speaker_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    begin_time timestamptz,
    end_time timestamptz,
    pause_time timestamptz,
    unpause_time timestamptz,
    total_pause integer,
    weight integer
        CONSTRAINT default_speaker_weight DEFAULT 10000,
    speech_state enum_speaker_speech_state,
    answer boolean,
    note varchar(250),
    point_of_order boolean,
    list_of_speakers_id integer
        CONSTRAINT required_speaker_list_of_speakers_id NOT NULL,
    structure_level_list_of_speakers_id integer,
    meeting_user_id integer,
    point_of_order_category_id integer,
    meeting_id integer
        CONSTRAINT required_speaker_meeting_id NOT NULL
);




CREATE TABLE structure_level_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_structure_level_name NOT NULL,
    color varchar(7)
        CONSTRAINT color_structure_level_color CHECK (color is null or color ~* '^#[a-f0-9]{6}$'),
    default_time integer
        CONSTRAINT minimum_structure_level_default_time CHECK (default_time >= 0),
    meeting_id integer
        CONSTRAINT required_structure_level_meeting_id NOT NULL,
    CONSTRAINT unique_structure_level_meeting_id_name UNIQUE (meeting_id, name)
);




CREATE TABLE structure_level_list_of_speakers_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    structure_level_id integer
        CONSTRAINT required_structure_level_list_of_speakers_structure_level_id NOT NULL,
    list_of_speakers_id integer
        CONSTRAINT required_structure_level_list_of_speakers_list_of_speakers_id NOT NULL,
    initial_time integer
        CONSTRAINT required_structure_level_list_of_speakers_initial_time NOT NULL
        CONSTRAINT minimum_structure_level_list_of_speakers_initial_time CHECK (initial_time >= 1),
    additional_time double precision,
    remaining_time double precision
        CONSTRAINT required_structure_level_list_of_speakers_remaining_time NOT NULL,
    current_start_time timestamptz,
    meeting_id integer
        CONSTRAINT required_structure_level_list_of_speakers_meeting_id NOT NULL,
    CONSTRAINT unique_structure_level_list_of_speakers_meeting_id_struce047abe UNIQUE (meeting_id, structure_level_id, list_of_speakers_id)
);



comment on column structure_level_list_of_speakers_t.initial_time is 'The initial time of this structure_level for this LoS';
comment on column structure_level_list_of_speakers_t.additional_time is 'The summed added time of this structure_level for this LoS';
comment on column structure_level_list_of_speakers_t.remaining_time is 'The currently remaining time of this structure_level for this LoS';
comment on column structure_level_list_of_speakers_t.current_start_time is 'The current start time of a speaker for this structure_level. Is only set if a currently speaking speaker exists';


CREATE TABLE tag_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_tag_name NOT NULL,
    meeting_id integer
        CONSTRAINT required_tag_meeting_id NOT NULL
);




CREATE TABLE theme_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    name varchar(256)
        CONSTRAINT required_theme_name NOT NULL,
    accent_100 varchar(7)
        CONSTRAINT color_theme_accent_100 CHECK (accent_100 is null or accent_100 ~* '^#[a-f0-9]{6}$'),
    accent_200 varchar(7)
        CONSTRAINT color_theme_accent_200 CHECK (accent_200 is null or accent_200 ~* '^#[a-f0-9]{6}$'),
    accent_300 varchar(7)
        CONSTRAINT color_theme_accent_300 CHECK (accent_300 is null or accent_300 ~* '^#[a-f0-9]{6}$'),
    accent_400 varchar(7)
        CONSTRAINT color_theme_accent_400 CHECK (accent_400 is null or accent_400 ~* '^#[a-f0-9]{6}$'),
    accent_50 varchar(7)
        CONSTRAINT color_theme_accent_50 CHECK (accent_50 is null or accent_50 ~* '^#[a-f0-9]{6}$'),
    accent_500 varchar(7)
        CONSTRAINT color_theme_accent_500 CHECK (accent_500 is null or accent_500 ~* '^#[a-f0-9]{6}$')
        CONSTRAINT required_theme_accent_500 NOT NULL
        CONSTRAINT default_theme_accent_500 DEFAULT '#2196f3',
    accent_600 varchar(7)
        CONSTRAINT color_theme_accent_600 CHECK (accent_600 is null or accent_600 ~* '^#[a-f0-9]{6}$'),
    accent_700 varchar(7)
        CONSTRAINT color_theme_accent_700 CHECK (accent_700 is null or accent_700 ~* '^#[a-f0-9]{6}$'),
    accent_800 varchar(7)
        CONSTRAINT color_theme_accent_800 CHECK (accent_800 is null or accent_800 ~* '^#[a-f0-9]{6}$'),
    accent_900 varchar(7)
        CONSTRAINT color_theme_accent_900 CHECK (accent_900 is null or accent_900 ~* '^#[a-f0-9]{6}$'),
    accent_a100 varchar(7)
        CONSTRAINT color_theme_accent_a100 CHECK (accent_a100 is null or accent_a100 ~* '^#[a-f0-9]{6}$'),
    accent_a200 varchar(7)
        CONSTRAINT color_theme_accent_a200 CHECK (accent_a200 is null or accent_a200 ~* '^#[a-f0-9]{6}$'),
    accent_a400 varchar(7)
        CONSTRAINT color_theme_accent_a400 CHECK (accent_a400 is null or accent_a400 ~* '^#[a-f0-9]{6}$'),
    accent_a700 varchar(7)
        CONSTRAINT color_theme_accent_a700 CHECK (accent_a700 is null or accent_a700 ~* '^#[a-f0-9]{6}$'),
    primary_100 varchar(7)
        CONSTRAINT color_theme_primary_100 CHECK (primary_100 is null or primary_100 ~* '^#[a-f0-9]{6}$'),
    primary_200 varchar(7)
        CONSTRAINT color_theme_primary_200 CHECK (primary_200 is null or primary_200 ~* '^#[a-f0-9]{6}$'),
    primary_300 varchar(7)
        CONSTRAINT color_theme_primary_300 CHECK (primary_300 is null or primary_300 ~* '^#[a-f0-9]{6}$'),
    primary_400 varchar(7)
        CONSTRAINT color_theme_primary_400 CHECK (primary_400 is null or primary_400 ~* '^#[a-f0-9]{6}$'),
    primary_50 varchar(7)
        CONSTRAINT color_theme_primary_50 CHECK (primary_50 is null or primary_50 ~* '^#[a-f0-9]{6}$'),
    primary_500 varchar(7)
        CONSTRAINT color_theme_primary_500 CHECK (primary_500 is null or primary_500 ~* '^#[a-f0-9]{6}$')
        CONSTRAINT required_theme_primary_500 NOT NULL
        CONSTRAINT default_theme_primary_500 DEFAULT '#317796',
    primary_600 varchar(7)
        CONSTRAINT color_theme_primary_600 CHECK (primary_600 is null or primary_600 ~* '^#[a-f0-9]{6}$'),
    primary_700 varchar(7)
        CONSTRAINT color_theme_primary_700 CHECK (primary_700 is null or primary_700 ~* '^#[a-f0-9]{6}$'),
    primary_800 varchar(7)
        CONSTRAINT color_theme_primary_800 CHECK (primary_800 is null or primary_800 ~* '^#[a-f0-9]{6}$'),
    primary_900 varchar(7)
        CONSTRAINT color_theme_primary_900 CHECK (primary_900 is null or primary_900 ~* '^#[a-f0-9]{6}$'),
    primary_a100 varchar(7)
        CONSTRAINT color_theme_primary_a100 CHECK (primary_a100 is null or primary_a100 ~* '^#[a-f0-9]{6}$'),
    primary_a200 varchar(7)
        CONSTRAINT color_theme_primary_a200 CHECK (primary_a200 is null or primary_a200 ~* '^#[a-f0-9]{6}$'),
    primary_a400 varchar(7)
        CONSTRAINT color_theme_primary_a400 CHECK (primary_a400 is null or primary_a400 ~* '^#[a-f0-9]{6}$'),
    primary_a700 varchar(7)
        CONSTRAINT color_theme_primary_a700 CHECK (primary_a700 is null or primary_a700 ~* '^#[a-f0-9]{6}$'),
    warn_100 varchar(7)
        CONSTRAINT color_theme_warn_100 CHECK (warn_100 is null or warn_100 ~* '^#[a-f0-9]{6}$'),
    warn_200 varchar(7)
        CONSTRAINT color_theme_warn_200 CHECK (warn_200 is null or warn_200 ~* '^#[a-f0-9]{6}$'),
    warn_300 varchar(7)
        CONSTRAINT color_theme_warn_300 CHECK (warn_300 is null or warn_300 ~* '^#[a-f0-9]{6}$'),
    warn_400 varchar(7)
        CONSTRAINT color_theme_warn_400 CHECK (warn_400 is null or warn_400 ~* '^#[a-f0-9]{6}$'),
    warn_50 varchar(7)
        CONSTRAINT color_theme_warn_50 CHECK (warn_50 is null or warn_50 ~* '^#[a-f0-9]{6}$'),
    warn_500 varchar(7)
        CONSTRAINT color_theme_warn_500 CHECK (warn_500 is null or warn_500 ~* '^#[a-f0-9]{6}$')
        CONSTRAINT required_theme_warn_500 NOT NULL
        CONSTRAINT default_theme_warn_500 DEFAULT '#f06400',
    warn_600 varchar(7)
        CONSTRAINT color_theme_warn_600 CHECK (warn_600 is null or warn_600 ~* '^#[a-f0-9]{6}$'),
    warn_700 varchar(7)
        CONSTRAINT color_theme_warn_700 CHECK (warn_700 is null or warn_700 ~* '^#[a-f0-9]{6}$'),
    warn_800 varchar(7)
        CONSTRAINT color_theme_warn_800 CHECK (warn_800 is null or warn_800 ~* '^#[a-f0-9]{6}$'),
    warn_900 varchar(7)
        CONSTRAINT color_theme_warn_900 CHECK (warn_900 is null or warn_900 ~* '^#[a-f0-9]{6}$'),
    warn_a100 varchar(7)
        CONSTRAINT color_theme_warn_a100 CHECK (warn_a100 is null or warn_a100 ~* '^#[a-f0-9]{6}$'),
    warn_a200 varchar(7)
        CONSTRAINT color_theme_warn_a200 CHECK (warn_a200 is null or warn_a200 ~* '^#[a-f0-9]{6}$'),
    warn_a400 varchar(7)
        CONSTRAINT color_theme_warn_a400 CHECK (warn_a400 is null or warn_a400 ~* '^#[a-f0-9]{6}$'),
    warn_a700 varchar(7)
        CONSTRAINT color_theme_warn_a700 CHECK (warn_a700 is null or warn_a700 ~* '^#[a-f0-9]{6}$'),
    headbar varchar(7)
        CONSTRAINT color_theme_headbar CHECK (headbar is null or headbar ~* '^#[a-f0-9]{6}$'),
    yes varchar(7)
        CONSTRAINT color_theme_yes CHECK (yes is null or yes ~* '^#[a-f0-9]{6}$'),
    no varchar(7)
        CONSTRAINT color_theme_no CHECK (no is null or no ~* '^#[a-f0-9]{6}$'),
    abstain varchar(7)
        CONSTRAINT color_theme_abstain CHECK (abstain is null or abstain ~* '^#[a-f0-9]{6}$'),
    organization_id integer
        CONSTRAINT required_theme_organization_id NOT NULL
        CONSTRAINT default_theme_organization_id DEFAULT 1
);




CREATE TABLE topic_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    title varchar(256)
        CONSTRAINT required_topic_title NOT NULL,
    text text,
    sequential_number integer
        CONSTRAINT required_topic_sequential_number NOT NULL,
    CONSTRAINT unique_topic_sequential_number_meeting_id UNIQUE (sequential_number, meeting_id),
    meeting_id integer
        CONSTRAINT required_topic_meeting_id NOT NULL
);



comment on column topic_t.sequential_number is 'The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.';


CREATE TABLE user_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    username varchar(256)
        CONSTRAINT required_user_username NOT NULL
        CONSTRAINT unique_user_username UNIQUE,
    member_number varchar(256)
        CONSTRAINT unique_user_member_number UNIQUE,
    saml_id varchar(256)
        CONSTRAINT unique_user_saml_id UNIQUE
        CONSTRAINT minlength_user_saml_id CHECK (char_length(saml_id) >= 1),
    pronoun varchar(32),
    title varchar(256),
    first_name varchar(256),
    last_name varchar(256),
    is_active boolean
        CONSTRAINT default_user_is_active DEFAULT True,
    is_physical_person boolean
        CONSTRAINT default_user_is_physical_person DEFAULT True,
    password varchar(256),
    default_password varchar(256),
    can_change_own_password boolean
        CONSTRAINT default_user_can_change_own_password DEFAULT True,
    email varchar(256),
    default_vote_weight decimal(16,6)
        CONSTRAINT minimum_user_default_vote_weight CHECK (default_vote_weight >= 0.000001)
        CONSTRAINT default_user_default_vote_weight DEFAULT '1.000000',
    last_email_sent timestamptz,
    is_demo_user boolean,
    last_login timestamptz,
    external boolean,
    gender_id integer,
    organization_management_level enum_user_organization_management_level,
    home_committee_id integer,
    organization_id integer
        CONSTRAINT required_user_organization_id NOT NULL
        CONSTRAINT default_user_organization_id DEFAULT 1
);



comment on column user_t.saml_id is 'unique-key from IdP for SAML login';
comment on column user_t.organization_management_level is 'Hierarchical permission level for the whole organization.';


CREATE TABLE vote_t (
    id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    weight decimal(16,6)
        CONSTRAINT required_vote_weight NOT NULL,
    value varchar(256)
        CONSTRAINT required_vote_value NOT NULL,
    user_token varchar(256)
        CONSTRAINT required_vote_user_token NOT NULL,
    option_id integer
        CONSTRAINT required_vote_option_id NOT NULL,
    user_id integer,
    delegated_user_id integer,
    meeting_id integer
        CONSTRAINT required_vote_meeting_id NOT NULL
);





-- Intermediate table definitions

CREATE TABLE nm_chat_group_read_group_ids_group_t (
    chat_group_id integer
        CONSTRAINT required_nm_chat_group_read_group_ids_group_t_chat_group_id NOT NULL
        CONSTRAINT fk_nm_chat_group_read_group_ids_group_t_chat_group_id_chc0b2569 REFERENCES chat_group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    group_id integer
        CONSTRAINT required_nm_chat_group_read_group_ids_group_t_group_id NOT NULL
        CONSTRAINT fk_nm_chat_group_read_group_ids_group_t_group_id_group_t_id REFERENCES group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_chat_group_read_group_ids_group_t PRIMARY KEY (chat_group_id, group_id)
);
CREATE INDEX idx_nm_chat_group_read_group_ids_group_t_chat_group_id ON nm_chat_group_read_group_ids_group_t (chat_group_id);
CREATE INDEX idx_nm_chat_group_read_group_ids_group_t_group_id ON nm_chat_group_read_group_ids_group_t (group_id);

CREATE TABLE nm_chat_group_write_group_ids_group_t (
    chat_group_id integer
        CONSTRAINT required_nm_chat_group_write_group_ids_group_t_chat_group_id NOT NULL
        CONSTRAINT fk_nm_chat_group_write_group_ids_group_t_chat_group_id_cc085d6c REFERENCES chat_group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    group_id integer
        CONSTRAINT required_nm_chat_group_write_group_ids_group_t_group_id NOT NULL
        CONSTRAINT fk_nm_chat_group_write_group_ids_group_t_group_id_group_t_id REFERENCES group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_chat_group_write_group_ids_group_t PRIMARY KEY (chat_group_id, group_id)
);
CREATE INDEX idx_nm_chat_group_write_group_ids_group_t_chat_group_id ON nm_chat_group_write_group_ids_group_t (chat_group_id);
CREATE INDEX idx_nm_chat_group_write_group_ids_group_t_group_id ON nm_chat_group_write_group_ids_group_t (group_id);

CREATE TABLE nm_committee_manager_ids_user_t (
    committee_id integer
        CONSTRAINT required_nm_committee_manager_ids_user_t_committee_id NOT NULL
        CONSTRAINT fk_nm_committee_manager_ids_user_t_committee_id_committee_t_id REFERENCES committee_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    user_id integer
        CONSTRAINT required_nm_committee_manager_ids_user_t_user_id NOT NULL
        CONSTRAINT fk_nm_committee_manager_ids_user_t_user_id_user_t_id REFERENCES user_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_committee_manager_ids_user_t PRIMARY KEY (committee_id, user_id)
);
CREATE INDEX idx_nm_committee_manager_ids_user_t_committee_id ON nm_committee_manager_ids_user_t (committee_id);
CREATE INDEX idx_nm_committee_manager_ids_user_t_user_id ON nm_committee_manager_ids_user_t (user_id);

CREATE TABLE nm_committee_all_child_ids_committee_t (
    all_parent_id integer
        CONSTRAINT required_nm_committee_all_child_ids_committee_t_all_parent_id NOT NULL
        CONSTRAINT fk_nm_committee_all_child_ids_committee_t_all_parent_id_014ed42 REFERENCES committee_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    all_child_id integer
        CONSTRAINT required_nm_committee_all_child_ids_committee_t_all_child_id NOT NULL
        CONSTRAINT fk_nm_committee_all_child_ids_committee_t_all_child_id_cc86a8b2 REFERENCES committee_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_committee_all_child_ids_committee_t PRIMARY KEY (all_parent_id, all_child_id)
);
CREATE INDEX idx_nm_committee_all_child_ids_committee_t_all_parent_id ON nm_committee_all_child_ids_committee_t (all_parent_id);
CREATE INDEX idx_nm_committee_all_child_ids_committee_t_all_child_id ON nm_committee_all_child_ids_committee_t (all_child_id);

CREATE TABLE nm_committee_forward_to_committee_ids_committee_t (
    receive_forwardings_from_committee_id integer
        CONSTRAINT required_nm_committee_forward_to_committee_ids_committee4d5486a NOT NULL
        CONSTRAINT fk_nm_committee_forward_to_committee_ids_committee_t_rec0dc00a3 REFERENCES committee_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    forward_to_committee_id integer
        CONSTRAINT required_nm_committee_forward_to_committee_ids_committee7641257 NOT NULL
        CONSTRAINT fk_nm_committee_forward_to_committee_ids_committee_t_fora987475 REFERENCES committee_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_committee_forward_to_committee_ids_committee_t PRIMARY KEY (receive_forwardings_from_committee_id, forward_to_committee_id)
);
CREATE INDEX idx_nm_committee_forward_to_committee_ids_committee_t_re9215b1e ON nm_committee_forward_to_committee_ids_committee_t (receive_forwardings_from_committee_id);
CREATE INDEX idx_nm_committee_forward_to_committee_ids_committee_t_fo5507b60 ON nm_committee_forward_to_committee_ids_committee_t (forward_to_committee_id);

CREATE TABLE nm_group_meeting_user_ids_meeting_user_t (
    group_id integer
        CONSTRAINT required_nm_group_meeting_user_ids_meeting_user_t_group_id NOT NULL
        CONSTRAINT fk_nm_group_meeting_user_ids_meeting_user_t_group_id_group_t_id REFERENCES group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    meeting_user_id integer
        CONSTRAINT required_nm_group_meeting_user_ids_meeting_user_t_meetinfd3eac3 NOT NULL
        CONSTRAINT fk_nm_group_meeting_user_ids_meeting_user_t_meeting_userd442927 REFERENCES meeting_user_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_group_meeting_user_ids_meeting_user_t PRIMARY KEY (group_id, meeting_user_id)
);
CREATE INDEX idx_nm_group_meeting_user_ids_meeting_user_t_group_id ON nm_group_meeting_user_ids_meeting_user_t (group_id);
CREATE INDEX idx_nm_group_meeting_user_ids_meeting_user_t_meeting_user_id ON nm_group_meeting_user_ids_meeting_user_t (meeting_user_id);

CREATE TABLE nm_group_mmagi_meeting_mediafile_t (
    group_id integer
        CONSTRAINT required_nm_group_mmagi_meeting_mediafile_t_group_id NOT NULL
        CONSTRAINT fk_nm_group_mmagi_meeting_mediafile_t_group_id_group_t_id REFERENCES group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    meeting_mediafile_id integer
        CONSTRAINT required_nm_group_mmagi_meeting_mediafile_t_meeting_medi07742fb NOT NULL
        CONSTRAINT fk_nm_group_mmagi_meeting_mediafile_t_meeting_mediafile_6a1f41a REFERENCES meeting_mediafile_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_group_mmagi_meeting_mediafile_t PRIMARY KEY (group_id, meeting_mediafile_id)
);
CREATE INDEX idx_nm_group_mmagi_meeting_mediafile_t_group_id ON nm_group_mmagi_meeting_mediafile_t (group_id);
CREATE INDEX idx_nm_group_mmagi_meeting_mediafile_t_meeting_mediafile_id ON nm_group_mmagi_meeting_mediafile_t (meeting_mediafile_id);

CREATE TABLE nm_group_mmiagi_meeting_mediafile_t (
    group_id integer
        CONSTRAINT required_nm_group_mmiagi_meeting_mediafile_t_group_id NOT NULL
        CONSTRAINT fk_nm_group_mmiagi_meeting_mediafile_t_group_id_group_t_id REFERENCES group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    meeting_mediafile_id integer
        CONSTRAINT required_nm_group_mmiagi_meeting_mediafile_t_meeting_med7971c24 NOT NULL
        CONSTRAINT fk_nm_group_mmiagi_meeting_mediafile_t_meeting_mediafile1728d31 REFERENCES meeting_mediafile_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_group_mmiagi_meeting_mediafile_t PRIMARY KEY (group_id, meeting_mediafile_id)
);
CREATE INDEX idx_nm_group_mmiagi_meeting_mediafile_t_group_id ON nm_group_mmiagi_meeting_mediafile_t (group_id);
CREATE INDEX idx_nm_group_mmiagi_meeting_mediafile_t_meeting_mediafile_id ON nm_group_mmiagi_meeting_mediafile_t (meeting_mediafile_id);

CREATE TABLE nm_group_read_comment_section_ids_motion_comment_section_t (
    group_id integer
        CONSTRAINT required_nm_group_read_comment_section_ids_motion_commen5deb24d NOT NULL
        CONSTRAINT fk_nm_group_read_comment_section_ids_motion_comment_sectd992bd3 REFERENCES group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    motion_comment_section_id integer
        CONSTRAINT required_nm_group_read_comment_section_ids_motion_commen63ca9fc NOT NULL
        CONSTRAINT fk_nm_group_read_comment_section_ids_motion_comment_sect2d17ce5 REFERENCES motion_comment_section_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_group_read_comment_section_ids_motion_comment_section_t PRIMARY KEY (group_id, motion_comment_section_id)
);
CREATE INDEX idx_nm_group_read_comment_section_ids_motion_comment_secb9c23c0 ON nm_group_read_comment_section_ids_motion_comment_section_t (group_id);
CREATE INDEX idx_nm_group_read_comment_section_ids_motion_comment_sec520054a ON nm_group_read_comment_section_ids_motion_comment_section_t (motion_comment_section_id);

CREATE TABLE nm_group_write_comment_section_ids_motion_comment_section_t (
    group_id integer
        CONSTRAINT required_nm_group_write_comment_section_ids_motion_commeeda6f3f NOT NULL
        CONSTRAINT fk_nm_group_write_comment_section_ids_motion_comment_sec39cad7b REFERENCES group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    motion_comment_section_id integer
        CONSTRAINT required_nm_group_write_comment_section_ids_motion_commee683d53 NOT NULL
        CONSTRAINT fk_nm_group_write_comment_section_ids_motion_comment_sec9ffa691 REFERENCES motion_comment_section_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_group_write_comment_section_ids_motion_comment_section_t PRIMARY KEY (group_id, motion_comment_section_id)
);
CREATE INDEX idx_nm_group_write_comment_section_ids_motion_comment_sed5732f3 ON nm_group_write_comment_section_ids_motion_comment_section_t (group_id);
CREATE INDEX idx_nm_group_write_comment_section_ids_motion_comment_se3ab0450 ON nm_group_write_comment_section_ids_motion_comment_section_t (motion_comment_section_id);

CREATE TABLE nm_group_poll_ids_poll_t (
    group_id integer
        CONSTRAINT required_nm_group_poll_ids_poll_t_group_id NOT NULL
        CONSTRAINT fk_nm_group_poll_ids_poll_t_group_id_group_t_id REFERENCES group_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    poll_id integer
        CONSTRAINT required_nm_group_poll_ids_poll_t_poll_id NOT NULL
        CONSTRAINT fk_nm_group_poll_ids_poll_t_poll_id_poll_t_id REFERENCES poll_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_group_poll_ids_poll_t PRIMARY KEY (group_id, poll_id)
);
CREATE INDEX idx_nm_group_poll_ids_poll_t_group_id ON nm_group_poll_ids_poll_t (group_id);
CREATE INDEX idx_nm_group_poll_ids_poll_t_poll_id ON nm_group_poll_ids_poll_t (poll_id);

CREATE TABLE nm_meeting_present_user_ids_user_t (
    meeting_id integer
        CONSTRAINT required_nm_meeting_present_user_ids_user_t_meeting_id NOT NULL
        CONSTRAINT fk_nm_meeting_present_user_ids_user_t_meeting_id_meeting_t_id REFERENCES meeting_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    user_id integer
        CONSTRAINT required_nm_meeting_present_user_ids_user_t_user_id NOT NULL
        CONSTRAINT fk_nm_meeting_present_user_ids_user_t_user_id_user_t_id REFERENCES user_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_meeting_present_user_ids_user_t PRIMARY KEY (meeting_id, user_id)
);
CREATE INDEX idx_nm_meeting_present_user_ids_user_t_meeting_id ON nm_meeting_present_user_ids_user_t (meeting_id);
CREATE INDEX idx_nm_meeting_present_user_ids_user_t_user_id ON nm_meeting_present_user_ids_user_t (user_id);

CREATE TABLE gm_meeting_mediafile_attachment_ids_t (
    meeting_mediafile_id integer
        CONSTRAINT required_gm_meeting_mediafile_attachment_ids_t_meeting_md55faf2 NOT NULL
        CONSTRAINT fk_gm_meeting_mediafile_attachment_ids_t_meeting_mediaficc00c2e REFERENCES meeting_mediafile_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    attachment_id varchar(100)
        CONSTRAINT required_gm_meeting_mediafile_attachment_ids_t_attachment_id NOT NULL,
    attachment_id_motion_id integer
        CONSTRAINT generated_always_as_meeting_mediafile_attachment_id GENERATED ALWAYS AS (CASE WHEN split_part(attachment_id, '/', 1) = 'motion' THEN cast(split_part(attachment_id, '/', 2) AS INTEGER) ELSE null END) STORED
        CONSTRAINT fk_gm_meeting_mediafile_attachment_ids_t_attachment_id_mec23f0c REFERENCES motion_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    attachment_id_topic_id integer
        CONSTRAINT generated_always_as_meeting_mediafile_attachment_id GENERATED ALWAYS AS (CASE WHEN split_part(attachment_id, '/', 1) = 'topic' THEN cast(split_part(attachment_id, '/', 2) AS INTEGER) ELSE null END) STORED
        CONSTRAINT fk_gm_meeting_mediafile_attachment_ids_t_attachment_id_tf2c2308 REFERENCES topic_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    attachment_id_assignment_id integer
        CONSTRAINT generated_always_as_meeting_mediafile_attachment_id GENERATED ALWAYS AS (CASE WHEN split_part(attachment_id, '/', 1) = 'assignment' THEN cast(split_part(attachment_id, '/', 2) AS INTEGER) ELSE null END) STORED
        CONSTRAINT fk_gm_meeting_mediafile_attachment_ids_t_attachment_id_af0f87e8 REFERENCES assignment_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT valid_meeting_mediafile_attachment_id_part1 CHECK (split_part(attachment_id, '/', 1) IN ('motion', 'topic', 'assignment')),
    CONSTRAINT unique_meeting_mediafile_id_attachment_id UNIQUE (meeting_mediafile_id, attachment_id)
);
CREATE INDEX idx_gm_meeting_mediafile_attachment_ids_t_meeting_mediafile_id ON gm_meeting_mediafile_attachment_ids_t (meeting_mediafile_id);
CREATE INDEX idx_gm_meeting_mediafile_attachment_ids_t_attachment_id ON gm_meeting_mediafile_attachment_ids_t (attachment_id);
CREATE INDEX idx_gm_meeting_mediafile_attachment_ids_t_attachment_id_3c67b77 ON gm_meeting_mediafile_attachment_ids_t (attachment_id_motion_id);
CREATE INDEX idx_gm_meeting_mediafile_attachment_ids_t_attachment_id_8abf47a ON gm_meeting_mediafile_attachment_ids_t (attachment_id_topic_id);
CREATE INDEX idx_gm_meeting_mediafile_attachment_ids_t_attachment_id_66fb18e ON gm_meeting_mediafile_attachment_ids_t (attachment_id_assignment_id);

CREATE TABLE nm_meeting_user_structure_level_ids_structure_level_t (
    meeting_user_id integer
        CONSTRAINT required_nm_meeting_user_structure_level_ids_structure_l456f3b7 NOT NULL
        CONSTRAINT fk_nm_meeting_user_structure_level_ids_structure_level_t8c0bc42 REFERENCES meeting_user_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    structure_level_id integer
        CONSTRAINT required_nm_meeting_user_structure_level_ids_structure_lde64e43 NOT NULL
        CONSTRAINT fk_nm_meeting_user_structure_level_ids_structure_level_ta594d12 REFERENCES structure_level_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_meeting_user_structure_level_ids_structure_level_t PRIMARY KEY (meeting_user_id, structure_level_id)
);
CREATE INDEX idx_nm_meeting_user_structure_level_ids_structure_level_a842d49 ON nm_meeting_user_structure_level_ids_structure_level_t (meeting_user_id);
CREATE INDEX idx_nm_meeting_user_structure_level_ids_structure_level_abd5dca ON nm_meeting_user_structure_level_ids_structure_level_t (structure_level_id);

CREATE TABLE nm_motion_all_derived_motion_ids_motion_t (
    all_origin_id integer
        CONSTRAINT required_nm_motion_all_derived_motion_ids_motion_t_all_o1296fbc NOT NULL
        CONSTRAINT fk_nm_motion_all_derived_motion_ids_motion_t_all_origin_c37696a REFERENCES motion_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    all_derived_motion_id integer
        CONSTRAINT required_nm_motion_all_derived_motion_ids_motion_t_all_dd4c13a2 NOT NULL
        CONSTRAINT fk_nm_motion_all_derived_motion_ids_motion_t_all_derived87fec12 REFERENCES motion_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_motion_all_derived_motion_ids_motion_t PRIMARY KEY (all_origin_id, all_derived_motion_id)
);
CREATE INDEX idx_nm_motion_all_derived_motion_ids_motion_t_all_origin_id ON nm_motion_all_derived_motion_ids_motion_t (all_origin_id);
CREATE INDEX idx_nm_motion_all_derived_motion_ids_motion_t_all_derivee757fda ON nm_motion_all_derived_motion_ids_motion_t (all_derived_motion_id);

CREATE TABLE nm_motion_identical_motion_ids_motion_t (
    identical_motion_id_1 integer
        CONSTRAINT required_nm_motion_identical_motion_ids_motion_t_identic027cd64 NOT NULL
        CONSTRAINT fk_nm_motion_identical_motion_ids_motion_t_identical_motcb3785b REFERENCES motion_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    identical_motion_id_2 integer
        CONSTRAINT required_nm_motion_identical_motion_ids_motion_t_identic21a923f NOT NULL
        CONSTRAINT fk_nm_motion_identical_motion_ids_motion_t_identical_mot4e10b0c REFERENCES motion_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_motion_identical_motion_ids_motion_t PRIMARY KEY (identical_motion_id_1, identical_motion_id_2)
);
CREATE INDEX idx_nm_motion_identical_motion_ids_motion_t_identical_mo6988270 ON nm_motion_identical_motion_ids_motion_t (identical_motion_id_1);
CREATE INDEX idx_nm_motion_identical_motion_ids_motion_t_identical_moe0b67bf ON nm_motion_identical_motion_ids_motion_t (identical_motion_id_2);

CREATE TABLE gm_motion_state_extension_reference_ids_t (
    motion_id integer
        CONSTRAINT required_gm_motion_state_extension_reference_ids_t_motion_id NOT NULL
        CONSTRAINT fk_gm_motion_state_extension_reference_ids_t_motion_id_m49e5f09 REFERENCES motion_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    state_extension_reference_id varchar(100)
        CONSTRAINT required_gm_motion_state_extension_reference_ids_t_statea0d97fd NOT NULL,
    state_extension_reference_id_motion_id integer
        CONSTRAINT generated_always_as_motion_state_extension_reference_id GENERATED ALWAYS AS (CASE WHEN split_part(state_extension_reference_id, '/', 1) = 'motion' THEN cast(split_part(state_extension_reference_id, '/', 2) AS INTEGER) ELSE null END) STORED
        CONSTRAINT fk_gm_motion_state_extension_reference_ids_t_state_exten1eb8dcc REFERENCES motion_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT valid_motion_state_extension_reference_id_part1 CHECK (split_part(state_extension_reference_id, '/', 1) IN ('motion')),
    CONSTRAINT unique_motion_id_state_extension_reference_id UNIQUE (motion_id, state_extension_reference_id)
);
CREATE INDEX idx_gm_motion_state_extension_reference_ids_t_motion_id ON gm_motion_state_extension_reference_ids_t (motion_id);
CREATE INDEX idx_gm_motion_state_extension_reference_ids_t_state_exte869c61b ON gm_motion_state_extension_reference_ids_t (state_extension_reference_id);
CREATE INDEX idx_gm_motion_state_extension_reference_ids_t_state_extee77cee3 ON gm_motion_state_extension_reference_ids_t (state_extension_reference_id_motion_id);

CREATE TABLE gm_motion_recommendation_extension_reference_ids_t (
    motion_id integer
        CONSTRAINT required_gm_motion_recommendation_extension_reference_ida5b58c4 NOT NULL
        CONSTRAINT fk_gm_motion_recommendation_extension_reference_ids_t_mo331611e REFERENCES motion_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    recommendation_extension_reference_id varchar(100)
        CONSTRAINT required_gm_motion_recommendation_extension_reference_id07dc8df NOT NULL,
    recommendation_extension_reference_id_motion_id integer
        CONSTRAINT generated_always_as_motion_recommendation_extension_refe8d13a13 GENERATED ALWAYS AS (CASE WHEN split_part(recommendation_extension_reference_id, '/', 1) = 'motion' THEN cast(split_part(recommendation_extension_reference_id, '/', 2) AS INTEGER) ELSE null END) STORED
        CONSTRAINT fk_gm_motion_recommendation_extension_reference_ids_t_re6acbf83 REFERENCES motion_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT valid_motion_recommendation_extension_reference_id_part1 CHECK (split_part(recommendation_extension_reference_id, '/', 1) IN ('motion')),
    CONSTRAINT unique_motion_id_recommendation_extension_reference_id UNIQUE (motion_id, recommendation_extension_reference_id)
);
CREATE INDEX idx_gm_motion_recommendation_extension_reference_ids_t_m81631d0 ON gm_motion_recommendation_extension_reference_ids_t (motion_id);
CREATE INDEX idx_gm_motion_recommendation_extension_reference_ids_t_r6488b59 ON gm_motion_recommendation_extension_reference_ids_t (recommendation_extension_reference_id);
CREATE INDEX idx_gm_motion_recommendation_extension_reference_ids_t_r1489537 ON gm_motion_recommendation_extension_reference_ids_t (recommendation_extension_reference_id_motion_id);

CREATE TABLE nm_motion_state_next_state_ids_motion_state_t (
    previous_state_id integer
        CONSTRAINT required_nm_motion_state_next_state_ids_motion_state_t_p18166f0 NOT NULL
        CONSTRAINT fk_nm_motion_state_next_state_ids_motion_state_t_previou40712f2 REFERENCES motion_state_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    next_state_id integer
        CONSTRAINT required_nm_motion_state_next_state_ids_motion_state_t_n82ff19d NOT NULL
        CONSTRAINT fk_nm_motion_state_next_state_ids_motion_state_t_next_st820d55c REFERENCES motion_state_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_motion_state_next_state_ids_motion_state_t PRIMARY KEY (previous_state_id, next_state_id)
);
CREATE INDEX idx_nm_motion_state_next_state_ids_motion_state_t_previoa964ca1 ON nm_motion_state_next_state_ids_motion_state_t (previous_state_id);
CREATE INDEX idx_nm_motion_state_next_state_ids_motion_state_t_next_state_id ON nm_motion_state_next_state_ids_motion_state_t (next_state_id);

CREATE TABLE gm_organization_tag_tagged_ids_t (
    organization_tag_id integer
        CONSTRAINT required_gm_organization_tag_tagged_ids_t_organization_tag_id NOT NULL
        CONSTRAINT fk_gm_organization_tag_tagged_ids_t_organization_tag_id_4c0ab0b REFERENCES organization_tag_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    tagged_id varchar(100)
        CONSTRAINT required_gm_organization_tag_tagged_ids_t_tagged_id NOT NULL,
    tagged_id_committee_id integer
        CONSTRAINT generated_always_as_organization_tag_tagged_id GENERATED ALWAYS AS (CASE WHEN split_part(tagged_id, '/', 1) = 'committee' THEN cast(split_part(tagged_id, '/', 2) AS INTEGER) ELSE null END) STORED
        CONSTRAINT fk_gm_organization_tag_tagged_ids_t_tagged_id_committee_c4b8172 REFERENCES committee_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    tagged_id_meeting_id integer
        CONSTRAINT generated_always_as_organization_tag_tagged_id GENERATED ALWAYS AS (CASE WHEN split_part(tagged_id, '/', 1) = 'meeting' THEN cast(split_part(tagged_id, '/', 2) AS INTEGER) ELSE null END) STORED
        CONSTRAINT fk_gm_organization_tag_tagged_ids_t_tagged_id_meeting_id97a619f REFERENCES meeting_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT valid_organization_tag_tagged_id_part1 CHECK (split_part(tagged_id, '/', 1) IN ('committee', 'meeting')),
    CONSTRAINT unique_organization_tag_id_tagged_id UNIQUE (organization_tag_id, tagged_id)
);
CREATE INDEX idx_gm_organization_tag_tagged_ids_t_organization_tag_id ON gm_organization_tag_tagged_ids_t (organization_tag_id);
CREATE INDEX idx_gm_organization_tag_tagged_ids_t_tagged_id ON gm_organization_tag_tagged_ids_t (tagged_id);
CREATE INDEX idx_gm_organization_tag_tagged_ids_t_tagged_id_committee_id ON gm_organization_tag_tagged_ids_t (tagged_id_committee_id);
CREATE INDEX idx_gm_organization_tag_tagged_ids_t_tagged_id_meeting_id ON gm_organization_tag_tagged_ids_t (tagged_id_meeting_id);

CREATE TABLE nm_poll_voted_ids_user_t (
    poll_id integer
        CONSTRAINT required_nm_poll_voted_ids_user_t_poll_id NOT NULL
        CONSTRAINT fk_nm_poll_voted_ids_user_t_poll_id_poll_t_id REFERENCES poll_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    user_id integer
        CONSTRAINT required_nm_poll_voted_ids_user_t_user_id NOT NULL
        CONSTRAINT fk_nm_poll_voted_ids_user_t_user_id_user_t_id REFERENCES user_t (id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT pk_nm_poll_voted_ids_user_t PRIMARY KEY (poll_id, user_id)
);
CREATE INDEX idx_nm_poll_voted_ids_user_t_poll_id ON nm_poll_voted_ids_user_t (poll_id);
CREATE INDEX idx_nm_poll_voted_ids_user_t_user_id ON nm_poll_voted_ids_user_t (user_id);

CREATE TABLE gm_tag_tagged_ids_t (
    tag_id integer
        CONSTRAINT required_gm_tag_tagged_ids_t_tag_id NOT NULL
        CONSTRAINT fk_gm_tag_tagged_ids_t_tag_id_tag_t_id REFERENCES tag_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    tagged_id varchar(100)
        CONSTRAINT required_gm_tag_tagged_ids_t_tagged_id NOT NULL,
    tagged_id_agenda_item_id integer
        CONSTRAINT generated_always_as_tag_tagged_id GENERATED ALWAYS AS (CASE WHEN split_part(tagged_id, '/', 1) = 'agenda_item' THEN cast(split_part(tagged_id, '/', 2) AS INTEGER) ELSE null END) STORED
        CONSTRAINT fk_gm_tag_tagged_ids_t_tagged_id_agenda_item_id_agenda_item_id REFERENCES agenda_item_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    tagged_id_assignment_id integer
        CONSTRAINT generated_always_as_tag_tagged_id GENERATED ALWAYS AS (CASE WHEN split_part(tagged_id, '/', 1) = 'assignment' THEN cast(split_part(tagged_id, '/', 2) AS INTEGER) ELSE null END) STORED
        CONSTRAINT fk_gm_tag_tagged_ids_t_tagged_id_assignment_id_assignment_id REFERENCES assignment_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    tagged_id_motion_id integer
        CONSTRAINT generated_always_as_tag_tagged_id GENERATED ALWAYS AS (CASE WHEN split_part(tagged_id, '/', 1) = 'motion' THEN cast(split_part(tagged_id, '/', 2) AS INTEGER) ELSE null END) STORED
        CONSTRAINT fk_gm_tag_tagged_ids_t_tagged_id_motion_id_motion_id REFERENCES motion_t(id)
        ON DELETE CASCADE
        INITIALLY DEFERRED,
    CONSTRAINT valid_tag_tagged_id_part1 CHECK (split_part(tagged_id, '/', 1) IN ('agenda_item', 'assignment', 'motion')),
    CONSTRAINT unique_tag_id_tagged_id UNIQUE (tag_id, tagged_id)
);
CREATE INDEX idx_gm_tag_tagged_ids_t_tag_id ON gm_tag_tagged_ids_t (tag_id);
CREATE INDEX idx_gm_tag_tagged_ids_t_tagged_id ON gm_tag_tagged_ids_t (tagged_id);
CREATE INDEX idx_gm_tag_tagged_ids_t_tagged_id_agenda_item_id ON gm_tag_tagged_ids_t (tagged_id_agenda_item_id);
CREATE INDEX idx_gm_tag_tagged_ids_t_tagged_id_assignment_id ON gm_tag_tagged_ids_t (tagged_id_assignment_id);
CREATE INDEX idx_gm_tag_tagged_ids_t_tagged_id_motion_id ON gm_tag_tagged_ids_t (tagged_id_motion_id);


-- View definitions

CREATE VIEW "action_worker" AS SELECT * FROM action_worker_t a;


CREATE VIEW "agenda_item" AS SELECT *,
(select array_agg(ai.id ORDER BY ai.id) from agenda_item_t ai where ai.parent_id = a.id) as child_ids,
(select array_agg(g.tag_id ORDER BY g.tag_id) from gm_tag_tagged_ids_t g where g.tagged_id_agenda_item_id = a.id) as tag_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_agenda_item_id = a.id) as projection_ids
FROM agenda_item_t a;


CREATE VIEW "assignment" AS SELECT *,
(select array_agg(ac.id ORDER BY ac.id) from assignment_candidate_t ac where ac.assignment_id = a.id) as candidate_ids,
(select array_agg(p.id ORDER BY p.id) from poll_t p where p.content_object_id_assignment_id = a.id) as poll_ids,
(select ai.id from agenda_item_t ai where ai.content_object_id_assignment_id = a.id) as agenda_item_id,
(select l.id from list_of_speakers_t l where l.content_object_id_assignment_id = a.id) as list_of_speakers_id,
(select array_agg(g.tag_id ORDER BY g.tag_id) from gm_tag_tagged_ids_t g where g.tagged_id_assignment_id = a.id) as tag_ids,
(select array_agg(g.meeting_mediafile_id ORDER BY g.meeting_mediafile_id) from gm_meeting_mediafile_attachment_ids_t g where g.attachment_id_assignment_id = a.id) as attachment_meeting_mediafile_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_assignment_id = a.id) as projection_ids,
(select array_agg(h.id ORDER BY h.id) from history_entry_t h where h.model_id_assignment_id = a.id) as history_entry_ids
FROM assignment_t a;


CREATE VIEW "assignment_candidate" AS SELECT * FROM assignment_candidate_t a;


CREATE VIEW "chat_group" AS SELECT *,
(select array_agg(cm.id ORDER BY cm.id) from chat_message_t cm where cm.chat_group_id = c.id) as chat_message_ids,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_chat_group_read_group_ids_group_t n where n.chat_group_id = c.id) as read_group_ids,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_chat_group_write_group_ids_group_t n where n.chat_group_id = c.id) as write_group_ids
FROM chat_group_t c;


CREATE VIEW "chat_message" AS SELECT * FROM chat_message_t c;


CREATE VIEW "committee" AS SELECT *,
(select array_agg(m.id ORDER BY m.id) from meeting_t m where m.committee_id = c.id) as meeting_ids,
(
  SELECT array_agg(DISTINCT user_id ORDER BY user_id)
  FROM (
    -- Select user_ids from committees meetings
    SELECT mu.user_id
    FROM meeting_t AS m
    INNER JOIN meeting_user_t AS mu ON mu.meeting_id = m.id
    WHERE m.committee_id = c.id

    UNION

    -- Select user_ids from committee managers
    SELECT cmu.user_id
    FROM nm_committee_manager_ids_user_t cmu
    WHERE cmu.committee_id = c.id

    UNION

    -- Select user_id from home committees
    SELECT u.id
    FROM user_t u
    WHERE u.home_committee_id = c.id
  ) _
) AS user_ids
,
(select array_agg(n.user_id ORDER BY n.user_id) from nm_committee_manager_ids_user_t n where n.committee_id = c.id) as manager_ids,
(select array_agg(ct.id ORDER BY ct.id) from committee_t ct where ct.parent_id = c.id) as child_ids,
(select array_agg(n.all_parent_id ORDER BY n.all_parent_id) from nm_committee_all_child_ids_committee_t n where n.all_child_id = c.id) as all_parent_ids,
(select array_agg(n.all_child_id ORDER BY n.all_child_id) from nm_committee_all_child_ids_committee_t n where n.all_parent_id = c.id) as all_child_ids,
(select array_agg(u.id ORDER BY u.id) from user_t u where u.home_committee_id = c.id) as native_user_ids,
(select array_agg(n.forward_to_committee_id ORDER BY n.forward_to_committee_id) from nm_committee_forward_to_committee_ids_committee_t n where n.receive_forwardings_from_committee_id = c.id) as forward_to_committee_ids,
(select array_agg(n.receive_forwardings_from_committee_id ORDER BY n.receive_forwardings_from_committee_id) from nm_committee_forward_to_committee_ids_committee_t n where n.forward_to_committee_id = c.id) as receive_forwardings_from_committee_ids,
(select array_agg(g.organization_tag_id ORDER BY g.organization_tag_id) from gm_organization_tag_tagged_ids_t g where g.tagged_id_committee_id = c.id) as organization_tag_ids
FROM committee_t c;

comment on column "committee".user_ids is 'Calculated field: All users which are in a group of a meeting, belonging to the committee or beeing manager of the committee';

CREATE VIEW "gender" AS SELECT *,
(select array_agg(u.id ORDER BY u.id) from user_t u where u.gender_id = g.id) as user_ids
FROM gender_t g;


CREATE VIEW "group" AS SELECT *,
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
(select array_agg(n.poll_id ORDER BY n.poll_id) from nm_group_poll_ids_poll_t n where n.group_id = g.id) as poll_ids
FROM group_t g;

comment on column "group".meeting_mediafile_inherited_access_group_ids is 'Calculated field.';

CREATE VIEW "history_entry" AS SELECT * FROM history_entry_t h;


CREATE VIEW "history_position" AS SELECT *,
(select array_agg(he.id ORDER BY he.id) from history_entry_t he where he.position_id = h.id) as entry_ids
FROM history_position_t h;


CREATE VIEW "import_preview" AS SELECT * FROM import_preview_t i;


CREATE VIEW "list_of_speakers" AS SELECT *,
(select array_agg(s.id ORDER BY s.id) from speaker_t s where s.list_of_speakers_id = l.id) as speaker_ids,
(select array_agg(s.id ORDER BY s.id) from structure_level_list_of_speakers_t s where s.list_of_speakers_id = l.id) as structure_level_list_of_speakers_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_list_of_speakers_id = l.id) as projection_ids
FROM list_of_speakers_t l;


CREATE VIEW "mediafile" AS SELECT *,
(select array_agg(mt.id ORDER BY mt.id) from mediafile_t mt where mt.parent_id = m.id) as child_ids,
(select array_agg(mm.id ORDER BY mm.id) from meeting_mediafile_t mm where mm.mediafile_id = m.id) as meeting_mediafile_ids
FROM mediafile_t m;


CREATE VIEW "meeting" AS SELECT *,
(select array_agg(g.id ORDER BY g.id) from group_t g where g.used_as_motion_poll_default_id = m.id) as motion_poll_default_group_ids,
(select array_agg(p.id ORDER BY p.id) from poll_candidate_list_t p where p.meeting_id = m.id) as poll_candidate_list_ids,
(select array_agg(p.id ORDER BY p.id) from poll_candidate_t p where p.meeting_id = m.id) as poll_candidate_ids,
(select array_agg(mu.id ORDER BY mu.id) from meeting_user_t mu where mu.meeting_id = m.id) as meeting_user_ids,
(select array_agg(g.id ORDER BY g.id) from group_t g where g.used_as_assignment_poll_default_id = m.id) as assignment_poll_default_group_ids,
(select array_agg(g.id ORDER BY g.id) from group_t g where g.used_as_poll_default_id = m.id) as poll_default_group_ids,
(select array_agg(g.id ORDER BY g.id) from group_t g where g.used_as_topic_poll_default_id = m.id) as topic_poll_default_group_ids,
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
(select array_agg(o.id ORDER BY o.id) from option_t o where o.meeting_id = m.id) as option_ids,
(select array_agg(v.id ORDER BY v.id) from vote_t v where v.meeting_id = m.id) as vote_ids,
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
(select array_agg(p.id ORDER BY p.id) from projector_t p where p.used_as_default_projector_for_poll_in_meeting_id = m.id) as default_projector_poll_ids,
(select array_agg(h.id ORDER BY h.id) from history_entry_t h where h.meeting_id = m.id) as relevant_history_entry_ids
FROM meeting_t m;

comment on column "meeting".user_ids is 'Calculated. All user ids from all users assigned to groups of this meeting.';

CREATE VIEW "meeting_mediafile" AS SELECT *,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_group_mmiagi_meeting_mediafile_t n where n.meeting_mediafile_id = m.id) as inherited_access_group_ids,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_group_mmagi_meeting_mediafile_t n where n.meeting_mediafile_id = m.id) as access_group_ids,
(select l.id from list_of_speakers_t l where l.content_object_id_meeting_mediafile_id = m.id) as list_of_speakers_id,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_meeting_mediafile_id = m.id) as projection_ids,
(select array_agg(g.attachment_id ORDER BY g.attachment_id) from gm_meeting_mediafile_attachment_ids_t g where g.meeting_mediafile_id = m.id) as attachment_ids,
(select m1.id from meeting_t m1 where m1.logo_projector_main_id = m.id) as used_as_logo_projector_main_in_meeting_id,
(select m1.id from meeting_t m1 where m1.logo_projector_header_id = m.id) as used_as_logo_projector_header_in_meeting_id,
(select m1.id from meeting_t m1 where m1.logo_web_header_id = m.id) as used_as_logo_web_header_in_meeting_id,
(select m1.id from meeting_t m1 where m1.logo_pdf_header_l_id = m.id) as used_as_logo_pdf_header_l_in_meeting_id,
(select m1.id from meeting_t m1 where m1.logo_pdf_header_r_id = m.id) as used_as_logo_pdf_header_r_in_meeting_id,
(select m1.id from meeting_t m1 where m1.logo_pdf_footer_l_id = m.id) as used_as_logo_pdf_footer_l_in_meeting_id,
(select m1.id from meeting_t m1 where m1.logo_pdf_footer_r_id = m.id) as used_as_logo_pdf_footer_r_in_meeting_id,
(select m1.id from meeting_t m1 where m1.logo_pdf_ballot_paper_id = m.id) as used_as_logo_pdf_ballot_paper_in_meeting_id,
(select m1.id from meeting_t m1 where m1.font_regular_id = m.id) as used_as_font_regular_in_meeting_id,
(select m1.id from meeting_t m1 where m1.font_italic_id = m.id) as used_as_font_italic_in_meeting_id,
(select m1.id from meeting_t m1 where m1.font_bold_id = m.id) as used_as_font_bold_in_meeting_id,
(select m1.id from meeting_t m1 where m1.font_bold_italic_id = m.id) as used_as_font_bold_italic_in_meeting_id,
(select m1.id from meeting_t m1 where m1.font_monospace_id = m.id) as used_as_font_monospace_in_meeting_id,
(select m1.id from meeting_t m1 where m1.font_chyron_speaker_name_id = m.id) as used_as_font_chyron_speaker_name_in_meeting_id,
(select m1.id from meeting_t m1 where m1.font_projector_h1_id = m.id) as used_as_font_projector_h1_in_meeting_id,
(select m1.id from meeting_t m1 where m1.font_projector_h2_id = m.id) as used_as_font_projector_h2_in_meeting_id
FROM meeting_mediafile_t m;

comment on column "meeting_mediafile".inherited_access_group_ids is 'Calculated in actions. Shows what access group permissions are actually relevant. Calculated as the intersection of this meeting_mediafiles access_group_ids and the related mediafiles potential parent mediafiles inherited_access_group_ids. If the parent has no meeting_mediafile for this meeting, its inherited access group is assumed to be the meetings admin group. If there is no parent, the inherited_access_group_ids is equal to the access_group_ids. If the access_group_ids are empty, the interpretations is that every group has access rights, therefore the parent inherited_access_group_ids are used as-is.';

CREATE VIEW "meeting_user" AS SELECT *,
(select array_agg(p.id ORDER BY p.id) from personal_note_t p where p.meeting_user_id = m.id) as personal_note_ids,
(select array_agg(s.id ORDER BY s.id) from speaker_t s where s.meeting_user_id = m.id) as speaker_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_supporter_t ms where ms.meeting_user_id = m.id) as motion_supporter_ids,
(select array_agg(me.id ORDER BY me.id) from motion_editor_t me where me.meeting_user_id = m.id) as motion_editor_ids,
(select array_agg(mw.id ORDER BY mw.id) from motion_working_group_speaker_t mw where mw.meeting_user_id = m.id) as motion_working_group_speaker_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_submitter_t ms where ms.meeting_user_id = m.id) as motion_submitter_ids,
(select array_agg(a.id ORDER BY a.id) from assignment_candidate_t a where a.meeting_user_id = m.id) as assignment_candidate_ids,
(select array_agg(mu.id ORDER BY mu.id) from meeting_user_t mu where mu.vote_delegated_to_id = m.id) as vote_delegations_from_ids,
(select array_agg(c.id ORDER BY c.id) from chat_message_t c where c.meeting_user_id = m.id) as chat_message_ids,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_group_meeting_user_ids_meeting_user_t n where n.meeting_user_id = m.id) as group_ids,
(select array_agg(n.structure_level_id ORDER BY n.structure_level_id) from nm_meeting_user_structure_level_ids_structure_level_t n where n.meeting_user_id = m.id) as structure_level_ids
FROM meeting_user_t m;


CREATE VIEW "motion" AS SELECT *,
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
(select array_agg(o.id ORDER BY o.id) from option_t o where o.content_object_id_motion_id = m.id) as option_ids,
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


CREATE VIEW "motion_block" AS SELECT *,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.block_id = m.id) as motion_ids,
(select a.id from agenda_item_t a where a.content_object_id_motion_block_id = m.id) as agenda_item_id,
(select l.id from list_of_speakers_t l where l.content_object_id_motion_block_id = m.id) as list_of_speakers_id,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_motion_block_id = m.id) as projection_ids
FROM motion_block_t m;


CREATE VIEW "motion_category" AS SELECT *,
(select array_agg(mc.id ORDER BY mc.id) from motion_category_t mc where mc.parent_id = m.id) as child_ids,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.category_id = m.id) as motion_ids
FROM motion_category_t m;


CREATE VIEW "motion_change_recommendation" AS SELECT * FROM motion_change_recommendation_t m;


CREATE VIEW "motion_comment" AS SELECT * FROM motion_comment_t m;


CREATE VIEW "motion_comment_section" AS SELECT *,
(select array_agg(mc.id ORDER BY mc.id) from motion_comment_t mc where mc.section_id = m.id) as comment_ids,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_group_read_comment_section_ids_motion_comment_section_t n where n.motion_comment_section_id = m.id) as read_group_ids,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_group_write_comment_section_ids_motion_comment_section_t n where n.motion_comment_section_id = m.id) as write_group_ids
FROM motion_comment_section_t m;


CREATE VIEW "motion_editor" AS SELECT * FROM motion_editor_t m;


CREATE VIEW "motion_state" AS SELECT *,
(select array_agg(ms.id ORDER BY ms.id) from motion_state_t ms where ms.submitter_withdraw_state_id = m.id) as submitter_withdraw_back_ids,
(select array_agg(n.next_state_id ORDER BY n.next_state_id) from nm_motion_state_next_state_ids_motion_state_t n where n.previous_state_id = m.id) as next_state_ids,
(select array_agg(n.previous_state_id ORDER BY n.previous_state_id) from nm_motion_state_next_state_ids_motion_state_t n where n.next_state_id = m.id) as previous_state_ids,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.state_id = m.id) as motion_ids,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.recommendation_id = m.id) as motion_recommendation_ids,
(select mw.id from motion_workflow_t mw where mw.first_state_id = m.id) as first_state_of_workflow_id
FROM motion_state_t m;


CREATE VIEW "motion_submitter" AS SELECT * FROM motion_submitter_t m;


CREATE VIEW "motion_supporter" AS SELECT * FROM motion_supporter_t m;


CREATE VIEW "motion_workflow" AS SELECT *,
(select array_agg(ms.id ORDER BY ms.id) from motion_state_t ms where ms.workflow_id = m.id) as state_ids,
(select m1.id from meeting_t m1 where m1.motions_default_workflow_id = m.id) as default_workflow_meeting_id,
(select m1.id from meeting_t m1 where m1.motions_default_amendment_workflow_id = m.id) as default_amendment_workflow_meeting_id
FROM motion_workflow_t m;


CREATE VIEW "motion_working_group_speaker" AS SELECT * FROM motion_working_group_speaker_t m;


CREATE VIEW "option" AS SELECT *,
(select p.id from poll_t p where p.global_option_id = o.id) as used_as_global_option_in_poll_id,
(select array_agg(v.id ORDER BY v.id) from vote_t v where v.option_id = o.id) as vote_ids
FROM option_t o;


CREATE VIEW "organization" AS SELECT *,
(select array_agg(g.id ORDER BY g.id) from gender_t g where g.organization_id = o.id) as gender_ids,
(select array_agg(c.id ORDER BY c.id) from committee_t c where c.organization_id = o.id) as committee_ids,
(select array_agg(m.id ORDER BY m.id) from meeting_t m where m.is_active_in_organization_id = o.id) as active_meeting_ids,
(select array_agg(m.id ORDER BY m.id) from meeting_t m where m.is_archived_in_organization_id = o.id) as archived_meeting_ids,
(select array_agg(m.id ORDER BY m.id) from meeting_t m where m.template_for_organization_id = o.id) as template_meeting_ids,
(select array_agg(ot.id ORDER BY ot.id) from organization_tag_t ot where ot.organization_id = o.id) as organization_tag_ids,
(select array_agg(t.id ORDER BY t.id) from theme_t t where t.organization_id = o.id) as theme_ids,
(select array_agg(m.id ORDER BY m.id) from mediafile_t m where m.owner_id_organization_id = o.id) as mediafile_ids,
(select array_agg(m.id ORDER BY m.id) from mediafile_t m where m.published_to_meetings_in_organization_id = o.id) as published_mediafile_ids,
(select array_agg(u.id ORDER BY u.id) from user_t u where u.organization_id = o.id) as user_ids
FROM organization_t o;


CREATE VIEW "organization_tag" AS SELECT *,
(select array_agg(g.tagged_id ORDER BY g.tagged_id) from gm_organization_tag_tagged_ids_t g where g.organization_tag_id = o.id) as tagged_ids
FROM organization_tag_t o;


CREATE VIEW "personal_note" AS SELECT * FROM personal_note_t p;


CREATE VIEW "point_of_order_category" AS SELECT *,
(select array_agg(s.id ORDER BY s.id) from speaker_t s where s.point_of_order_category_id = p.id) as speaker_ids
FROM point_of_order_category_t p;


CREATE VIEW "poll" AS SELECT *,
(select array_agg(o.id ORDER BY o.id) from option_t o where o.poll_id = p.id) as option_ids,
(select array_agg(n.user_id ORDER BY n.user_id) from nm_poll_voted_ids_user_t n where n.poll_id = p.id) as voted_ids,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_group_poll_ids_poll_t n where n.poll_id = p.id) as entitled_group_ids,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.content_object_id_poll_id = p.id) as projection_ids
FROM poll_t p;


CREATE VIEW "poll_candidate" AS SELECT * FROM poll_candidate_t p;


CREATE VIEW "poll_candidate_list" AS SELECT *,
(select array_agg(pc.id ORDER BY pc.id) from poll_candidate_t pc where pc.poll_candidate_list_id = p.id) as poll_candidate_ids,
(select o.id from option_t o where o.content_object_id_poll_candidate_list_id = p.id) as option_id
FROM poll_candidate_list_t p;


CREATE VIEW "projection" AS SELECT * FROM projection_t p;


CREATE VIEW "projector" AS SELECT *,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.current_projector_id = p.id) as current_projection_ids,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.preview_projector_id = p.id) as preview_projection_ids,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.history_projector_id = p.id) as history_projection_ids,
(select m.id from meeting_t m where m.reference_projector_id = p.id) as used_as_reference_projector_meeting_id
FROM projector_t p;


CREATE VIEW "projector_countdown" AS SELECT *,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.content_object_id_projector_countdown_id = p.id) as projection_ids,
(select m.id from meeting_t m where m.list_of_speakers_countdown_id = p.id) as used_as_list_of_speakers_countdown_meeting_id,
(select m.id from meeting_t m where m.poll_countdown_id = p.id) as used_as_poll_countdown_meeting_id
FROM projector_countdown_t p;


CREATE VIEW "projector_message" AS SELECT *,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.content_object_id_projector_message_id = p.id) as projection_ids
FROM projector_message_t p;


CREATE VIEW "speaker" AS SELECT * FROM speaker_t s;


CREATE VIEW "structure_level" AS SELECT *,
(select array_agg(n.meeting_user_id ORDER BY n.meeting_user_id) from nm_meeting_user_structure_level_ids_structure_level_t n where n.structure_level_id = s.id) as meeting_user_ids,
(select array_agg(sl.id ORDER BY sl.id) from structure_level_list_of_speakers_t sl where sl.structure_level_id = s.id) as structure_level_list_of_speakers_ids
FROM structure_level_t s;


CREATE VIEW "structure_level_list_of_speakers" AS SELECT *,
(select array_agg(st.id ORDER BY st.id) from speaker_t st where st.structure_level_list_of_speakers_id = s.id) as speaker_ids
FROM structure_level_list_of_speakers_t s;


CREATE VIEW "tag" AS SELECT *,
(select array_agg(g.tagged_id ORDER BY g.tagged_id) from gm_tag_tagged_ids_t g where g.tag_id = t.id) as tagged_ids
FROM tag_t t;


CREATE VIEW "theme" AS SELECT *,
(select o.id from organization_t o where o.theme_id = t.id) as theme_for_organization_id
FROM theme_t t;


CREATE VIEW "topic" AS SELECT *,
(select array_agg(g.meeting_mediafile_id ORDER BY g.meeting_mediafile_id) from gm_meeting_mediafile_attachment_ids_t g where g.attachment_id_topic_id = t.id) as attachment_meeting_mediafile_ids,
(select a.id from agenda_item_t a where a.content_object_id_topic_id = t.id) as agenda_item_id,
(select l.id from list_of_speakers_t l where l.content_object_id_topic_id = t.id) as list_of_speakers_id,
(select array_agg(p.id ORDER BY p.id) from poll_t p where p.content_object_id_topic_id = t.id) as poll_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_topic_id = t.id) as projection_ids
FROM topic_t t;


CREATE VIEW "user" AS SELECT *,
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
(select array_agg(n.poll_id ORDER BY n.poll_id) from nm_poll_voted_ids_user_t n where n.user_id = u.id) as poll_voted_ids,
(select array_agg(o.id ORDER BY o.id) from option_t o where o.content_object_id_user_id = u.id) as option_ids,
(select array_agg(v.id ORDER BY v.id) from vote_t v where v.user_id = u.id) as vote_ids,
(select array_agg(v.id ORDER BY v.id) from vote_t v where v.delegated_user_id = u.id) as delegated_vote_ids,
(select array_agg(p.id ORDER BY p.id) from poll_candidate_t p where p.user_id = u.id) as poll_candidate_ids,
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

CREATE VIEW "vote" AS SELECT * FROM vote_t v;



-- Alter table relations
ALTER TABLE agenda_item_t ADD CONSTRAINT fk_agenda_item_t_content_object_id_motion_id_motion_t_id FOREIGN KEY(content_object_id_motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_agenda_item_t_content_object_id_motion_id ON agenda_item_t (content_object_id_motion_id);
ALTER TABLE agenda_item_t ADD CONSTRAINT fk_agenda_item_t_content_object_id_motion_block_id_motiofc82ae2 FOREIGN KEY(content_object_id_motion_block_id) REFERENCES motion_block_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_agenda_item_t_content_object_id_motion_block_id ON agenda_item_t (content_object_id_motion_block_id);
ALTER TABLE agenda_item_t ADD CONSTRAINT fk_agenda_item_t_content_object_id_assignment_id_assignmd1e068c FOREIGN KEY(content_object_id_assignment_id) REFERENCES assignment_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_agenda_item_t_content_object_id_assignment_id ON agenda_item_t (content_object_id_assignment_id);
ALTER TABLE agenda_item_t ADD CONSTRAINT fk_agenda_item_t_content_object_id_topic_id_topic_t_id FOREIGN KEY(content_object_id_topic_id) REFERENCES topic_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_agenda_item_t_content_object_id_topic_id ON agenda_item_t (content_object_id_topic_id);
ALTER TABLE agenda_item_t ADD CONSTRAINT fk_agenda_item_t_parent_id_agenda_item_t_id FOREIGN KEY(parent_id) REFERENCES agenda_item_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_agenda_item_t_parent_id ON agenda_item_t (parent_id);
ALTER TABLE agenda_item_t ADD CONSTRAINT fk_agenda_item_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_agenda_item_t_meeting_id ON agenda_item_t (meeting_id);

ALTER TABLE assignment_t ADD CONSTRAINT fk_assignment_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_assignment_t_meeting_id ON assignment_t (meeting_id);

ALTER TABLE assignment_candidate_t ADD CONSTRAINT fk_assignment_candidate_t_assignment_id_assignment_t_id FOREIGN KEY(assignment_id) REFERENCES assignment_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_assignment_candidate_t_assignment_id ON assignment_candidate_t (assignment_id);
ALTER TABLE assignment_candidate_t ADD CONSTRAINT fk_assignment_candidate_t_meeting_user_id_meeting_user_t_id FOREIGN KEY(meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_assignment_candidate_t_meeting_user_id ON assignment_candidate_t (meeting_user_id);
ALTER TABLE assignment_candidate_t ADD CONSTRAINT fk_assignment_candidate_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_assignment_candidate_t_meeting_id ON assignment_candidate_t (meeting_id);

ALTER TABLE chat_group_t ADD CONSTRAINT fk_chat_group_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_chat_group_t_meeting_id ON chat_group_t (meeting_id);

ALTER TABLE chat_message_t ADD CONSTRAINT fk_chat_message_t_meeting_user_id_meeting_user_t_id FOREIGN KEY(meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_chat_message_t_meeting_user_id ON chat_message_t (meeting_user_id);
ALTER TABLE chat_message_t ADD CONSTRAINT fk_chat_message_t_chat_group_id_chat_group_t_id FOREIGN KEY(chat_group_id) REFERENCES chat_group_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_chat_message_t_chat_group_id ON chat_message_t (chat_group_id);
ALTER TABLE chat_message_t ADD CONSTRAINT fk_chat_message_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_chat_message_t_meeting_id ON chat_message_t (meeting_id);

ALTER TABLE committee_t ADD CONSTRAINT fk_committee_t_default_meeting_id_meeting_t_id FOREIGN KEY(default_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_committee_t_default_meeting_id ON committee_t (default_meeting_id);
ALTER TABLE committee_t ADD CONSTRAINT fk_committee_t_parent_id_committee_t_id FOREIGN KEY(parent_id) REFERENCES committee_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_committee_t_parent_id ON committee_t (parent_id);
ALTER TABLE committee_t ADD CONSTRAINT fk_committee_t_organization_id_organization_t_id FOREIGN KEY(organization_id) REFERENCES organization_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_committee_t_organization_id ON committee_t (organization_id);

ALTER TABLE gender_t ADD CONSTRAINT fk_gender_t_organization_id_organization_t_id FOREIGN KEY(organization_id) REFERENCES organization_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_gender_t_organization_id ON gender_t (organization_id);

ALTER TABLE group_t ADD CONSTRAINT fk_group_t_used_as_motion_poll_default_id_meeting_t_id FOREIGN KEY(used_as_motion_poll_default_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_group_t_used_as_motion_poll_default_id ON group_t (used_as_motion_poll_default_id);
ALTER TABLE group_t ADD CONSTRAINT fk_group_t_used_as_assignment_poll_default_id_meeting_t_id FOREIGN KEY(used_as_assignment_poll_default_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_group_t_used_as_assignment_poll_default_id ON group_t (used_as_assignment_poll_default_id);
ALTER TABLE group_t ADD CONSTRAINT fk_group_t_used_as_topic_poll_default_id_meeting_t_id FOREIGN KEY(used_as_topic_poll_default_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_group_t_used_as_topic_poll_default_id ON group_t (used_as_topic_poll_default_id);
ALTER TABLE group_t ADD CONSTRAINT fk_group_t_used_as_poll_default_id_meeting_t_id FOREIGN KEY(used_as_poll_default_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_group_t_used_as_poll_default_id ON group_t (used_as_poll_default_id);
ALTER TABLE group_t ADD CONSTRAINT fk_group_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_group_t_meeting_id ON group_t (meeting_id);

ALTER TABLE history_entry_t ADD CONSTRAINT fk_history_entry_t_model_id_user_id_user_t_id FOREIGN KEY(model_id_user_id) REFERENCES user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_history_entry_t_model_id_user_id ON history_entry_t (model_id_user_id);
ALTER TABLE history_entry_t ADD CONSTRAINT fk_history_entry_t_model_id_motion_id_motion_t_id FOREIGN KEY(model_id_motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_history_entry_t_model_id_motion_id ON history_entry_t (model_id_motion_id);
ALTER TABLE history_entry_t ADD CONSTRAINT fk_history_entry_t_model_id_assignment_id_assignment_t_id FOREIGN KEY(model_id_assignment_id) REFERENCES assignment_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_history_entry_t_model_id_assignment_id ON history_entry_t (model_id_assignment_id);
ALTER TABLE history_entry_t ADD CONSTRAINT fk_history_entry_t_position_id_history_position_t_id FOREIGN KEY(position_id) REFERENCES history_position_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_history_entry_t_position_id ON history_entry_t (position_id);
ALTER TABLE history_entry_t ADD CONSTRAINT fk_history_entry_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_history_entry_t_meeting_id ON history_entry_t (meeting_id);

ALTER TABLE history_position_t ADD CONSTRAINT fk_history_position_t_user_id_user_t_id FOREIGN KEY(user_id) REFERENCES user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_history_position_t_user_id ON history_position_t (user_id);

ALTER TABLE list_of_speakers_t ADD CONSTRAINT fk_list_of_speakers_t_content_object_id_motion_id_motion_t_id FOREIGN KEY(content_object_id_motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_list_of_speakers_t_content_object_id_motion_id ON list_of_speakers_t (content_object_id_motion_id);
ALTER TABLE list_of_speakers_t ADD CONSTRAINT fk_list_of_speakers_t_content_object_id_motion_block_id_62f90e7 FOREIGN KEY(content_object_id_motion_block_id) REFERENCES motion_block_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_list_of_speakers_t_content_object_id_motion_block_id ON list_of_speakers_t (content_object_id_motion_block_id);
ALTER TABLE list_of_speakers_t ADD CONSTRAINT fk_list_of_speakers_t_content_object_id_assignment_id_as9909666 FOREIGN KEY(content_object_id_assignment_id) REFERENCES assignment_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_list_of_speakers_t_content_object_id_assignment_id ON list_of_speakers_t (content_object_id_assignment_id);
ALTER TABLE list_of_speakers_t ADD CONSTRAINT fk_list_of_speakers_t_content_object_id_topic_id_topic_t_id FOREIGN KEY(content_object_id_topic_id) REFERENCES topic_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_list_of_speakers_t_content_object_id_topic_id ON list_of_speakers_t (content_object_id_topic_id);
ALTER TABLE list_of_speakers_t ADD CONSTRAINT fk_list_of_speakers_t_content_object_id_meeting_mediafilc591d1a FOREIGN KEY(content_object_id_meeting_mediafile_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_list_of_speakers_t_content_object_id_meeting_mediafile_id ON list_of_speakers_t (content_object_id_meeting_mediafile_id);
ALTER TABLE list_of_speakers_t ADD CONSTRAINT fk_list_of_speakers_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_list_of_speakers_t_meeting_id ON list_of_speakers_t (meeting_id);

ALTER TABLE mediafile_t ADD CONSTRAINT fk_mediafile_t_published_to_meetings_in_organization_id_471fd9a FOREIGN KEY(published_to_meetings_in_organization_id) REFERENCES organization_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_mediafile_t_published_to_meetings_in_organization_id ON mediafile_t (published_to_meetings_in_organization_id);
ALTER TABLE mediafile_t ADD CONSTRAINT fk_mediafile_t_parent_id_mediafile_t_id FOREIGN KEY(parent_id) REFERENCES mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_mediafile_t_parent_id ON mediafile_t (parent_id);
ALTER TABLE mediafile_t ADD CONSTRAINT fk_mediafile_t_owner_id_meeting_id_meeting_t_id FOREIGN KEY(owner_id_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_mediafile_t_owner_id_meeting_id ON mediafile_t (owner_id_meeting_id);
ALTER TABLE mediafile_t ADD CONSTRAINT fk_mediafile_t_owner_id_organization_id_organization_t_id FOREIGN KEY(owner_id_organization_id) REFERENCES organization_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_mediafile_t_owner_id_organization_id ON mediafile_t (owner_id_organization_id);

ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_is_active_in_organization_id_organization_t_id FOREIGN KEY(is_active_in_organization_id) REFERENCES organization_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_is_active_in_organization_id ON meeting_t (is_active_in_organization_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_is_archived_in_organization_id_organization_t_id FOREIGN KEY(is_archived_in_organization_id) REFERENCES organization_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_is_archived_in_organization_id ON meeting_t (is_archived_in_organization_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_template_for_organization_id_organization_t_id FOREIGN KEY(template_for_organization_id) REFERENCES organization_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_template_for_organization_id ON meeting_t (template_for_organization_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_motions_default_workflow_id_motion_workflow_t_id FOREIGN KEY(motions_default_workflow_id) REFERENCES motion_workflow_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_motions_default_workflow_id ON meeting_t (motions_default_workflow_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_motions_default_amendment_workflow_id_motio34ae2bf FOREIGN KEY(motions_default_amendment_workflow_id) REFERENCES motion_workflow_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_motions_default_amendment_workflow_id ON meeting_t (motions_default_amendment_workflow_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_logo_projector_main_id_meeting_mediafile_t_id FOREIGN KEY(logo_projector_main_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_logo_projector_main_id ON meeting_t (logo_projector_main_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_logo_projector_header_id_meeting_mediafile_t_id FOREIGN KEY(logo_projector_header_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_logo_projector_header_id ON meeting_t (logo_projector_header_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_logo_web_header_id_meeting_mediafile_t_id FOREIGN KEY(logo_web_header_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_logo_web_header_id ON meeting_t (logo_web_header_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_logo_pdf_header_l_id_meeting_mediafile_t_id FOREIGN KEY(logo_pdf_header_l_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_logo_pdf_header_l_id ON meeting_t (logo_pdf_header_l_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_logo_pdf_header_r_id_meeting_mediafile_t_id FOREIGN KEY(logo_pdf_header_r_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_logo_pdf_header_r_id ON meeting_t (logo_pdf_header_r_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_logo_pdf_footer_l_id_meeting_mediafile_t_id FOREIGN KEY(logo_pdf_footer_l_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_logo_pdf_footer_l_id ON meeting_t (logo_pdf_footer_l_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_logo_pdf_footer_r_id_meeting_mediafile_t_id FOREIGN KEY(logo_pdf_footer_r_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_logo_pdf_footer_r_id ON meeting_t (logo_pdf_footer_r_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_logo_pdf_ballot_paper_id_meeting_mediafile_t_id FOREIGN KEY(logo_pdf_ballot_paper_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_logo_pdf_ballot_paper_id ON meeting_t (logo_pdf_ballot_paper_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_font_regular_id_meeting_mediafile_t_id FOREIGN KEY(font_regular_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_font_regular_id ON meeting_t (font_regular_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_font_italic_id_meeting_mediafile_t_id FOREIGN KEY(font_italic_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_font_italic_id ON meeting_t (font_italic_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_font_bold_id_meeting_mediafile_t_id FOREIGN KEY(font_bold_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_font_bold_id ON meeting_t (font_bold_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_font_bold_italic_id_meeting_mediafile_t_id FOREIGN KEY(font_bold_italic_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_font_bold_italic_id ON meeting_t (font_bold_italic_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_font_monospace_id_meeting_mediafile_t_id FOREIGN KEY(font_monospace_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_font_monospace_id ON meeting_t (font_monospace_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_font_chyron_speaker_name_id_meeting_mediafile_t_id FOREIGN KEY(font_chyron_speaker_name_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_font_chyron_speaker_name_id ON meeting_t (font_chyron_speaker_name_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_font_projector_h1_id_meeting_mediafile_t_id FOREIGN KEY(font_projector_h1_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_font_projector_h1_id ON meeting_t (font_projector_h1_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_font_projector_h2_id_meeting_mediafile_t_id FOREIGN KEY(font_projector_h2_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_font_projector_h2_id ON meeting_t (font_projector_h2_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_committee_id_committee_t_id FOREIGN KEY(committee_id) REFERENCES committee_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_committee_id ON meeting_t (committee_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_reference_projector_id_projector_t_id FOREIGN KEY(reference_projector_id) REFERENCES projector_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_reference_projector_id ON meeting_t (reference_projector_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_list_of_speakers_countdown_id_projector_cou566cfb1 FOREIGN KEY(list_of_speakers_countdown_id) REFERENCES projector_countdown_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_list_of_speakers_countdown_id ON meeting_t (list_of_speakers_countdown_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_poll_countdown_id_projector_countdown_t_id FOREIGN KEY(poll_countdown_id) REFERENCES projector_countdown_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_poll_countdown_id ON meeting_t (poll_countdown_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_default_group_id_group_t_id FOREIGN KEY(default_group_id) REFERENCES group_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_default_group_id ON meeting_t (default_group_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_admin_group_id_group_t_id FOREIGN KEY(admin_group_id) REFERENCES group_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_admin_group_id ON meeting_t (admin_group_id);
ALTER TABLE meeting_t ADD CONSTRAINT fk_meeting_t_anonymous_group_id_group_t_id FOREIGN KEY(anonymous_group_id) REFERENCES group_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_t_anonymous_group_id ON meeting_t (anonymous_group_id);

ALTER TABLE meeting_mediafile_t ADD CONSTRAINT fk_meeting_mediafile_t_mediafile_id_mediafile_t_id FOREIGN KEY(mediafile_id) REFERENCES mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_mediafile_t_mediafile_id ON meeting_mediafile_t (mediafile_id);
ALTER TABLE meeting_mediafile_t ADD CONSTRAINT fk_meeting_mediafile_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_mediafile_t_meeting_id ON meeting_mediafile_t (meeting_id);

ALTER TABLE meeting_user_t ADD CONSTRAINT fk_meeting_user_t_user_id_user_t_id FOREIGN KEY(user_id) REFERENCES user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_user_t_user_id ON meeting_user_t (user_id);
ALTER TABLE meeting_user_t ADD CONSTRAINT fk_meeting_user_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_user_t_meeting_id ON meeting_user_t (meeting_id);
ALTER TABLE meeting_user_t ADD CONSTRAINT fk_meeting_user_t_vote_delegated_to_id_meeting_user_t_id FOREIGN KEY(vote_delegated_to_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_meeting_user_t_vote_delegated_to_id ON meeting_user_t (vote_delegated_to_id);

ALTER TABLE motion_t ADD CONSTRAINT fk_motion_t_lead_motion_id_motion_t_id FOREIGN KEY(lead_motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_t_lead_motion_id ON motion_t (lead_motion_id);
ALTER TABLE motion_t ADD CONSTRAINT fk_motion_t_sort_parent_id_motion_t_id FOREIGN KEY(sort_parent_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_t_sort_parent_id ON motion_t (sort_parent_id);
ALTER TABLE motion_t ADD CONSTRAINT fk_motion_t_origin_id_motion_t_id FOREIGN KEY(origin_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_t_origin_id ON motion_t (origin_id);
ALTER TABLE motion_t ADD CONSTRAINT fk_motion_t_origin_meeting_id_meeting_t_id FOREIGN KEY(origin_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_t_origin_meeting_id ON motion_t (origin_meeting_id);
ALTER TABLE motion_t ADD CONSTRAINT fk_motion_t_state_id_motion_state_t_id FOREIGN KEY(state_id) REFERENCES motion_state_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_t_state_id ON motion_t (state_id);
ALTER TABLE motion_t ADD CONSTRAINT fk_motion_t_recommendation_id_motion_state_t_id FOREIGN KEY(recommendation_id) REFERENCES motion_state_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_t_recommendation_id ON motion_t (recommendation_id);
ALTER TABLE motion_t ADD CONSTRAINT fk_motion_t_category_id_motion_category_t_id FOREIGN KEY(category_id) REFERENCES motion_category_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_t_category_id ON motion_t (category_id);
ALTER TABLE motion_t ADD CONSTRAINT fk_motion_t_block_id_motion_block_t_id FOREIGN KEY(block_id) REFERENCES motion_block_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_t_block_id ON motion_t (block_id);
ALTER TABLE motion_t ADD CONSTRAINT fk_motion_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_t_meeting_id ON motion_t (meeting_id);

ALTER TABLE motion_block_t ADD CONSTRAINT fk_motion_block_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_block_t_meeting_id ON motion_block_t (meeting_id);

ALTER TABLE motion_category_t ADD CONSTRAINT fk_motion_category_t_parent_id_motion_category_t_id FOREIGN KEY(parent_id) REFERENCES motion_category_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_category_t_parent_id ON motion_category_t (parent_id);
ALTER TABLE motion_category_t ADD CONSTRAINT fk_motion_category_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_category_t_meeting_id ON motion_category_t (meeting_id);

ALTER TABLE motion_change_recommendation_t ADD CONSTRAINT fk_motion_change_recommendation_t_motion_id_motion_t_id FOREIGN KEY(motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_change_recommendation_t_motion_id ON motion_change_recommendation_t (motion_id);
ALTER TABLE motion_change_recommendation_t ADD CONSTRAINT fk_motion_change_recommendation_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_change_recommendation_t_meeting_id ON motion_change_recommendation_t (meeting_id);

ALTER TABLE motion_comment_t ADD CONSTRAINT fk_motion_comment_t_motion_id_motion_t_id FOREIGN KEY(motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_comment_t_motion_id ON motion_comment_t (motion_id);
ALTER TABLE motion_comment_t ADD CONSTRAINT fk_motion_comment_t_section_id_motion_comment_section_t_id FOREIGN KEY(section_id) REFERENCES motion_comment_section_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_comment_t_section_id ON motion_comment_t (section_id);
ALTER TABLE motion_comment_t ADD CONSTRAINT fk_motion_comment_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_comment_t_meeting_id ON motion_comment_t (meeting_id);

ALTER TABLE motion_comment_section_t ADD CONSTRAINT fk_motion_comment_section_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_comment_section_t_meeting_id ON motion_comment_section_t (meeting_id);

ALTER TABLE motion_editor_t ADD CONSTRAINT fk_motion_editor_t_meeting_user_id_meeting_user_t_id FOREIGN KEY(meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_editor_t_meeting_user_id ON motion_editor_t (meeting_user_id);
ALTER TABLE motion_editor_t ADD CONSTRAINT fk_motion_editor_t_motion_id_motion_t_id FOREIGN KEY(motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_editor_t_motion_id ON motion_editor_t (motion_id);
ALTER TABLE motion_editor_t ADD CONSTRAINT fk_motion_editor_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_editor_t_meeting_id ON motion_editor_t (meeting_id);

ALTER TABLE motion_state_t ADD CONSTRAINT fk_motion_state_t_submitter_withdraw_state_id_motion_state_t_id FOREIGN KEY(submitter_withdraw_state_id) REFERENCES motion_state_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_state_t_submitter_withdraw_state_id ON motion_state_t (submitter_withdraw_state_id);
ALTER TABLE motion_state_t ADD CONSTRAINT fk_motion_state_t_workflow_id_motion_workflow_t_id FOREIGN KEY(workflow_id) REFERENCES motion_workflow_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_state_t_workflow_id ON motion_state_t (workflow_id);
ALTER TABLE motion_state_t ADD CONSTRAINT fk_motion_state_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_state_t_meeting_id ON motion_state_t (meeting_id);

ALTER TABLE motion_submitter_t ADD CONSTRAINT fk_motion_submitter_t_meeting_user_id_meeting_user_t_id FOREIGN KEY(meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_submitter_t_meeting_user_id ON motion_submitter_t (meeting_user_id);
ALTER TABLE motion_submitter_t ADD CONSTRAINT fk_motion_submitter_t_motion_id_motion_t_id FOREIGN KEY(motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_submitter_t_motion_id ON motion_submitter_t (motion_id);
ALTER TABLE motion_submitter_t ADD CONSTRAINT fk_motion_submitter_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_submitter_t_meeting_id ON motion_submitter_t (meeting_id);

ALTER TABLE motion_supporter_t ADD CONSTRAINT fk_motion_supporter_t_meeting_user_id_meeting_user_t_id FOREIGN KEY(meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_supporter_t_meeting_user_id ON motion_supporter_t (meeting_user_id);
ALTER TABLE motion_supporter_t ADD CONSTRAINT fk_motion_supporter_t_motion_id_motion_t_id FOREIGN KEY(motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_supporter_t_motion_id ON motion_supporter_t (motion_id);
ALTER TABLE motion_supporter_t ADD CONSTRAINT fk_motion_supporter_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_supporter_t_meeting_id ON motion_supporter_t (meeting_id);

ALTER TABLE motion_workflow_t ADD CONSTRAINT fk_motion_workflow_t_first_state_id_motion_state_t_id FOREIGN KEY(first_state_id) REFERENCES motion_state_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_workflow_t_first_state_id ON motion_workflow_t (first_state_id);
ALTER TABLE motion_workflow_t ADD CONSTRAINT fk_motion_workflow_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_workflow_t_meeting_id ON motion_workflow_t (meeting_id);

ALTER TABLE motion_working_group_speaker_t ADD CONSTRAINT fk_motion_working_group_speaker_t_meeting_user_id_meetinbc3a7bb FOREIGN KEY(meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_working_group_speaker_t_meeting_user_id ON motion_working_group_speaker_t (meeting_user_id);
ALTER TABLE motion_working_group_speaker_t ADD CONSTRAINT fk_motion_working_group_speaker_t_motion_id_motion_t_id FOREIGN KEY(motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_working_group_speaker_t_motion_id ON motion_working_group_speaker_t (motion_id);
ALTER TABLE motion_working_group_speaker_t ADD CONSTRAINT fk_motion_working_group_speaker_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_motion_working_group_speaker_t_meeting_id ON motion_working_group_speaker_t (meeting_id);

ALTER TABLE option_t ADD CONSTRAINT fk_option_t_poll_id_poll_t_id FOREIGN KEY(poll_id) REFERENCES poll_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_option_t_poll_id ON option_t (poll_id);
ALTER TABLE option_t ADD CONSTRAINT fk_option_t_content_object_id_motion_id_motion_t_id FOREIGN KEY(content_object_id_motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_option_t_content_object_id_motion_id ON option_t (content_object_id_motion_id);
ALTER TABLE option_t ADD CONSTRAINT fk_option_t_content_object_id_user_id_user_t_id FOREIGN KEY(content_object_id_user_id) REFERENCES user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_option_t_content_object_id_user_id ON option_t (content_object_id_user_id);
ALTER TABLE option_t ADD CONSTRAINT fk_option_t_content_object_id_poll_candidate_list_id_pold428251 FOREIGN KEY(content_object_id_poll_candidate_list_id) REFERENCES poll_candidate_list_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_option_t_content_object_id_poll_candidate_list_id ON option_t (content_object_id_poll_candidate_list_id);
ALTER TABLE option_t ADD CONSTRAINT fk_option_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_option_t_meeting_id ON option_t (meeting_id);

ALTER TABLE organization_t ADD CONSTRAINT fk_organization_t_theme_id_theme_t_id FOREIGN KEY(theme_id) REFERENCES theme_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_organization_t_theme_id ON organization_t (theme_id);

ALTER TABLE organization_tag_t ADD CONSTRAINT fk_organization_tag_t_organization_id_organization_t_id FOREIGN KEY(organization_id) REFERENCES organization_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_organization_tag_t_organization_id ON organization_tag_t (organization_id);

ALTER TABLE personal_note_t ADD CONSTRAINT fk_personal_note_t_meeting_user_id_meeting_user_t_id FOREIGN KEY(meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_personal_note_t_meeting_user_id ON personal_note_t (meeting_user_id);
ALTER TABLE personal_note_t ADD CONSTRAINT fk_personal_note_t_content_object_id_motion_id_motion_t_id FOREIGN KEY(content_object_id_motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_personal_note_t_content_object_id_motion_id ON personal_note_t (content_object_id_motion_id);
ALTER TABLE personal_note_t ADD CONSTRAINT fk_personal_note_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_personal_note_t_meeting_id ON personal_note_t (meeting_id);

ALTER TABLE point_of_order_category_t ADD CONSTRAINT fk_point_of_order_category_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_point_of_order_category_t_meeting_id ON point_of_order_category_t (meeting_id);

ALTER TABLE poll_t ADD CONSTRAINT fk_poll_t_content_object_id_motion_id_motion_t_id FOREIGN KEY(content_object_id_motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_t_content_object_id_motion_id ON poll_t (content_object_id_motion_id);
ALTER TABLE poll_t ADD CONSTRAINT fk_poll_t_content_object_id_assignment_id_assignment_t_id FOREIGN KEY(content_object_id_assignment_id) REFERENCES assignment_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_t_content_object_id_assignment_id ON poll_t (content_object_id_assignment_id);
ALTER TABLE poll_t ADD CONSTRAINT fk_poll_t_content_object_id_topic_id_topic_t_id FOREIGN KEY(content_object_id_topic_id) REFERENCES topic_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_t_content_object_id_topic_id ON poll_t (content_object_id_topic_id);
ALTER TABLE poll_t ADD CONSTRAINT fk_poll_t_global_option_id_option_t_id FOREIGN KEY(global_option_id) REFERENCES option_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_t_global_option_id ON poll_t (global_option_id);
ALTER TABLE poll_t ADD CONSTRAINT fk_poll_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_t_meeting_id ON poll_t (meeting_id);

ALTER TABLE poll_candidate_t ADD CONSTRAINT fk_poll_candidate_t_poll_candidate_list_id_poll_candidat7fec070 FOREIGN KEY(poll_candidate_list_id) REFERENCES poll_candidate_list_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_candidate_t_poll_candidate_list_id ON poll_candidate_t (poll_candidate_list_id);
ALTER TABLE poll_candidate_t ADD CONSTRAINT fk_poll_candidate_t_user_id_user_t_id FOREIGN KEY(user_id) REFERENCES user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_candidate_t_user_id ON poll_candidate_t (user_id);
ALTER TABLE poll_candidate_t ADD CONSTRAINT fk_poll_candidate_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_candidate_t_meeting_id ON poll_candidate_t (meeting_id);

ALTER TABLE poll_candidate_list_t ADD CONSTRAINT fk_poll_candidate_list_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_poll_candidate_list_t_meeting_id ON poll_candidate_list_t (meeting_id);

ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_current_projector_id_projector_t_id FOREIGN KEY(current_projector_id) REFERENCES projector_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_current_projector_id ON projection_t (current_projector_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_preview_projector_id_projector_t_id FOREIGN KEY(preview_projector_id) REFERENCES projector_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_preview_projector_id ON projection_t (preview_projector_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_history_projector_id_projector_t_id FOREIGN KEY(history_projector_id) REFERENCES projector_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_history_projector_id ON projection_t (history_projector_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_meeting_id_meeting_t_id FOREIGN KEY(content_object_id_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_meeting_id ON projection_t (content_object_id_meeting_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_motion_id_motion_t_id FOREIGN KEY(content_object_id_motion_id) REFERENCES motion_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_motion_id ON projection_t (content_object_id_motion_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_meeting_mediafile_id_m09270d6 FOREIGN KEY(content_object_id_meeting_mediafile_id) REFERENCES meeting_mediafile_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_meeting_mediafile_id ON projection_t (content_object_id_meeting_mediafile_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_list_of_speakers_id_li392b5e1 FOREIGN KEY(content_object_id_list_of_speakers_id) REFERENCES list_of_speakers_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_list_of_speakers_id ON projection_t (content_object_id_list_of_speakers_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_motion_block_id_motioncbb3c5b FOREIGN KEY(content_object_id_motion_block_id) REFERENCES motion_block_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_motion_block_id ON projection_t (content_object_id_motion_block_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_assignment_id_assignment_t_id FOREIGN KEY(content_object_id_assignment_id) REFERENCES assignment_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_assignment_id ON projection_t (content_object_id_assignment_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_agenda_item_id_agenda_bd5d814 FOREIGN KEY(content_object_id_agenda_item_id) REFERENCES agenda_item_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_agenda_item_id ON projection_t (content_object_id_agenda_item_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_topic_id_topic_t_id FOREIGN KEY(content_object_id_topic_id) REFERENCES topic_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_topic_id ON projection_t (content_object_id_topic_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_poll_id_poll_t_id FOREIGN KEY(content_object_id_poll_id) REFERENCES poll_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_poll_id ON projection_t (content_object_id_poll_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_projector_message_id_p5c0a05e FOREIGN KEY(content_object_id_projector_message_id) REFERENCES projector_message_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_projector_message_id ON projection_t (content_object_id_projector_message_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_content_object_id_projector_countdown_id1942f3a FOREIGN KEY(content_object_id_projector_countdown_id) REFERENCES projector_countdown_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_content_object_id_projector_countdown_id ON projection_t (content_object_id_projector_countdown_id);
ALTER TABLE projection_t ADD CONSTRAINT fk_projection_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projection_t_meeting_id ON projection_t (meeting_id);

ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_agenda_itemca4cc75 FOREIGN KEY(used_as_default_projector_for_agenda_item_list_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_agenda_ite41b5bd9 ON projector_t (used_as_default_projector_for_agenda_item_list_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_topic_in_me0971ea7 FOREIGN KEY(used_as_default_projector_for_topic_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_topic_in_mab361e8 ON projector_t (used_as_default_projector_for_topic_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_list_of_spe619d36f FOREIGN KEY(used_as_default_projector_for_list_of_speakers_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_list_of_spb099704 ON projector_t (used_as_default_projector_for_list_of_speakers_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_current_lose8cefef FOREIGN KEY(used_as_default_projector_for_current_los_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_current_locdd5b27 ON projector_t (used_as_default_projector_for_current_los_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_motion_in_m3a0e1e4 FOREIGN KEY(used_as_default_projector_for_motion_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_motion_in_f66691f ON projector_t (used_as_default_projector_for_motion_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_amendment_i4b417bf FOREIGN KEY(used_as_default_projector_for_amendment_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_amendment_2235e12 ON projector_t (used_as_default_projector_for_amendment_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_motion_blocd05a71e FOREIGN KEY(used_as_default_projector_for_motion_block_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_motion_blo7b0c3c8 ON projector_t (used_as_default_projector_for_motion_block_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_assignment_ddcffde FOREIGN KEY(used_as_default_projector_for_assignment_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_assignment78622ce ON projector_t (used_as_default_projector_for_assignment_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_mediafile_i9b33fdb FOREIGN KEY(used_as_default_projector_for_mediafile_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_mediafile_1c31a99 ON projector_t (used_as_default_projector_for_mediafile_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_message_in_21dcbf0 FOREIGN KEY(used_as_default_projector_for_message_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_message_in339958e ON projector_t (used_as_default_projector_for_message_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_countdown_if9b333e FOREIGN KEY(used_as_default_projector_for_countdown_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_countdown_07665b4 ON projector_t (used_as_default_projector_for_countdown_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_assignment_8b61ac6 FOREIGN KEY(used_as_default_projector_for_assignment_poll_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_assignment5a08584 ON projector_t (used_as_default_projector_for_assignment_poll_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_motion_poll5bff78e FOREIGN KEY(used_as_default_projector_for_motion_poll_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_motion_pol0605aa8 ON projector_t (used_as_default_projector_for_motion_poll_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_used_as_default_projector_for_poll_in_mee417a148 FOREIGN KEY(used_as_default_projector_for_poll_in_meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_used_as_default_projector_for_poll_in_me446bdba ON projector_t (used_as_default_projector_for_poll_in_meeting_id);
ALTER TABLE projector_t ADD CONSTRAINT fk_projector_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_t_meeting_id ON projector_t (meeting_id);

ALTER TABLE projector_countdown_t ADD CONSTRAINT fk_projector_countdown_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_countdown_t_meeting_id ON projector_countdown_t (meeting_id);

ALTER TABLE projector_message_t ADD CONSTRAINT fk_projector_message_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_projector_message_t_meeting_id ON projector_message_t (meeting_id);

ALTER TABLE speaker_t ADD CONSTRAINT fk_speaker_t_list_of_speakers_id_list_of_speakers_t_id FOREIGN KEY(list_of_speakers_id) REFERENCES list_of_speakers_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_speaker_t_list_of_speakers_id ON speaker_t (list_of_speakers_id);
ALTER TABLE speaker_t ADD CONSTRAINT fk_speaker_t_structure_level_list_of_speakers_id_structu559f22d FOREIGN KEY(structure_level_list_of_speakers_id) REFERENCES structure_level_list_of_speakers_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_speaker_t_structure_level_list_of_speakers_id ON speaker_t (structure_level_list_of_speakers_id);
ALTER TABLE speaker_t ADD CONSTRAINT fk_speaker_t_meeting_user_id_meeting_user_t_id FOREIGN KEY(meeting_user_id) REFERENCES meeting_user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_speaker_t_meeting_user_id ON speaker_t (meeting_user_id);
ALTER TABLE speaker_t ADD CONSTRAINT fk_speaker_t_point_of_order_category_id_point_of_order_ce6dbc9a FOREIGN KEY(point_of_order_category_id) REFERENCES point_of_order_category_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_speaker_t_point_of_order_category_id ON speaker_t (point_of_order_category_id);
ALTER TABLE speaker_t ADD CONSTRAINT fk_speaker_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_speaker_t_meeting_id ON speaker_t (meeting_id);

ALTER TABLE structure_level_t ADD CONSTRAINT fk_structure_level_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_structure_level_t_meeting_id ON structure_level_t (meeting_id);

ALTER TABLE structure_level_list_of_speakers_t ADD CONSTRAINT fk_structure_level_list_of_speakers_t_structure_level_idee3e20c FOREIGN KEY(structure_level_id) REFERENCES structure_level_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_structure_level_list_of_speakers_t_structure_level_id ON structure_level_list_of_speakers_t (structure_level_id);
ALTER TABLE structure_level_list_of_speakers_t ADD CONSTRAINT fk_structure_level_list_of_speakers_t_list_of_speakers_idbd2794 FOREIGN KEY(list_of_speakers_id) REFERENCES list_of_speakers_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_structure_level_list_of_speakers_t_list_of_speakers_id ON structure_level_list_of_speakers_t (list_of_speakers_id);
ALTER TABLE structure_level_list_of_speakers_t ADD CONSTRAINT fk_structure_level_list_of_speakers_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_structure_level_list_of_speakers_t_meeting_id ON structure_level_list_of_speakers_t (meeting_id);

ALTER TABLE tag_t ADD CONSTRAINT fk_tag_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_tag_t_meeting_id ON tag_t (meeting_id);

ALTER TABLE theme_t ADD CONSTRAINT fk_theme_t_organization_id_organization_t_id FOREIGN KEY(organization_id) REFERENCES organization_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_theme_t_organization_id ON theme_t (organization_id);

ALTER TABLE topic_t ADD CONSTRAINT fk_topic_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_topic_t_meeting_id ON topic_t (meeting_id);

ALTER TABLE user_t ADD CONSTRAINT fk_user_t_gender_id_gender_t_id FOREIGN KEY(gender_id) REFERENCES gender_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_user_t_gender_id ON user_t (gender_id);
ALTER TABLE user_t ADD CONSTRAINT fk_user_t_home_committee_id_committee_t_id FOREIGN KEY(home_committee_id) REFERENCES committee_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_user_t_home_committee_id ON user_t (home_committee_id);
ALTER TABLE user_t ADD CONSTRAINT fk_user_t_organization_id_organization_t_id FOREIGN KEY(organization_id) REFERENCES organization_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_user_t_organization_id ON user_t (organization_id);

ALTER TABLE vote_t ADD CONSTRAINT fk_vote_t_option_id_option_t_id FOREIGN KEY(option_id) REFERENCES option_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_vote_t_option_id ON vote_t (option_id);
ALTER TABLE vote_t ADD CONSTRAINT fk_vote_t_user_id_user_t_id FOREIGN KEY(user_id) REFERENCES user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_vote_t_user_id ON vote_t (user_id);
ALTER TABLE vote_t ADD CONSTRAINT fk_vote_t_delegated_user_id_user_t_id FOREIGN KEY(delegated_user_id) REFERENCES user_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_vote_t_delegated_user_id ON vote_t (delegated_user_id);
ALTER TABLE vote_t ADD CONSTRAINT fk_vote_t_meeting_id_meeting_t_id FOREIGN KEY(meeting_id) REFERENCES meeting_t(id) INITIALLY DEFERRED;
CREATE INDEX idx_vote_t_meeting_id ON vote_t (meeting_id);



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
CREATE TRIGGER tr_log_action_worker AFTER INSERT OR UPDATE OR DELETE ON action_worker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('action_worker');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON action_worker_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_agenda_item AFTER INSERT OR UPDATE OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('agenda_item');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON agenda_item_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','agenda_item_id');

CREATE TRIGGER tr_log_motion_block_content_object_id_motion_block_id AFTER INSERT OR UPDATE OF content_object_id_motion_block_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_block','content_object_id_motion_block_id','agenda_item_id');

CREATE TRIGGER tr_log_assignment_content_object_id_assignment_id AFTER INSERT OR UPDATE OF content_object_id_assignment_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment','content_object_id_assignment_id','agenda_item_id');

CREATE TRIGGER tr_log_topic_content_object_id_topic_id AFTER INSERT OR UPDATE OF content_object_id_topic_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('topic','content_object_id_topic_id','agenda_item_id');
CREATE TRIGGER tr_log_agenda_item_t_parent_id AFTER INSERT OR UPDATE OF parent_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('agenda_item', 'parent_id', 'child_ids');
CREATE TRIGGER tr_log_agenda_item_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON agenda_item_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'agenda_item_ids');

CREATE TRIGGER tr_log_assignment AFTER INSERT OR UPDATE OR DELETE ON assignment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('assignment');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON assignment_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_assignment_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON assignment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'assignment_ids');

CREATE TRIGGER tr_log_assignment_candidate AFTER INSERT OR UPDATE OR DELETE ON assignment_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('assignment_candidate');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON assignment_candidate_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_assignment_candidate_t_assignment_id AFTER INSERT OR UPDATE OF assignment_id OR DELETE ON assignment_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment', 'assignment_id', 'candidate_ids');
CREATE TRIGGER tr_log_assignment_candidate_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON assignment_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'assignment_candidate_ids');
CREATE TRIGGER tr_log_assignment_candidate_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON assignment_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'assignment_candidate_ids');

CREATE TRIGGER tr_log_chat_group AFTER INSERT OR UPDATE OR DELETE ON chat_group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('chat_group');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON chat_group_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


CREATE TRIGGER tr_log_nm_chat_group_read_group_ids_group_t AFTER INSERT OR UPDATE OR DELETE ON nm_chat_group_read_group_ids_group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('chat_group','chat_group_id','read_group_ids','group','group_id','read_chat_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_chat_group_read_group_ids_group_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_nm_chat_group_write_group_ids_group_t AFTER INSERT OR UPDATE OR DELETE ON nm_chat_group_write_group_ids_group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('chat_group','chat_group_id','write_group_ids','group','group_id','write_chat_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_chat_group_write_group_ids_group_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
CREATE TRIGGER tr_log_chat_group_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON chat_group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'chat_group_ids');

CREATE TRIGGER tr_log_chat_message AFTER INSERT OR UPDATE OR DELETE ON chat_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('chat_message');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON chat_message_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_chat_message_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON chat_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'chat_message_ids');
CREATE TRIGGER tr_log_chat_message_t_chat_group_id AFTER INSERT OR UPDATE OF chat_group_id OR DELETE ON chat_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('chat_group', 'chat_group_id', 'chat_message_ids');
CREATE TRIGGER tr_log_chat_message_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON chat_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'chat_message_ids');

CREATE TRIGGER tr_log_committee AFTER INSERT OR UPDATE OR DELETE ON committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('committee');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON committee_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_committee_t_default_meeting_id AFTER INSERT OR UPDATE OF default_meeting_id OR DELETE ON committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'default_meeting_id', 'default_meeting_for_committee_id');

CREATE TRIGGER tr_log_i_committee_user_ids_from_meeting_user_t BEFORE INSERT ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('committee', '', 'SELECT committee_id FROM meeting_t WHERE id = ($1).meeting_id', 'user_ids', 'user_id', '');
CREATE TRIGGER tr_log_d_committee_user_ids_from_meeting_user_t AFTER DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('committee', '', 'SELECT committee_id FROM meeting_t WHERE id = ($1).meeting_id', 'user_ids', 'user_id', '');
CREATE TRIGGER tr_log_i_committee_user_ids_from_nm_committee_manager_idd4a2a53 BEFORE INSERT ON nm_committee_manager_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('committee', 'committee_id', '', 'user_ids', 'user_id', '');
CREATE TRIGGER tr_log_d_committee_user_ids_from_nm_committee_manager_id82dfd00 AFTER DELETE ON nm_committee_manager_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('committee', 'committee_id', '', 'user_ids', 'user_id', '');
CREATE TRIGGER tr_log_iu_committee_user_ids_from_user_t BEFORE INSERT OR UPDATE OF home_committee_id ON user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('committee', 'home_committee_id', '', 'user_ids', 'id', '');
CREATE TRIGGER tr_log_ud_committee_user_ids_from_user_t AFTER UPDATE OF home_committee_id OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('committee', 'home_committee_id', '', 'user_ids', 'id', '');


CREATE TRIGGER tr_log_nm_committee_manager_ids_user_t AFTER INSERT OR UPDATE OR DELETE ON nm_committee_manager_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee','committee_id','manager_ids','user','user_id','committee_management_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_committee_manager_ids_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
CREATE TRIGGER tr_log_committee_t_parent_id AFTER INSERT OR UPDATE OF parent_id OR DELETE ON committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee', 'parent_id', 'child_ids');

CREATE TRIGGER tr_log_nm_committee_all_child_ids_committee_t AFTER INSERT OR UPDATE OR DELETE ON nm_committee_all_child_ids_committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee','all_parent_id','all_child_ids','committee','all_child_id','all_parent_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_committee_all_child_ids_committee_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_nm_committee_forward_to_committee_ids_committee_t AFTER INSERT OR UPDATE OR DELETE ON nm_committee_forward_to_committee_ids_committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee','receive_forwardings_from_committee_id','forward_to_committee_ids','committee','forward_to_committee_id','receive_forwardings_from_committee_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_committee_forward_to_committee_ids_committee_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
CREATE TRIGGER tr_log_committee_t_organization_id AFTER INSERT OR UPDATE OF organization_id OR DELETE ON committee_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'organization_id', 'committee_ids');

CREATE TRIGGER tr_log_gender AFTER INSERT OR UPDATE OR DELETE ON gender_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('gender');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gender_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_gender_t_organization_id AFTER INSERT OR UPDATE OF organization_id OR DELETE ON gender_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'organization_id', 'gender_ids');

CREATE TRIGGER tr_log_group AFTER INSERT OR UPDATE OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('group');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON group_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


CREATE TRIGGER tr_log_nm_group_meeting_user_ids_meeting_user_t AFTER INSERT OR UPDATE OR DELETE ON nm_group_meeting_user_ids_meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','meeting_user_ids','meeting_user','meeting_user_id','group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_meeting_user_ids_meeting_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_nm_group_mmagi_meeting_mediafile_t AFTER INSERT OR UPDATE OR DELETE ON nm_group_mmagi_meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','meeting_mediafile_access_group_ids','meeting_mediafile','meeting_mediafile_id','access_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_mmagi_meeting_mediafile_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_nm_group_mmiagi_meeting_mediafile_t AFTER INSERT OR UPDATE OR DELETE ON nm_group_mmiagi_meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','meeting_mediafile_inherited_access_group_ids','meeting_mediafile','meeting_mediafile_id','inherited_access_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_mmiagi_meeting_mediafile_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_nm_group_read_comment_section_ids_motion_comment_6e42c77 AFTER INSERT OR UPDATE OR DELETE ON nm_group_read_comment_section_ids_motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','read_comment_section_ids','motion_comment_section','motion_comment_section_id','read_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_read_comment_section_ids_motion_comment_section_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_nm_group_write_comment_section_ids_motion_commentb627a2e AFTER INSERT OR UPDATE OR DELETE ON nm_group_write_comment_section_ids_motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','write_comment_section_ids','motion_comment_section','motion_comment_section_id','write_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_write_comment_section_ids_motion_comment_section_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_nm_group_poll_ids_poll_t AFTER INSERT OR UPDATE OR DELETE ON nm_group_poll_ids_poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group','group_id','poll_ids','poll','poll_id','entitled_group_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_group_poll_ids_poll_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
CREATE TRIGGER tr_log_group_t_used_as_motion_poll_default_id AFTER INSERT OR UPDATE OF used_as_motion_poll_default_id OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_motion_poll_default_id', 'motion_poll_default_group_ids');
CREATE TRIGGER tr_log_group_t_used_as_assignment_poll_default_id AFTER INSERT OR UPDATE OF used_as_assignment_poll_default_id OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_assignment_poll_default_id', 'assignment_poll_default_group_ids');
CREATE TRIGGER tr_log_group_t_used_as_topic_poll_default_id AFTER INSERT OR UPDATE OF used_as_topic_poll_default_id OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_topic_poll_default_id', 'topic_poll_default_group_ids');
CREATE TRIGGER tr_log_group_t_used_as_poll_default_id AFTER INSERT OR UPDATE OF used_as_poll_default_id OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_poll_default_id', 'poll_default_group_ids');
CREATE TRIGGER tr_log_group_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON group_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'group_ids');

CREATE TRIGGER tr_log_history_entry AFTER INSERT OR UPDATE OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('history_entry');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON history_entry_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


CREATE TRIGGER tr_log_user_model_id_user_id AFTER INSERT OR UPDATE OF model_id_user_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user','model_id_user_id','history_entry_ids');

CREATE TRIGGER tr_log_motion_model_id_motion_id AFTER INSERT OR UPDATE OF model_id_motion_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','model_id_motion_id','history_entry_ids');

CREATE TRIGGER tr_log_assignment_model_id_assignment_id AFTER INSERT OR UPDATE OF model_id_assignment_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment','model_id_assignment_id','history_entry_ids');
CREATE TRIGGER tr_log_history_entry_t_position_id AFTER INSERT OR UPDATE OF position_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('history_position', 'position_id', 'entry_ids');
CREATE TRIGGER tr_log_history_entry_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'relevant_history_entry_ids');

CREATE TRIGGER tr_log_history_position AFTER INSERT OR UPDATE OR DELETE ON history_position_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('history_position');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON history_position_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_history_position_t_user_id AFTER INSERT OR UPDATE OF user_id OR DELETE ON history_position_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user', 'user_id', 'history_position_ids');

CREATE TRIGGER tr_log_import_preview AFTER INSERT OR UPDATE OR DELETE ON import_preview_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('import_preview');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON import_preview_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_list_of_speakers AFTER INSERT OR UPDATE OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('list_of_speakers');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON list_of_speakers_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','list_of_speakers_id');

CREATE TRIGGER tr_log_motion_block_content_object_id_motion_block_id AFTER INSERT OR UPDATE OF content_object_id_motion_block_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_block','content_object_id_motion_block_id','list_of_speakers_id');

CREATE TRIGGER tr_log_assignment_content_object_id_assignment_id AFTER INSERT OR UPDATE OF content_object_id_assignment_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment','content_object_id_assignment_id','list_of_speakers_id');

CREATE TRIGGER tr_log_topic_content_object_id_topic_id AFTER INSERT OR UPDATE OF content_object_id_topic_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('topic','content_object_id_topic_id','list_of_speakers_id');

CREATE TRIGGER tr_log_meeting_mediafile_content_object_id_meeting_mediafile_id AFTER INSERT OR UPDATE OF content_object_id_meeting_mediafile_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile','content_object_id_meeting_mediafile_id','list_of_speakers_id');
CREATE TRIGGER tr_log_list_of_speakers_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'list_of_speakers_ids');

CREATE TRIGGER tr_log_mediafile AFTER INSERT OR UPDATE OR DELETE ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('mediafile');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON mediafile_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_mediafile_t_published_to_meetings_in_organization_id AFTER INSERT OR UPDATE OF published_to_meetings_in_organization_id OR DELETE ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'published_to_meetings_in_organization_id', 'published_mediafile_ids');
CREATE TRIGGER tr_log_mediafile_t_parent_id AFTER INSERT OR UPDATE OF parent_id OR DELETE ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('mediafile', 'parent_id', 'child_ids');

CREATE TRIGGER tr_log_meeting_owner_id_meeting_id AFTER INSERT OR UPDATE OF owner_id_meeting_id OR DELETE ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting','owner_id_meeting_id','mediafile_ids');

CREATE TRIGGER tr_log_organization_owner_id_organization_id AFTER INSERT OR UPDATE OF owner_id_organization_id OR DELETE ON mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization','owner_id_organization_id','mediafile_ids');

CREATE TRIGGER tr_log_meeting AFTER INSERT OR UPDATE OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('meeting');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON meeting_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_meeting_t_is_active_in_organization_id AFTER INSERT OR UPDATE OF is_active_in_organization_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'is_active_in_organization_id', 'active_meeting_ids');
CREATE TRIGGER tr_log_meeting_t_is_archived_in_organization_id AFTER INSERT OR UPDATE OF is_archived_in_organization_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'is_archived_in_organization_id', 'archived_meeting_ids');
CREATE TRIGGER tr_log_meeting_t_template_for_organization_id AFTER INSERT OR UPDATE OF template_for_organization_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'template_for_organization_id', 'template_meeting_ids');
CREATE TRIGGER tr_log_meeting_t_motions_default_workflow_id AFTER INSERT OR UPDATE OF motions_default_workflow_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_workflow', 'motions_default_workflow_id', 'default_workflow_meeting_id');
CREATE TRIGGER tr_log_meeting_t_motions_default_amendment_workflow_id AFTER INSERT OR UPDATE OF motions_default_amendment_workflow_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_workflow', 'motions_default_amendment_workflow_id', 'default_amendment_workflow_meeting_id');
CREATE TRIGGER tr_log_meeting_t_logo_projector_main_id AFTER INSERT OR UPDATE OF logo_projector_main_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_projector_main_id', 'used_as_logo_projector_main_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_logo_projector_header_id AFTER INSERT OR UPDATE OF logo_projector_header_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_projector_header_id', 'used_as_logo_projector_header_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_logo_web_header_id AFTER INSERT OR UPDATE OF logo_web_header_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_web_header_id', 'used_as_logo_web_header_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_logo_pdf_header_l_id AFTER INSERT OR UPDATE OF logo_pdf_header_l_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_pdf_header_l_id', 'used_as_logo_pdf_header_l_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_logo_pdf_header_r_id AFTER INSERT OR UPDATE OF logo_pdf_header_r_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_pdf_header_r_id', 'used_as_logo_pdf_header_r_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_logo_pdf_footer_l_id AFTER INSERT OR UPDATE OF logo_pdf_footer_l_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_pdf_footer_l_id', 'used_as_logo_pdf_footer_l_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_logo_pdf_footer_r_id AFTER INSERT OR UPDATE OF logo_pdf_footer_r_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_pdf_footer_r_id', 'used_as_logo_pdf_footer_r_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_logo_pdf_ballot_paper_id AFTER INSERT OR UPDATE OF logo_pdf_ballot_paper_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'logo_pdf_ballot_paper_id', 'used_as_logo_pdf_ballot_paper_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_font_regular_id AFTER INSERT OR UPDATE OF font_regular_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_regular_id', 'used_as_font_regular_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_font_italic_id AFTER INSERT OR UPDATE OF font_italic_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_italic_id', 'used_as_font_italic_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_font_bold_id AFTER INSERT OR UPDATE OF font_bold_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_bold_id', 'used_as_font_bold_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_font_bold_italic_id AFTER INSERT OR UPDATE OF font_bold_italic_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_bold_italic_id', 'used_as_font_bold_italic_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_font_monospace_id AFTER INSERT OR UPDATE OF font_monospace_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_monospace_id', 'used_as_font_monospace_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_font_chyron_speaker_name_id AFTER INSERT OR UPDATE OF font_chyron_speaker_name_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_chyron_speaker_name_id', 'used_as_font_chyron_speaker_name_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_font_projector_h1_id AFTER INSERT OR UPDATE OF font_projector_h1_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_projector_h1_id', 'used_as_font_projector_h1_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_font_projector_h2_id AFTER INSERT OR UPDATE OF font_projector_h2_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile', 'font_projector_h2_id', 'used_as_font_projector_h2_in_meeting_id');
CREATE TRIGGER tr_log_meeting_t_committee_id AFTER INSERT OR UPDATE OF committee_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee', 'committee_id', 'meeting_ids');

CREATE TRIGGER tr_log_nm_meeting_present_user_ids_user_t AFTER INSERT OR UPDATE OR DELETE ON nm_meeting_present_user_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting','meeting_id','present_user_ids','user','user_id','is_present_in_meeting_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_meeting_present_user_ids_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_i_meeting_user_ids_from_meeting_user_t BEFORE INSERT ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('meeting', 'meeting_id', '', 'user_ids', 'user_id', '');
CREATE TRIGGER tr_log_d_meeting_user_ids_from_meeting_user_t AFTER DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('meeting', 'meeting_id', '', 'user_ids', 'user_id', '');

CREATE TRIGGER tr_log_meeting_t_reference_projector_id AFTER INSERT OR UPDATE OF reference_projector_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector', 'reference_projector_id', 'used_as_reference_projector_meeting_id');
CREATE TRIGGER tr_log_meeting_t_list_of_speakers_countdown_id AFTER INSERT OR UPDATE OF list_of_speakers_countdown_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector_countdown', 'list_of_speakers_countdown_id', 'used_as_list_of_speakers_countdown_meeting_id');
CREATE TRIGGER tr_log_meeting_t_poll_countdown_id AFTER INSERT OR UPDATE OF poll_countdown_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector_countdown', 'poll_countdown_id', 'used_as_poll_countdown_meeting_id');
CREATE TRIGGER tr_log_meeting_t_default_group_id AFTER INSERT OR UPDATE OF default_group_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group', 'default_group_id', 'default_group_for_meeting_id');
CREATE TRIGGER tr_log_meeting_t_admin_group_id AFTER INSERT OR UPDATE OF admin_group_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group', 'admin_group_id', 'admin_group_for_meeting_id');
CREATE TRIGGER tr_log_meeting_t_anonymous_group_id AFTER INSERT OR UPDATE OF anonymous_group_id OR DELETE ON meeting_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('group', 'anonymous_group_id', 'anonymous_group_for_meeting_id');

CREATE TRIGGER tr_log_meeting_mediafile AFTER INSERT OR UPDATE OR DELETE ON meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('meeting_mediafile');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON meeting_mediafile_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_meeting_mediafile_t_mediafile_id AFTER INSERT OR UPDATE OF mediafile_id OR DELETE ON meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('mediafile', 'mediafile_id', 'meeting_mediafile_ids');
CREATE TRIGGER tr_log_meeting_mediafile_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON meeting_mediafile_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'meeting_mediafile_ids');

CREATE TRIGGER tr_log_attachment_id_motion_id_gm_meeting_mediafile_atta25df47a AFTER INSERT OR UPDATE OF attachment_id_motion_id OR DELETE ON gm_meeting_mediafile_attachment_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile','meeting_mediafile_id','attachment_ids','motion','attachment_id_motion_id','attachment_meeting_mediafile_ids');

CREATE TRIGGER tr_log_attachment_id_topic_id_gm_meeting_mediafile_attac4e93703 AFTER INSERT OR UPDATE OF attachment_id_topic_id OR DELETE ON gm_meeting_mediafile_attachment_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile','meeting_mediafile_id','attachment_ids','topic','attachment_id_topic_id','attachment_meeting_mediafile_ids');

CREATE TRIGGER tr_log_attachment_id_assignment_id_gm_meeting_mediafile_2f214fd AFTER INSERT OR UPDATE OF attachment_id_assignment_id OR DELETE ON gm_meeting_mediafile_attachment_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile','meeting_mediafile_id','attachment_ids','assignment','attachment_id_assignment_id','attachment_meeting_mediafile_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gm_meeting_mediafile_attachment_ids_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_meeting_user AFTER INSERT OR UPDATE OR DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('meeting_user');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON meeting_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_meeting_user_t_user_id AFTER INSERT OR UPDATE OF user_id OR DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user', 'user_id', 'meeting_user_ids');
CREATE TRIGGER tr_log_meeting_user_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'meeting_user_ids');
CREATE TRIGGER tr_log_meeting_user_t_vote_delegated_to_id AFTER INSERT OR UPDATE OF vote_delegated_to_id OR DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'vote_delegated_to_id', 'vote_delegations_from_ids');

CREATE TRIGGER tr_log_nm_meeting_user_structure_level_ids_structure_level_t AFTER INSERT OR UPDATE OR DELETE ON nm_meeting_user_structure_level_ids_structure_level_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user','meeting_user_id','structure_level_ids','structure_level','structure_level_id','meeting_user_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_meeting_user_structure_level_ids_structure_level_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion AFTER INSERT OR UPDATE OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_t_lead_motion_id AFTER INSERT OR UPDATE OF lead_motion_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'lead_motion_id', 'amendment_ids');
CREATE TRIGGER tr_log_motion_t_sort_parent_id AFTER INSERT OR UPDATE OF sort_parent_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'sort_parent_id', 'sort_child_ids');
CREATE TRIGGER tr_log_motion_t_origin_id AFTER INSERT OR UPDATE OF origin_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'origin_id', 'derived_motion_ids');
CREATE TRIGGER tr_log_motion_t_origin_meeting_id AFTER INSERT OR UPDATE OF origin_meeting_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'origin_meeting_id', 'forwarded_motion_ids');

CREATE TRIGGER tr_log_nm_motion_all_derived_motion_ids_motion_t AFTER INSERT OR UPDATE OR DELETE ON nm_motion_all_derived_motion_ids_motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','all_origin_id','all_derived_motion_ids','motion','all_derived_motion_id','all_origin_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_motion_all_derived_motion_ids_motion_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_nm_motion_identical_motion_ids_motion_t AFTER INSERT OR UPDATE OR DELETE ON nm_motion_identical_motion_ids_motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','identical_motion_id_1','identical_motion_ids','motion','identical_motion_id_2','identical_motion_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_motion_identical_motion_ids_motion_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
CREATE TRIGGER tr_log_motion_t_state_id AFTER INSERT OR UPDATE OF state_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_state', 'state_id', 'motion_ids');
CREATE TRIGGER tr_log_motion_t_recommendation_id AFTER INSERT OR UPDATE OF recommendation_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_state', 'recommendation_id', 'motion_recommendation_ids');

CREATE TRIGGER tr_log_state_extension_reference_id_motion_id_gm_motion_2720cdc AFTER INSERT OR UPDATE OF state_extension_reference_id_motion_id OR DELETE ON gm_motion_state_extension_reference_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','motion_id','state_extension_reference_ids','motion','state_extension_reference_id_motion_id','referenced_in_motion_state_extension_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gm_motion_state_extension_reference_ids_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_recommendation_extension_reference_id_motion_id_g047b2db AFTER INSERT OR UPDATE OF recommendation_extension_reference_id_motion_id OR DELETE ON gm_motion_recommendation_extension_reference_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','motion_id','recommendation_extension_reference_ids','motion','recommendation_extension_reference_id_motion_id','referenced_in_motion_recommendation_extension_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gm_motion_recommendation_extension_reference_ids_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
CREATE TRIGGER tr_log_motion_t_category_id AFTER INSERT OR UPDATE OF category_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_category', 'category_id', 'motion_ids');
CREATE TRIGGER tr_log_motion_t_block_id AFTER INSERT OR UPDATE OF block_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_block', 'block_id', 'motion_ids');
CREATE TRIGGER tr_log_motion_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_ids');

CREATE TRIGGER tr_log_motion_block AFTER INSERT OR UPDATE OR DELETE ON motion_block_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_block');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_block_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_block_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_block_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_block_ids');

CREATE TRIGGER tr_log_motion_category AFTER INSERT OR UPDATE OR DELETE ON motion_category_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_category');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_category_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_category_t_parent_id AFTER INSERT OR UPDATE OF parent_id OR DELETE ON motion_category_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_category', 'parent_id', 'child_ids');
CREATE TRIGGER tr_log_motion_category_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_category_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_category_ids');

CREATE TRIGGER tr_log_motion_change_recommendation AFTER INSERT OR UPDATE OR DELETE ON motion_change_recommendation_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_change_recommendation');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_change_recommendation_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_change_recommendation_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_change_recommendation_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'change_recommendation_ids');
CREATE TRIGGER tr_log_motion_change_recommendation_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_change_recommendation_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_change_recommendation_ids');

CREATE TRIGGER tr_log_motion_comment AFTER INSERT OR UPDATE OR DELETE ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_comment');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_comment_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_comment_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'comment_ids');
CREATE TRIGGER tr_log_motion_comment_t_section_id AFTER INSERT OR UPDATE OF section_id OR DELETE ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_comment_section', 'section_id', 'comment_ids');
CREATE TRIGGER tr_log_motion_comment_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_comment_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_comment_ids');

CREATE TRIGGER tr_log_motion_comment_section AFTER INSERT OR UPDATE OR DELETE ON motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_comment_section');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_comment_section_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_comment_section_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_comment_section_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_comment_section_ids');

CREATE TRIGGER tr_log_motion_editor AFTER INSERT OR UPDATE OR DELETE ON motion_editor_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_editor');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_editor_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_editor_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON motion_editor_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'motion_editor_ids');
CREATE TRIGGER tr_log_motion_editor_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_editor_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'editor_ids');
CREATE TRIGGER tr_log_motion_editor_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_editor_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_editor_ids');

CREATE TRIGGER tr_log_motion_state AFTER INSERT OR UPDATE OR DELETE ON motion_state_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_state');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_state_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_state_t_submitter_withdraw_state_id AFTER INSERT OR UPDATE OF submitter_withdraw_state_id OR DELETE ON motion_state_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_state', 'submitter_withdraw_state_id', 'submitter_withdraw_back_ids');

CREATE TRIGGER tr_log_nm_motion_state_next_state_ids_motion_state_t AFTER INSERT OR UPDATE OR DELETE ON nm_motion_state_next_state_ids_motion_state_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_state','previous_state_id','next_state_ids','motion_state','next_state_id','previous_state_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_motion_state_next_state_ids_motion_state_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
CREATE TRIGGER tr_log_motion_state_t_workflow_id AFTER INSERT OR UPDATE OF workflow_id OR DELETE ON motion_state_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_workflow', 'workflow_id', 'state_ids');
CREATE TRIGGER tr_log_motion_state_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_state_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_state_ids');

CREATE TRIGGER tr_log_motion_submitter AFTER INSERT OR UPDATE OR DELETE ON motion_submitter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_submitter');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_submitter_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_submitter_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON motion_submitter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'motion_submitter_ids');
CREATE TRIGGER tr_log_motion_submitter_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_submitter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'submitter_ids');
CREATE TRIGGER tr_log_motion_submitter_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_submitter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_submitter_ids');

CREATE TRIGGER tr_log_motion_supporter AFTER INSERT OR UPDATE OR DELETE ON motion_supporter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_supporter');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_supporter_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_supporter_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON motion_supporter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'motion_supporter_ids');
CREATE TRIGGER tr_log_motion_supporter_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_supporter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'supporter_ids');
CREATE TRIGGER tr_log_motion_supporter_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_supporter_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_supporter_ids');

CREATE TRIGGER tr_log_motion_workflow AFTER INSERT OR UPDATE OR DELETE ON motion_workflow_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_workflow');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_workflow_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_workflow_t_first_state_id AFTER INSERT OR UPDATE OF first_state_id OR DELETE ON motion_workflow_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_state', 'first_state_id', 'first_state_of_workflow_id');
CREATE TRIGGER tr_log_motion_workflow_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_workflow_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_workflow_ids');

CREATE TRIGGER tr_log_motion_working_group_speaker AFTER INSERT OR UPDATE OR DELETE ON motion_working_group_speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('motion_working_group_speaker');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON motion_working_group_speaker_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_motion_working_group_speaker_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON motion_working_group_speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'motion_working_group_speaker_ids');
CREATE TRIGGER tr_log_motion_working_group_speaker_t_motion_id AFTER INSERT OR UPDATE OF motion_id OR DELETE ON motion_working_group_speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion', 'motion_id', 'working_group_speaker_ids');
CREATE TRIGGER tr_log_motion_working_group_speaker_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON motion_working_group_speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'motion_working_group_speaker_ids');

CREATE TRIGGER tr_log_option AFTER INSERT OR UPDATE OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('option');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON option_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_option_t_poll_id AFTER INSERT OR UPDATE OF poll_id OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll', 'poll_id', 'option_ids');

CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','option_ids');

CREATE TRIGGER tr_log_user_content_object_id_user_id AFTER INSERT OR UPDATE OF content_object_id_user_id OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user','content_object_id_user_id','option_ids');

CREATE TRIGGER tr_log_poll_candidate_list_content_object_id_poll_candidc235209 AFTER INSERT OR UPDATE OF content_object_id_poll_candidate_list_id OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll_candidate_list','content_object_id_poll_candidate_list_id','option_id');
CREATE TRIGGER tr_log_option_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON option_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'option_ids');

CREATE TRIGGER tr_log_organization AFTER INSERT OR UPDATE OR DELETE ON organization_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('organization');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON organization_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_organization_t_theme_id AFTER INSERT OR UPDATE OF theme_id OR DELETE ON organization_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('theme', 'theme_id', 'theme_for_organization_id');

CREATE TRIGGER tr_log_organization_tag AFTER INSERT OR UPDATE OR DELETE ON organization_tag_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('organization_tag');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON organization_tag_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


CREATE TRIGGER tr_log_tagged_id_committee_id_gm_organization_tag_tagged_ids_t AFTER INSERT OR UPDATE OF tagged_id_committee_id OR DELETE ON gm_organization_tag_tagged_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization_tag','organization_tag_id','tagged_ids','committee','tagged_id_committee_id','organization_tag_ids');

CREATE TRIGGER tr_log_tagged_id_meeting_id_gm_organization_tag_tagged_ids_t AFTER INSERT OR UPDATE OF tagged_id_meeting_id OR DELETE ON gm_organization_tag_tagged_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization_tag','organization_tag_id','tagged_ids','meeting','tagged_id_meeting_id','organization_tag_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gm_organization_tag_tagged_ids_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
CREATE TRIGGER tr_log_organization_tag_t_organization_id AFTER INSERT OR UPDATE OF organization_id OR DELETE ON organization_tag_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'organization_id', 'organization_tag_ids');

CREATE TRIGGER tr_log_personal_note AFTER INSERT OR UPDATE OR DELETE ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('personal_note');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON personal_note_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_personal_note_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'personal_note_ids');

CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','personal_note_ids');
CREATE TRIGGER tr_log_personal_note_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON personal_note_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'personal_note_ids');

CREATE TRIGGER tr_log_point_of_order_category AFTER INSERT OR UPDATE OR DELETE ON point_of_order_category_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('point_of_order_category');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON point_of_order_category_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_point_of_order_category_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON point_of_order_category_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'point_of_order_category_ids');

CREATE TRIGGER tr_log_poll AFTER INSERT OR UPDATE OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','poll_ids');

CREATE TRIGGER tr_log_assignment_content_object_id_assignment_id AFTER INSERT OR UPDATE OF content_object_id_assignment_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment','content_object_id_assignment_id','poll_ids');

CREATE TRIGGER tr_log_topic_content_object_id_topic_id AFTER INSERT OR UPDATE OF content_object_id_topic_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('topic','content_object_id_topic_id','poll_ids');
CREATE TRIGGER tr_log_poll_t_global_option_id AFTER INSERT OR UPDATE OF global_option_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('option', 'global_option_id', 'used_as_global_option_in_poll_id');

CREATE TRIGGER tr_log_nm_poll_voted_ids_user_t AFTER INSERT OR UPDATE OR DELETE ON nm_poll_voted_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll','poll_id','voted_ids','user','user_id','poll_voted_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON nm_poll_voted_ids_user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
CREATE TRIGGER tr_log_poll_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON poll_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'poll_ids');

CREATE TRIGGER tr_log_poll_candidate AFTER INSERT OR UPDATE OR DELETE ON poll_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_candidate');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_candidate_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_poll_candidate_t_poll_candidate_list_id AFTER INSERT OR UPDATE OF poll_candidate_list_id OR DELETE ON poll_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll_candidate_list', 'poll_candidate_list_id', 'poll_candidate_ids');
CREATE TRIGGER tr_log_poll_candidate_t_user_id AFTER INSERT OR UPDATE OF user_id OR DELETE ON poll_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user', 'user_id', 'poll_candidate_ids');
CREATE TRIGGER tr_log_poll_candidate_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON poll_candidate_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'poll_candidate_ids');

CREATE TRIGGER tr_log_poll_candidate_list AFTER INSERT OR UPDATE OR DELETE ON poll_candidate_list_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('poll_candidate_list');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON poll_candidate_list_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_poll_candidate_list_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON poll_candidate_list_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'poll_candidate_list_ids');

CREATE TRIGGER tr_log_projection AFTER INSERT OR UPDATE OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('projection');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON projection_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_projection_t_current_projector_id AFTER INSERT OR UPDATE OF current_projector_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector', 'current_projector_id', 'current_projection_ids');
CREATE TRIGGER tr_log_projection_t_preview_projector_id AFTER INSERT OR UPDATE OF preview_projector_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector', 'preview_projector_id', 'preview_projection_ids');
CREATE TRIGGER tr_log_projection_t_history_projector_id AFTER INSERT OR UPDATE OF history_projector_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector', 'history_projector_id', 'history_projection_ids');

CREATE TRIGGER tr_log_meeting_content_object_id_meeting_id AFTER INSERT OR UPDATE OF content_object_id_meeting_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting','content_object_id_meeting_id','projection_ids');

CREATE TRIGGER tr_log_motion_content_object_id_motion_id AFTER INSERT OR UPDATE OF content_object_id_motion_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion','content_object_id_motion_id','projection_ids');

CREATE TRIGGER tr_log_meeting_mediafile_content_object_id_meeting_mediafile_id AFTER INSERT OR UPDATE OF content_object_id_meeting_mediafile_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_mediafile','content_object_id_meeting_mediafile_id','projection_ids');

CREATE TRIGGER tr_log_list_of_speakers_content_object_id_list_of_speakers_id AFTER INSERT OR UPDATE OF content_object_id_list_of_speakers_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('list_of_speakers','content_object_id_list_of_speakers_id','projection_ids');

CREATE TRIGGER tr_log_motion_block_content_object_id_motion_block_id AFTER INSERT OR UPDATE OF content_object_id_motion_block_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('motion_block','content_object_id_motion_block_id','projection_ids');

CREATE TRIGGER tr_log_assignment_content_object_id_assignment_id AFTER INSERT OR UPDATE OF content_object_id_assignment_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('assignment','content_object_id_assignment_id','projection_ids');

CREATE TRIGGER tr_log_agenda_item_content_object_id_agenda_item_id AFTER INSERT OR UPDATE OF content_object_id_agenda_item_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('agenda_item','content_object_id_agenda_item_id','projection_ids');

CREATE TRIGGER tr_log_topic_content_object_id_topic_id AFTER INSERT OR UPDATE OF content_object_id_topic_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('topic','content_object_id_topic_id','projection_ids');

CREATE TRIGGER tr_log_poll_content_object_id_poll_id AFTER INSERT OR UPDATE OF content_object_id_poll_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('poll','content_object_id_poll_id','projection_ids');

CREATE TRIGGER tr_log_projector_message_content_object_id_projector_message_id AFTER INSERT OR UPDATE OF content_object_id_projector_message_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector_message','content_object_id_projector_message_id','projection_ids');

CREATE TRIGGER tr_log_projector_countdown_content_object_id_projector_c35fae82 AFTER INSERT OR UPDATE OF content_object_id_projector_countdown_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('projector_countdown','content_object_id_projector_countdown_id','projection_ids');
CREATE TRIGGER tr_log_projection_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON projection_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'all_projection_ids');

CREATE TRIGGER tr_log_projector AFTER INSERT OR UPDATE OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('projector');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON projector_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_agenda_a3418fd AFTER INSERT OR UPDATE OF used_as_default_projector_for_agenda_item_list_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_agenda_item_list_in_meeting_id', 'default_projector_agenda_item_list_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_topic_iccc9ca7 AFTER INSERT OR UPDATE OF used_as_default_projector_for_topic_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_topic_in_meeting_id', 'default_projector_topic_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_list_offcea2e3 AFTER INSERT OR UPDATE OF used_as_default_projector_for_list_of_speakers_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_list_of_speakers_in_meeting_id', 'default_projector_list_of_speakers_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_current897012e AFTER INSERT OR UPDATE OF used_as_default_projector_for_current_los_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_current_los_in_meeting_id', 'default_projector_current_los_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_motion_9cf3618 AFTER INSERT OR UPDATE OF used_as_default_projector_for_motion_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_motion_in_meeting_id', 'default_projector_motion_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_amendme4ebfd41 AFTER INSERT OR UPDATE OF used_as_default_projector_for_amendment_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_amendment_in_meeting_id', 'default_projector_amendment_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_motion_1b9d3a7 AFTER INSERT OR UPDATE OF used_as_default_projector_for_motion_block_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_motion_block_in_meeting_id', 'default_projector_motion_block_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_assignm9e3b0b3 AFTER INSERT OR UPDATE OF used_as_default_projector_for_assignment_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_assignment_in_meeting_id', 'default_projector_assignment_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_mediafib4f0da8 AFTER INSERT OR UPDATE OF used_as_default_projector_for_mediafile_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_mediafile_in_meeting_id', 'default_projector_mediafile_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_message28c0ca6 AFTER INSERT OR UPDATE OF used_as_default_projector_for_message_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_message_in_meeting_id', 'default_projector_message_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_countdoe67f735 AFTER INSERT OR UPDATE OF used_as_default_projector_for_countdown_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_countdown_in_meeting_id', 'default_projector_countdown_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_assignmf3a7b0f AFTER INSERT OR UPDATE OF used_as_default_projector_for_assignment_poll_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_assignment_poll_in_meeting_id', 'default_projector_assignment_poll_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_motion_c48d3bb AFTER INSERT OR UPDATE OF used_as_default_projector_for_motion_poll_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_motion_poll_in_meeting_id', 'default_projector_motion_poll_ids');
CREATE TRIGGER tr_log_projector_t_used_as_default_projector_for_poll_inf6f7d63 AFTER INSERT OR UPDATE OF used_as_default_projector_for_poll_in_meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'used_as_default_projector_for_poll_in_meeting_id', 'default_projector_poll_ids');
CREATE TRIGGER tr_log_projector_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON projector_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'projector_ids');

CREATE TRIGGER tr_log_projector_countdown AFTER INSERT OR UPDATE OR DELETE ON projector_countdown_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('projector_countdown');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON projector_countdown_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_projector_countdown_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON projector_countdown_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'projector_countdown_ids');

CREATE TRIGGER tr_log_projector_message AFTER INSERT OR UPDATE OR DELETE ON projector_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('projector_message');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON projector_message_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_projector_message_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON projector_message_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'projector_message_ids');

CREATE TRIGGER tr_log_speaker AFTER INSERT OR UPDATE OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('speaker');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON speaker_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_speaker_t_list_of_speakers_id AFTER INSERT OR UPDATE OF list_of_speakers_id OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('list_of_speakers', 'list_of_speakers_id', 'speaker_ids');
CREATE TRIGGER tr_log_speaker_t_structure_level_list_of_speakers_id AFTER INSERT OR UPDATE OF structure_level_list_of_speakers_id OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('structure_level_list_of_speakers', 'structure_level_list_of_speakers_id', 'speaker_ids');
CREATE TRIGGER tr_log_speaker_t_meeting_user_id AFTER INSERT OR UPDATE OF meeting_user_id OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting_user', 'meeting_user_id', 'speaker_ids');
CREATE TRIGGER tr_log_speaker_t_point_of_order_category_id AFTER INSERT OR UPDATE OF point_of_order_category_id OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('point_of_order_category', 'point_of_order_category_id', 'speaker_ids');
CREATE TRIGGER tr_log_speaker_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON speaker_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'speaker_ids');

CREATE TRIGGER tr_log_structure_level AFTER INSERT OR UPDATE OR DELETE ON structure_level_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('structure_level');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON structure_level_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_structure_level_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON structure_level_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'structure_level_ids');

CREATE TRIGGER tr_log_structure_level_list_of_speakers AFTER INSERT OR UPDATE OR DELETE ON structure_level_list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('structure_level_list_of_speakers');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON structure_level_list_of_speakers_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_structure_level_list_of_speakers_t_structure_level_id AFTER INSERT OR UPDATE OF structure_level_id OR DELETE ON structure_level_list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('structure_level', 'structure_level_id', 'structure_level_list_of_speakers_ids');
CREATE TRIGGER tr_log_structure_level_list_of_speakers_t_list_of_speakers_id AFTER INSERT OR UPDATE OF list_of_speakers_id OR DELETE ON structure_level_list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('list_of_speakers', 'list_of_speakers_id', 'structure_level_list_of_speakers_ids');
CREATE TRIGGER tr_log_structure_level_list_of_speakers_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON structure_level_list_of_speakers_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'structure_level_list_of_speakers_ids');

CREATE TRIGGER tr_log_tag AFTER INSERT OR UPDATE OR DELETE ON tag_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('tag');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON tag_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();


CREATE TRIGGER tr_log_tagged_id_agenda_item_id_gm_tag_tagged_ids_t AFTER INSERT OR UPDATE OF tagged_id_agenda_item_id OR DELETE ON gm_tag_tagged_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('tag','tag_id','tagged_ids','agenda_item','tagged_id_agenda_item_id','tag_ids');

CREATE TRIGGER tr_log_tagged_id_assignment_id_gm_tag_tagged_ids_t AFTER INSERT OR UPDATE OF tagged_id_assignment_id OR DELETE ON gm_tag_tagged_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('tag','tag_id','tagged_ids','assignment','tagged_id_assignment_id','tag_ids');

CREATE TRIGGER tr_log_tagged_id_motion_id_gm_tag_tagged_ids_t AFTER INSERT OR UPDATE OF tagged_id_motion_id OR DELETE ON gm_tag_tagged_ids_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('tag','tag_id','tagged_ids','motion','tagged_id_motion_id','tag_ids');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON gm_tag_tagged_ids_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();
CREATE TRIGGER tr_log_tag_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON tag_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'tag_ids');

CREATE TRIGGER tr_log_theme AFTER INSERT OR UPDATE OR DELETE ON theme_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('theme');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON theme_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_theme_t_organization_id AFTER INSERT OR UPDATE OF organization_id OR DELETE ON theme_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'organization_id', 'theme_ids');

CREATE TRIGGER tr_log_topic AFTER INSERT OR UPDATE OR DELETE ON topic_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('topic');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON topic_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_topic_t_meeting_id AFTER INSERT OR UPDATE OF meeting_id OR DELETE ON topic_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('meeting', 'meeting_id', 'topic_ids');

CREATE TRIGGER tr_log_user AFTER INSERT OR UPDATE OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('user');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON user_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_user_t_gender_id AFTER INSERT OR UPDATE OF gender_id OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('gender', 'gender_id', 'user_ids');

CREATE TRIGGER tr_log_i_user_committee_ids_from_meeting_user_t BEFORE INSERT ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('user', 'user_id', '', 'committee_ids', '', 'SELECT committee_id FROM meeting_t WHERE id = ($1).meeting_id');
CREATE TRIGGER tr_log_d_user_committee_ids_from_meeting_user_t AFTER DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('user', 'user_id', '', 'committee_ids', '', 'SELECT committee_id FROM meeting_t WHERE id = ($1).meeting_id');
CREATE TRIGGER tr_log_i_user_committee_ids_from_nm_committee_manager_id3c34791 BEFORE INSERT ON nm_committee_manager_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('user', 'user_id', '', 'committee_ids', 'committee_id', '');
CREATE TRIGGER tr_log_d_user_committee_ids_from_nm_committee_manager_id8cfd923 AFTER DELETE ON nm_committee_manager_ids_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('user', 'user_id', '', 'committee_ids', 'committee_id', '');
CREATE TRIGGER tr_log_iu_user_committee_ids_from_user_t BEFORE INSERT OR UPDATE OF home_committee_id ON user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('user', 'id', '', 'committee_ids', 'home_committee_id', '');
CREATE TRIGGER tr_log_ud_user_committee_ids_from_user_t AFTER UPDATE OF home_committee_id OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('user', 'id', '', 'committee_ids', 'home_committee_id', '');

CREATE TRIGGER tr_log_user_t_home_committee_id AFTER INSERT OR UPDATE OF home_committee_id OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('committee', 'home_committee_id', 'native_user_ids');

CREATE TRIGGER tr_log_i_user_meeting_ids_from_meeting_user_t BEFORE INSERT ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_iu_modified_calculated_id_array_field('user', 'user_id', '', 'meeting_ids', 'meeting_id', '');
CREATE TRIGGER tr_log_d_user_meeting_ids_from_meeting_user_t AFTER DELETE ON meeting_user_t
FOR EACH ROW EXECUTE FUNCTION log_ud_modified_calculated_id_array_field('user', 'user_id', '', 'meeting_ids', 'meeting_id', '');

CREATE TRIGGER tr_log_user_t_organization_id AFTER INSERT OR UPDATE OF organization_id OR DELETE ON user_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('organization', 'organization_id', 'user_ids');

CREATE TRIGGER tr_log_vote AFTER INSERT OR UPDATE OR DELETE ON vote_t
FOR EACH ROW EXECUTE FUNCTION log_modified_models('vote');
CREATE CONSTRAINT TRIGGER notify_transaction_end AFTER INSERT OR UPDATE OR DELETE ON vote_t
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION notify_transaction_end();

CREATE TRIGGER tr_log_vote_t_option_id AFTER INSERT OR UPDATE OF option_id OR DELETE ON vote_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('option', 'option_id', 'vote_ids');
CREATE TRIGGER tr_log_vote_t_user_id AFTER INSERT OR UPDATE OF user_id OR DELETE ON vote_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user', 'user_id', 'vote_ids');
CREATE TRIGGER tr_log_vote_t_delegated_user_id AFTER INSERT OR UPDATE OF delegated_user_id OR DELETE ON vote_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user', 'delegated_user_id', 'delegated_vote_ids');
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



/*   Relation-list infos
Generated: What will be generated for left field
    FIELD: a usual Database field
    SQL: a sql-expression in a view
    ***: Error
Field Attributes:Field Attributes opposite side
    1: cardinality 1
    1G: cardinality 1 with generic-relation field
    n: cardinality n
    nG: cardinality n with generic-relation-list field
    t: "to" defined
    r: "reference" defined
    s: sql directive inclusive sql-statement
    R: Required
Model.Field -> Model.Field
    model.field names
*/

/*
FIELD 1GrR:1t,1t,1t,1tR => agenda_item/content_object_id:-> motion/agenda_item_id,motion_block/agenda_item_id,assignment/agenda_item_id,topic/agenda_item_id
FIELD 1r:nt => agenda_item/parent_id:-> agenda_item/child_ids
SQL nt:1r => agenda_item/child_ids:-> agenda_item/parent_id
SQL nt:nGt => agenda_item/tag_ids:-> tag/tagged_ids
SQL nt:1GrR => agenda_item/projection_ids:-> projection/content_object_id
FIELD 1rR:nt => agenda_item/meeting_id:-> meeting/agenda_item_ids

SQL nt:1rR => assignment/candidate_ids:-> assignment_candidate/assignment_id
SQL nt:1GrR => assignment/poll_ids:-> poll/content_object_id
SQL 1t:1GrR => assignment/agenda_item_id:-> agenda_item/content_object_id
SQL 1tR:1GrR => assignment/list_of_speakers_id:-> list_of_speakers/content_object_id
SQL nt:nGt => assignment/tag_ids:-> tag/tagged_ids
SQL nt:nGt => assignment/attachment_meeting_mediafile_ids:-> meeting_mediafile/attachment_ids
SQL nt:1GrR => assignment/projection_ids:-> projection/content_object_id
FIELD 1rR:nt => assignment/meeting_id:-> meeting/assignment_ids
SQL nt:1Gr => assignment/history_entry_ids:-> history_entry/model_id

FIELD 1rR:nt => assignment_candidate/assignment_id:-> assignment/candidate_ids
FIELD 1r:nt => assignment_candidate/meeting_user_id:-> meeting_user/assignment_candidate_ids
FIELD 1rR:nt => assignment_candidate/meeting_id:-> meeting/assignment_candidate_ids

SQL nt:1rR => chat_group/chat_message_ids:-> chat_message/chat_group_id
SQL nt:nt => chat_group/read_group_ids:-> group/read_chat_group_ids
SQL nt:nt => chat_group/write_group_ids:-> group/write_chat_group_ids
FIELD 1rR:nt => chat_group/meeting_id:-> meeting/chat_group_ids

FIELD 1r:nt => chat_message/meeting_user_id:-> meeting_user/chat_message_ids
FIELD 1rR:nt => chat_message/chat_group_id:-> chat_group/chat_message_ids
FIELD 1rR:nt => chat_message/meeting_id:-> meeting/chat_message_ids

SQL nt:1rR => committee/meeting_ids:-> meeting/committee_id
FIELD 1r:1t => committee/default_meeting_id:-> meeting/default_meeting_for_committee_id
SQL nts:nts => committee/user_ids:-> user/committee_ids
SQL nt:nt => committee/manager_ids:-> user/committee_management_ids
FIELD 1r:nt => committee/parent_id:-> committee/child_ids
SQL nt:1r => committee/child_ids:-> committee/parent_id
SQL nt:nt => committee/all_parent_ids:-> committee/all_child_ids
SQL nt:nt => committee/all_child_ids:-> committee/all_parent_ids
SQL nt:1r => committee/native_user_ids:-> user/home_committee_id
SQL nt:nt => committee/forward_to_committee_ids:-> committee/receive_forwardings_from_committee_ids
SQL nt:nt => committee/receive_forwardings_from_committee_ids:-> committee/forward_to_committee_ids
SQL nt:nGt => committee/organization_tag_ids:-> organization_tag/tagged_ids
FIELD 1rR:nr => committee/organization_id:-> organization/committee_ids

FIELD 1rR:nr => gender/organization_id:-> organization/gender_ids
SQL nr:1r => gender/user_ids:-> user/gender_id

SQL nt:ntR => group/meeting_user_ids:-> meeting_user/group_ids
SQL 1t:1rR => group/default_group_for_meeting_id:-> meeting/default_group_id
SQL 1t:1r => group/admin_group_for_meeting_id:-> meeting/admin_group_id
SQL 1t:1r => group/anonymous_group_for_meeting_id:-> meeting/anonymous_group_id
SQL nt:nt => group/meeting_mediafile_access_group_ids:-> meeting_mediafile/access_group_ids
SQL nt:nt => group/meeting_mediafile_inherited_access_group_ids:-> meeting_mediafile/inherited_access_group_ids
SQL nt:nt => group/read_comment_section_ids:-> motion_comment_section/read_group_ids
SQL nt:nt => group/write_comment_section_ids:-> motion_comment_section/write_group_ids
SQL nt:nt => group/read_chat_group_ids:-> chat_group/read_group_ids
SQL nt:nt => group/write_chat_group_ids:-> chat_group/write_group_ids
SQL nt:nt => group/poll_ids:-> poll/entitled_group_ids
FIELD 1r:nt => group/used_as_motion_poll_default_id:-> meeting/motion_poll_default_group_ids
FIELD 1r:nt => group/used_as_assignment_poll_default_id:-> meeting/assignment_poll_default_group_ids
FIELD 1r:nt => group/used_as_topic_poll_default_id:-> meeting/topic_poll_default_group_ids
FIELD 1r:nt => group/used_as_poll_default_id:-> meeting/poll_default_group_ids
FIELD 1rR:nt => group/meeting_id:-> meeting/group_ids

FIELD 1Gr:nt,nt,nt => history_entry/model_id:-> user/history_entry_ids,motion/history_entry_ids,assignment/history_entry_ids
FIELD 1rR:nt => history_entry/position_id:-> history_position/entry_ids
FIELD 1r:nt => history_entry/meeting_id:-> meeting/relevant_history_entry_ids

FIELD 1r:nt => history_position/user_id:-> user/history_position_ids
SQL nt:1rR => history_position/entry_ids:-> history_entry/position_id

FIELD 1GrR:1tR,1tR,1tR,1tR,1t => list_of_speakers/content_object_id:-> motion/list_of_speakers_id,motion_block/list_of_speakers_id,assignment/list_of_speakers_id,topic/list_of_speakers_id,meeting_mediafile/list_of_speakers_id
SQL nt:1rR => list_of_speakers/speaker_ids:-> speaker/list_of_speakers_id
SQL nt:1rR => list_of_speakers/structure_level_list_of_speakers_ids:-> structure_level_list_of_speakers/list_of_speakers_id
SQL nt:1GrR => list_of_speakers/projection_ids:-> projection/content_object_id
FIELD 1rR:nt => list_of_speakers/meeting_id:-> meeting/list_of_speakers_ids

FIELD 1r:nt => mediafile/published_to_meetings_in_organization_id:-> organization/published_mediafile_ids
FIELD 1r:nt => mediafile/parent_id:-> mediafile/child_ids
SQL nt:1r => mediafile/child_ids:-> mediafile/parent_id
FIELD 1GrR:nt,nt => mediafile/owner_id:-> meeting/mediafile_ids,organization/mediafile_ids
SQL nt:1rR => mediafile/meeting_mediafile_ids:-> meeting_mediafile/mediafile_id

FIELD 1r:nt => meeting/is_active_in_organization_id:-> organization/active_meeting_ids
FIELD 1r:nt => meeting/is_archived_in_organization_id:-> organization/archived_meeting_ids
FIELD 1r:nt => meeting/template_for_organization_id:-> organization/template_meeting_ids
FIELD 1rR:1t => meeting/motions_default_workflow_id:-> motion_workflow/default_workflow_meeting_id
FIELD 1rR:1t => meeting/motions_default_amendment_workflow_id:-> motion_workflow/default_amendment_workflow_meeting_id
SQL nt:1r => meeting/motion_poll_default_group_ids:-> group/used_as_motion_poll_default_id
SQL nr:1rR => meeting/poll_candidate_list_ids:-> poll_candidate_list/meeting_id
SQL nr:1rR => meeting/poll_candidate_ids:-> poll_candidate/meeting_id
SQL nt:1rR => meeting/meeting_user_ids:-> meeting_user/meeting_id
SQL nt:1r => meeting/assignment_poll_default_group_ids:-> group/used_as_assignment_poll_default_id
SQL nt:1r => meeting/poll_default_group_ids:-> group/used_as_poll_default_id
SQL nt:1r => meeting/topic_poll_default_group_ids:-> group/used_as_topic_poll_default_id
SQL nt:1rR => meeting/projector_ids:-> projector/meeting_id
SQL nt:1rR => meeting/all_projection_ids:-> projection/meeting_id
SQL nt:1rR => meeting/projector_message_ids:-> projector_message/meeting_id
SQL nt:1rR => meeting/projector_countdown_ids:-> projector_countdown/meeting_id
SQL nt:1rR => meeting/tag_ids:-> tag/meeting_id
SQL nt:1rR => meeting/agenda_item_ids:-> agenda_item/meeting_id
SQL nt:1rR => meeting/list_of_speakers_ids:-> list_of_speakers/meeting_id
SQL nt:1rR => meeting/structure_level_list_of_speakers_ids:-> structure_level_list_of_speakers/meeting_id
SQL nt:1rR => meeting/point_of_order_category_ids:-> point_of_order_category/meeting_id
SQL nt:1rR => meeting/speaker_ids:-> speaker/meeting_id
SQL nt:1rR => meeting/topic_ids:-> topic/meeting_id
SQL nt:1rR => meeting/group_ids:-> group/meeting_id
SQL nt:1rR => meeting/meeting_mediafile_ids:-> meeting_mediafile/meeting_id
SQL nt:1GrR => meeting/mediafile_ids:-> mediafile/owner_id
SQL nt:1rR => meeting/motion_ids:-> motion/meeting_id
SQL nt:1r => meeting/forwarded_motion_ids:-> motion/origin_meeting_id
SQL nt:1rR => meeting/motion_comment_section_ids:-> motion_comment_section/meeting_id
SQL nt:1rR => meeting/motion_category_ids:-> motion_category/meeting_id
SQL nt:1rR => meeting/motion_block_ids:-> motion_block/meeting_id
SQL nt:1rR => meeting/motion_workflow_ids:-> motion_workflow/meeting_id
SQL nt:1rR => meeting/motion_comment_ids:-> motion_comment/meeting_id
SQL nt:1rR => meeting/motion_submitter_ids:-> motion_submitter/meeting_id
SQL nt:1rR => meeting/motion_supporter_ids:-> motion_supporter/meeting_id
SQL nt:1rR => meeting/motion_editor_ids:-> motion_editor/meeting_id
SQL nt:1rR => meeting/motion_working_group_speaker_ids:-> motion_working_group_speaker/meeting_id
SQL nt:1rR => meeting/motion_change_recommendation_ids:-> motion_change_recommendation/meeting_id
SQL nt:1rR => meeting/motion_state_ids:-> motion_state/meeting_id
SQL nr:1rR => meeting/poll_ids:-> poll/meeting_id
SQL nr:1rR => meeting/option_ids:-> option/meeting_id
SQL nr:1rR => meeting/vote_ids:-> vote/meeting_id
SQL nt:1rR => meeting/assignment_ids:-> assignment/meeting_id
SQL nt:1rR => meeting/assignment_candidate_ids:-> assignment_candidate/meeting_id
SQL nt:1rR => meeting/personal_note_ids:-> personal_note/meeting_id
SQL nt:1rR => meeting/chat_group_ids:-> chat_group/meeting_id
SQL nt:1rR => meeting/chat_message_ids:-> chat_message/meeting_id
SQL nt:1rR => meeting/structure_level_ids:-> structure_level/meeting_id
FIELD 1r:1t => meeting/logo_projector_main_id:-> meeting_mediafile/used_as_logo_projector_main_in_meeting_id
FIELD 1r:1t => meeting/logo_projector_header_id:-> meeting_mediafile/used_as_logo_projector_header_in_meeting_id
FIELD 1r:1t => meeting/logo_web_header_id:-> meeting_mediafile/used_as_logo_web_header_in_meeting_id
FIELD 1r:1t => meeting/logo_pdf_header_l_id:-> meeting_mediafile/used_as_logo_pdf_header_l_in_meeting_id
FIELD 1r:1t => meeting/logo_pdf_header_r_id:-> meeting_mediafile/used_as_logo_pdf_header_r_in_meeting_id
FIELD 1r:1t => meeting/logo_pdf_footer_l_id:-> meeting_mediafile/used_as_logo_pdf_footer_l_in_meeting_id
FIELD 1r:1t => meeting/logo_pdf_footer_r_id:-> meeting_mediafile/used_as_logo_pdf_footer_r_in_meeting_id
FIELD 1r:1t => meeting/logo_pdf_ballot_paper_id:-> meeting_mediafile/used_as_logo_pdf_ballot_paper_in_meeting_id
FIELD 1r:1t => meeting/font_regular_id:-> meeting_mediafile/used_as_font_regular_in_meeting_id
FIELD 1r:1t => meeting/font_italic_id:-> meeting_mediafile/used_as_font_italic_in_meeting_id
FIELD 1r:1t => meeting/font_bold_id:-> meeting_mediafile/used_as_font_bold_in_meeting_id
FIELD 1r:1t => meeting/font_bold_italic_id:-> meeting_mediafile/used_as_font_bold_italic_in_meeting_id
FIELD 1r:1t => meeting/font_monospace_id:-> meeting_mediafile/used_as_font_monospace_in_meeting_id
FIELD 1r:1t => meeting/font_chyron_speaker_name_id:-> meeting_mediafile/used_as_font_chyron_speaker_name_in_meeting_id
FIELD 1r:1t => meeting/font_projector_h1_id:-> meeting_mediafile/used_as_font_projector_h1_in_meeting_id
FIELD 1r:1t => meeting/font_projector_h2_id:-> meeting_mediafile/used_as_font_projector_h2_in_meeting_id
FIELD 1rR:nt => meeting/committee_id:-> committee/meeting_ids
SQL 1t:1r => meeting/default_meeting_for_committee_id:-> committee/default_meeting_id
SQL nt:nGt => meeting/organization_tag_ids:-> organization_tag/tagged_ids
SQL nt:nt => meeting/present_user_ids:-> user/is_present_in_meeting_ids
SQL nts:nts => meeting/user_ids:-> user/meeting_ids
FIELD 1rR:1t => meeting/reference_projector_id:-> projector/used_as_reference_projector_meeting_id
FIELD 1r:1t => meeting/list_of_speakers_countdown_id:-> projector_countdown/used_as_list_of_speakers_countdown_meeting_id
FIELD 1r:1t => meeting/poll_countdown_id:-> projector_countdown/used_as_poll_countdown_meeting_id
SQL nt:1GrR => meeting/projection_ids:-> projection/content_object_id
SQL ntR:1r => meeting/default_projector_agenda_item_list_ids:-> projector/used_as_default_projector_for_agenda_item_list_in_meeting_id
SQL ntR:1r => meeting/default_projector_topic_ids:-> projector/used_as_default_projector_for_topic_in_meeting_id
SQL ntR:1r => meeting/default_projector_list_of_speakers_ids:-> projector/used_as_default_projector_for_list_of_speakers_in_meeting_id
SQL ntR:1r => meeting/default_projector_current_los_ids:-> projector/used_as_default_projector_for_current_los_in_meeting_id
SQL ntR:1r => meeting/default_projector_motion_ids:-> projector/used_as_default_projector_for_motion_in_meeting_id
SQL ntR:1r => meeting/default_projector_amendment_ids:-> projector/used_as_default_projector_for_amendment_in_meeting_id
SQL ntR:1r => meeting/default_projector_motion_block_ids:-> projector/used_as_default_projector_for_motion_block_in_meeting_id
SQL ntR:1r => meeting/default_projector_assignment_ids:-> projector/used_as_default_projector_for_assignment_in_meeting_id
SQL ntR:1r => meeting/default_projector_mediafile_ids:-> projector/used_as_default_projector_for_mediafile_in_meeting_id
SQL ntR:1r => meeting/default_projector_message_ids:-> projector/used_as_default_projector_for_message_in_meeting_id
SQL ntR:1r => meeting/default_projector_countdown_ids:-> projector/used_as_default_projector_for_countdown_in_meeting_id
SQL ntR:1r => meeting/default_projector_assignment_poll_ids:-> projector/used_as_default_projector_for_assignment_poll_in_meeting_id
SQL ntR:1r => meeting/default_projector_motion_poll_ids:-> projector/used_as_default_projector_for_motion_poll_in_meeting_id
SQL ntR:1r => meeting/default_projector_poll_ids:-> projector/used_as_default_projector_for_poll_in_meeting_id
FIELD 1rR:1t => meeting/default_group_id:-> group/default_group_for_meeting_id
FIELD 1r:1t => meeting/admin_group_id:-> group/admin_group_for_meeting_id
FIELD 1r:1t => meeting/anonymous_group_id:-> group/anonymous_group_for_meeting_id
SQL nt:1r => meeting/relevant_history_entry_ids:-> history_entry/meeting_id

FIELD 1rR:nt => meeting_mediafile/mediafile_id:-> mediafile/meeting_mediafile_ids
FIELD 1rR:nt => meeting_mediafile/meeting_id:-> meeting/meeting_mediafile_ids
SQL nt:nt => meeting_mediafile/inherited_access_group_ids:-> group/meeting_mediafile_inherited_access_group_ids
SQL nt:nt => meeting_mediafile/access_group_ids:-> group/meeting_mediafile_access_group_ids
SQL 1t:1GrR => meeting_mediafile/list_of_speakers_id:-> list_of_speakers/content_object_id
SQL nt:1GrR => meeting_mediafile/projection_ids:-> projection/content_object_id
SQL nGt:nt,nt,nt => meeting_mediafile/attachment_ids:-> motion/attachment_meeting_mediafile_ids,topic/attachment_meeting_mediafile_ids,assignment/attachment_meeting_mediafile_ids
SQL 1t:1r => meeting_mediafile/used_as_logo_projector_main_in_meeting_id:-> meeting/logo_projector_main_id
SQL 1t:1r => meeting_mediafile/used_as_logo_projector_header_in_meeting_id:-> meeting/logo_projector_header_id
SQL 1t:1r => meeting_mediafile/used_as_logo_web_header_in_meeting_id:-> meeting/logo_web_header_id
SQL 1t:1r => meeting_mediafile/used_as_logo_pdf_header_l_in_meeting_id:-> meeting/logo_pdf_header_l_id
SQL 1t:1r => meeting_mediafile/used_as_logo_pdf_header_r_in_meeting_id:-> meeting/logo_pdf_header_r_id
SQL 1t:1r => meeting_mediafile/used_as_logo_pdf_footer_l_in_meeting_id:-> meeting/logo_pdf_footer_l_id
SQL 1t:1r => meeting_mediafile/used_as_logo_pdf_footer_r_in_meeting_id:-> meeting/logo_pdf_footer_r_id
SQL 1t:1r => meeting_mediafile/used_as_logo_pdf_ballot_paper_in_meeting_id:-> meeting/logo_pdf_ballot_paper_id
SQL 1t:1r => meeting_mediafile/used_as_font_regular_in_meeting_id:-> meeting/font_regular_id
SQL 1t:1r => meeting_mediafile/used_as_font_italic_in_meeting_id:-> meeting/font_italic_id
SQL 1t:1r => meeting_mediafile/used_as_font_bold_in_meeting_id:-> meeting/font_bold_id
SQL 1t:1r => meeting_mediafile/used_as_font_bold_italic_in_meeting_id:-> meeting/font_bold_italic_id
SQL 1t:1r => meeting_mediafile/used_as_font_monospace_in_meeting_id:-> meeting/font_monospace_id
SQL 1t:1r => meeting_mediafile/used_as_font_chyron_speaker_name_in_meeting_id:-> meeting/font_chyron_speaker_name_id
SQL 1t:1r => meeting_mediafile/used_as_font_projector_h1_in_meeting_id:-> meeting/font_projector_h1_id
SQL 1t:1r => meeting_mediafile/used_as_font_projector_h2_in_meeting_id:-> meeting/font_projector_h2_id

FIELD 1rR:nt => meeting_user/user_id:-> user/meeting_user_ids
FIELD 1rR:nt => meeting_user/meeting_id:-> meeting/meeting_user_ids
SQL nt:1rR => meeting_user/personal_note_ids:-> personal_note/meeting_user_id
SQL nt:1r => meeting_user/speaker_ids:-> speaker/meeting_user_id
SQL nt:1r => meeting_user/motion_supporter_ids:-> motion_supporter/meeting_user_id
SQL nt:1r => meeting_user/motion_editor_ids:-> motion_editor/meeting_user_id
SQL nt:1r => meeting_user/motion_working_group_speaker_ids:-> motion_working_group_speaker/meeting_user_id
SQL nt:1r => meeting_user/motion_submitter_ids:-> motion_submitter/meeting_user_id
SQL nt:1r => meeting_user/assignment_candidate_ids:-> assignment_candidate/meeting_user_id
FIELD 1r:nt => meeting_user/vote_delegated_to_id:-> meeting_user/vote_delegations_from_ids
SQL nt:1r => meeting_user/vote_delegations_from_ids:-> meeting_user/vote_delegated_to_id
SQL nt:1r => meeting_user/chat_message_ids:-> chat_message/meeting_user_id
SQL ntR:nt => meeting_user/group_ids:-> group/meeting_user_ids
SQL nt:nt => meeting_user/structure_level_ids:-> structure_level/meeting_user_ids

FIELD 1r:nt => motion/lead_motion_id:-> motion/amendment_ids
SQL nt:1r => motion/amendment_ids:-> motion/lead_motion_id
FIELD 1r:nt => motion/sort_parent_id:-> motion/sort_child_ids
SQL nt:1r => motion/sort_child_ids:-> motion/sort_parent_id
FIELD 1r:nt => motion/origin_id:-> motion/derived_motion_ids
FIELD 1r:nt => motion/origin_meeting_id:-> meeting/forwarded_motion_ids
SQL nt:1r => motion/derived_motion_ids:-> motion/origin_id
SQL nt:nt => motion/all_origin_ids:-> motion/all_derived_motion_ids
SQL nt:nt => motion/all_derived_motion_ids:-> motion/all_origin_ids
SQL nt:nt => motion/identical_motion_ids:-> motion/identical_motion_ids
FIELD 1rR:nt => motion/state_id:-> motion_state/motion_ids
FIELD 1r:nt => motion/recommendation_id:-> motion_state/motion_recommendation_ids
SQL nGt:nt => motion/state_extension_reference_ids:-> motion/referenced_in_motion_state_extension_ids
SQL nt:nGt => motion/referenced_in_motion_state_extension_ids:-> motion/state_extension_reference_ids
SQL nGt:nt => motion/recommendation_extension_reference_ids:-> motion/referenced_in_motion_recommendation_extension_ids
SQL nt:nGt => motion/referenced_in_motion_recommendation_extension_ids:-> motion/recommendation_extension_reference_ids
FIELD 1r:nt => motion/category_id:-> motion_category/motion_ids
FIELD 1r:nt => motion/block_id:-> motion_block/motion_ids
SQL nt:1rR => motion/submitter_ids:-> motion_submitter/motion_id
SQL nt:1rR => motion/supporter_ids:-> motion_supporter/motion_id
SQL nt:1rR => motion/editor_ids:-> motion_editor/motion_id
SQL nt:1rR => motion/working_group_speaker_ids:-> motion_working_group_speaker/motion_id
SQL nt:1GrR => motion/poll_ids:-> poll/content_object_id
SQL nr:1Gr => motion/option_ids:-> option/content_object_id
SQL nt:1rR => motion/change_recommendation_ids:-> motion_change_recommendation/motion_id
SQL nt:1rR => motion/comment_ids:-> motion_comment/motion_id
SQL 1t:1GrR => motion/agenda_item_id:-> agenda_item/content_object_id
SQL 1tR:1GrR => motion/list_of_speakers_id:-> list_of_speakers/content_object_id
SQL nt:nGt => motion/tag_ids:-> tag/tagged_ids
SQL nt:nGt => motion/attachment_meeting_mediafile_ids:-> meeting_mediafile/attachment_ids
SQL nt:1GrR => motion/projection_ids:-> projection/content_object_id
SQL nt:1GrR => motion/personal_note_ids:-> personal_note/content_object_id
FIELD 1rR:nt => motion/meeting_id:-> meeting/motion_ids
SQL nt:1Gr => motion/history_entry_ids:-> history_entry/model_id

SQL nt:1r => motion_block/motion_ids:-> motion/block_id
SQL 1t:1GrR => motion_block/agenda_item_id:-> agenda_item/content_object_id
SQL 1tR:1GrR => motion_block/list_of_speakers_id:-> list_of_speakers/content_object_id
SQL nt:1GrR => motion_block/projection_ids:-> projection/content_object_id
FIELD 1rR:nt => motion_block/meeting_id:-> meeting/motion_block_ids

FIELD 1r:nt => motion_category/parent_id:-> motion_category/child_ids
SQL nt:1r => motion_category/child_ids:-> motion_category/parent_id
SQL nt:1r => motion_category/motion_ids:-> motion/category_id
FIELD 1rR:nt => motion_category/meeting_id:-> meeting/motion_category_ids

FIELD 1rR:nt => motion_change_recommendation/motion_id:-> motion/change_recommendation_ids
FIELD 1rR:nt => motion_change_recommendation/meeting_id:-> meeting/motion_change_recommendation_ids

FIELD 1rR:nt => motion_comment/motion_id:-> motion/comment_ids
FIELD 1rR:nt => motion_comment/section_id:-> motion_comment_section/comment_ids
FIELD 1rR:nt => motion_comment/meeting_id:-> meeting/motion_comment_ids

SQL nt:1rR => motion_comment_section/comment_ids:-> motion_comment/section_id
SQL nt:nt => motion_comment_section/read_group_ids:-> group/read_comment_section_ids
SQL nt:nt => motion_comment_section/write_group_ids:-> group/write_comment_section_ids
FIELD 1rR:nt => motion_comment_section/meeting_id:-> meeting/motion_comment_section_ids

FIELD 1r:nt => motion_editor/meeting_user_id:-> meeting_user/motion_editor_ids
FIELD 1rR:nt => motion_editor/motion_id:-> motion/editor_ids
FIELD 1rR:nt => motion_editor/meeting_id:-> meeting/motion_editor_ids

FIELD 1r:nt => motion_state/submitter_withdraw_state_id:-> motion_state/submitter_withdraw_back_ids
SQL nt:1r => motion_state/submitter_withdraw_back_ids:-> motion_state/submitter_withdraw_state_id
SQL nt:nt => motion_state/next_state_ids:-> motion_state/previous_state_ids
SQL nt:nt => motion_state/previous_state_ids:-> motion_state/next_state_ids
SQL nt:1rR => motion_state/motion_ids:-> motion/state_id
SQL nt:1r => motion_state/motion_recommendation_ids:-> motion/recommendation_id
FIELD 1rR:nt => motion_state/workflow_id:-> motion_workflow/state_ids
SQL 1t:1rR => motion_state/first_state_of_workflow_id:-> motion_workflow/first_state_id
FIELD 1rR:nt => motion_state/meeting_id:-> meeting/motion_state_ids

FIELD 1r:nt => motion_submitter/meeting_user_id:-> meeting_user/motion_submitter_ids
FIELD 1rR:nt => motion_submitter/motion_id:-> motion/submitter_ids
FIELD 1rR:nt => motion_submitter/meeting_id:-> meeting/motion_submitter_ids

FIELD 1r:nt => motion_supporter/meeting_user_id:-> meeting_user/motion_supporter_ids
FIELD 1rR:nt => motion_supporter/motion_id:-> motion/supporter_ids
FIELD 1rR:nt => motion_supporter/meeting_id:-> meeting/motion_supporter_ids

SQL nt:1rR => motion_workflow/state_ids:-> motion_state/workflow_id
FIELD 1rR:1t => motion_workflow/first_state_id:-> motion_state/first_state_of_workflow_id
SQL 1t:1rR => motion_workflow/default_workflow_meeting_id:-> meeting/motions_default_workflow_id
SQL 1t:1rR => motion_workflow/default_amendment_workflow_meeting_id:-> meeting/motions_default_amendment_workflow_id
FIELD 1rR:nt => motion_workflow/meeting_id:-> meeting/motion_workflow_ids

FIELD 1r:nt => motion_working_group_speaker/meeting_user_id:-> meeting_user/motion_working_group_speaker_ids
FIELD 1rR:nt => motion_working_group_speaker/motion_id:-> motion/working_group_speaker_ids
FIELD 1rR:nt => motion_working_group_speaker/meeting_id:-> meeting/motion_working_group_speaker_ids

FIELD 1r:nr => option/poll_id:-> poll/option_ids
SQL 1t:1r => option/used_as_global_option_in_poll_id:-> poll/global_option_id
SQL nr:1rR => option/vote_ids:-> vote/option_id
FIELD 1Gr:nr,nr,1tR => option/content_object_id:-> motion/option_ids,user/option_ids,poll_candidate_list/option_id
FIELD 1rR:nr => option/meeting_id:-> meeting/option_ids

SQL nr:1rR => organization/gender_ids:-> gender/organization_id
SQL nr:1rR => organization/committee_ids:-> committee/organization_id
SQL nt:1r => organization/active_meeting_ids:-> meeting/is_active_in_organization_id
SQL nt:1r => organization/archived_meeting_ids:-> meeting/is_archived_in_organization_id
SQL nt:1r => organization/template_meeting_ids:-> meeting/template_for_organization_id
SQL nr:1rR => organization/organization_tag_ids:-> organization_tag/organization_id
FIELD 1rR:1t => organization/theme_id:-> theme/theme_for_organization_id
SQL nr:1rR => organization/theme_ids:-> theme/organization_id
SQL nt:1GrR => organization/mediafile_ids:-> mediafile/owner_id
SQL nt:1r => organization/published_mediafile_ids:-> mediafile/published_to_meetings_in_organization_id
SQL nr:1rR => organization/user_ids:-> user/organization_id

SQL nGt:nt,nt => organization_tag/tagged_ids:-> committee/organization_tag_ids,meeting/organization_tag_ids
FIELD 1rR:nr => organization_tag/organization_id:-> organization/organization_tag_ids

FIELD 1rR:nt => personal_note/meeting_user_id:-> meeting_user/personal_note_ids
FIELD 1GrR:nt => personal_note/content_object_id:-> motion/personal_note_ids
FIELD 1rR:nt => personal_note/meeting_id:-> meeting/personal_note_ids

FIELD 1rR:nt => point_of_order_category/meeting_id:-> meeting/point_of_order_category_ids
SQL nt:1r => point_of_order_category/speaker_ids:-> speaker/point_of_order_category_id

FIELD 1GrR:nt,nt,nt => poll/content_object_id:-> motion/poll_ids,assignment/poll_ids,topic/poll_ids
SQL nr:1r => poll/option_ids:-> option/poll_id
FIELD 1r:1t => poll/global_option_id:-> option/used_as_global_option_in_poll_id
SQL nt:nt => poll/voted_ids:-> user/poll_voted_ids
SQL nt:nt => poll/entitled_group_ids:-> group/poll_ids
SQL nt:1GrR => poll/projection_ids:-> projection/content_object_id
FIELD 1rR:nr => poll/meeting_id:-> meeting/poll_ids

FIELD 1rR:nr => poll_candidate/poll_candidate_list_id:-> poll_candidate_list/poll_candidate_ids
FIELD 1r:nr => poll_candidate/user_id:-> user/poll_candidate_ids
FIELD 1rR:nr => poll_candidate/meeting_id:-> meeting/poll_candidate_ids

SQL nr:1rR => poll_candidate_list/poll_candidate_ids:-> poll_candidate/poll_candidate_list_id
FIELD 1rR:nr => poll_candidate_list/meeting_id:-> meeting/poll_candidate_list_ids
SQL 1tR:1Gr => poll_candidate_list/option_id:-> option/content_object_id

FIELD 1r:nt => projection/current_projector_id:-> projector/current_projection_ids
FIELD 1r:nt => projection/preview_projector_id:-> projector/preview_projection_ids
FIELD 1r:nt => projection/history_projector_id:-> projector/history_projection_ids
FIELD 1GrR:nt,nt,nt,nt,nt,nt,nt,nt,nt,nt,nt => projection/content_object_id:-> meeting/projection_ids,motion/projection_ids,meeting_mediafile/projection_ids,list_of_speakers/projection_ids,motion_block/projection_ids,assignment/projection_ids,agenda_item/projection_ids,topic/projection_ids,poll/projection_ids,projector_message/projection_ids,projector_countdown/projection_ids
FIELD 1rR:nt => projection/meeting_id:-> meeting/all_projection_ids

SQL nt:1r => projector/current_projection_ids:-> projection/current_projector_id
SQL nt:1r => projector/preview_projection_ids:-> projection/preview_projector_id
SQL nt:1r => projector/history_projection_ids:-> projection/history_projector_id
SQL 1t:1rR => projector/used_as_reference_projector_meeting_id:-> meeting/reference_projector_id
FIELD 1r:ntR => projector/used_as_default_projector_for_agenda_item_list_in_meeting_id:-> meeting/default_projector_agenda_item_list_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_topic_in_meeting_id:-> meeting/default_projector_topic_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_list_of_speakers_in_meeting_id:-> meeting/default_projector_list_of_speakers_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_current_los_in_meeting_id:-> meeting/default_projector_current_los_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_motion_in_meeting_id:-> meeting/default_projector_motion_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_amendment_in_meeting_id:-> meeting/default_projector_amendment_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_motion_block_in_meeting_id:-> meeting/default_projector_motion_block_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_assignment_in_meeting_id:-> meeting/default_projector_assignment_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_mediafile_in_meeting_id:-> meeting/default_projector_mediafile_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_message_in_meeting_id:-> meeting/default_projector_message_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_countdown_in_meeting_id:-> meeting/default_projector_countdown_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_assignment_poll_in_meeting_id:-> meeting/default_projector_assignment_poll_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_motion_poll_in_meeting_id:-> meeting/default_projector_motion_poll_ids
FIELD 1r:ntR => projector/used_as_default_projector_for_poll_in_meeting_id:-> meeting/default_projector_poll_ids
FIELD 1rR:nt => projector/meeting_id:-> meeting/projector_ids

SQL nt:1GrR => projector_countdown/projection_ids:-> projection/content_object_id
SQL 1t:1r => projector_countdown/used_as_list_of_speakers_countdown_meeting_id:-> meeting/list_of_speakers_countdown_id
SQL 1t:1r => projector_countdown/used_as_poll_countdown_meeting_id:-> meeting/poll_countdown_id
FIELD 1rR:nt => projector_countdown/meeting_id:-> meeting/projector_countdown_ids

SQL nt:1GrR => projector_message/projection_ids:-> projection/content_object_id
FIELD 1rR:nt => projector_message/meeting_id:-> meeting/projector_message_ids

FIELD 1rR:nt => speaker/list_of_speakers_id:-> list_of_speakers/speaker_ids
FIELD 1r:nt => speaker/structure_level_list_of_speakers_id:-> structure_level_list_of_speakers/speaker_ids
FIELD 1r:nt => speaker/meeting_user_id:-> meeting_user/speaker_ids
FIELD 1r:nt => speaker/point_of_order_category_id:-> point_of_order_category/speaker_ids
FIELD 1rR:nt => speaker/meeting_id:-> meeting/speaker_ids

SQL nt:nt => structure_level/meeting_user_ids:-> meeting_user/structure_level_ids
SQL nt:1rR => structure_level/structure_level_list_of_speakers_ids:-> structure_level_list_of_speakers/structure_level_id
FIELD 1rR:nt => structure_level/meeting_id:-> meeting/structure_level_ids

FIELD 1rR:nt => structure_level_list_of_speakers/structure_level_id:-> structure_level/structure_level_list_of_speakers_ids
FIELD 1rR:nt => structure_level_list_of_speakers/list_of_speakers_id:-> list_of_speakers/structure_level_list_of_speakers_ids
SQL nt:1r => structure_level_list_of_speakers/speaker_ids:-> speaker/structure_level_list_of_speakers_id
FIELD 1rR:nt => structure_level_list_of_speakers/meeting_id:-> meeting/structure_level_list_of_speakers_ids

SQL nGt:nt,nt,nt => tag/tagged_ids:-> agenda_item/tag_ids,assignment/tag_ids,motion/tag_ids
FIELD 1rR:nt => tag/meeting_id:-> meeting/tag_ids

SQL 1t:1rR => theme/theme_for_organization_id:-> organization/theme_id
FIELD 1rR:nr => theme/organization_id:-> organization/theme_ids

SQL nt:nGt => topic/attachment_meeting_mediafile_ids:-> meeting_mediafile/attachment_ids
SQL 1tR:1GrR => topic/agenda_item_id:-> agenda_item/content_object_id
SQL 1tR:1GrR => topic/list_of_speakers_id:-> list_of_speakers/content_object_id
SQL nt:1GrR => topic/poll_ids:-> poll/content_object_id
SQL nt:1GrR => topic/projection_ids:-> projection/content_object_id
FIELD 1rR:nt => topic/meeting_id:-> meeting/topic_ids

FIELD 1r:nr => user/gender_id:-> gender/user_ids
SQL nt:nt => user/is_present_in_meeting_ids:-> meeting/present_user_ids
SQL nts:nts => user/committee_ids:-> committee/user_ids
SQL nt:nt => user/committee_management_ids:-> committee/manager_ids
SQL nt:1rR => user/meeting_user_ids:-> meeting_user/user_id
SQL nt:nt => user/poll_voted_ids:-> poll/voted_ids
SQL nr:1Gr => user/option_ids:-> option/content_object_id
SQL nr:1r => user/vote_ids:-> vote/user_id
SQL nr:1r => user/delegated_vote_ids:-> vote/delegated_user_id
SQL nr:1r => user/poll_candidate_ids:-> poll_candidate/user_id
FIELD 1r:nt => user/home_committee_id:-> committee/native_user_ids
SQL nt:1r => user/history_position_ids:-> history_position/user_id
SQL nt:1Gr => user/history_entry_ids:-> history_entry/model_id
SQL nts:nts => user/meeting_ids:-> meeting/user_ids
FIELD 1rR:nr => user/organization_id:-> organization/user_ids

FIELD 1rR:nr => vote/option_id:-> option/vote_ids
FIELD 1r:nr => vote/user_id:-> user/vote_ids
FIELD 1r:nr => vote/delegated_user_id:-> user/delegated_vote_ids
FIELD 1rR:nr => vote/meeting_id:-> meeting/vote_ids

*/
/*
There are 2 errors/warnings
    poll/live_votes: type:JSON is marked as a calculated field and not generated in schema
    projection/content: type:JSON is marked as a calculated field and not generated in schema
*/

/*   Missing attribute handling for on_delete, constant_legacy, deferred */