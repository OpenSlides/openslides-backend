-- Some Notes:
-- * The collection names are maxed to 32 characters.
-- * fqids can be max 48 chars long. The longest collection is currently `motion_change_recommendation` with 28 chars. The
--   maximum is 32 chars. So 15 chars are left for ids, which means there can be (10^16)-1 ids. That are about 4.5x10^6 more ids
--   in 15 characters in comparison to (2^31)-1 for the sql INTEGER type. This should be enough.
-- * In contrast, collectionfields can be very long in fact of structured keys. I choose 255 to be save. Maybe this can be
--   reduced in the future to save space...


-- Why doesn't postgres have a "CREATE TYPE IF NOT EXISTS"???????
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_type') THEN
        CREATE TYPE event_type AS ENUM ('create', 'update', 'delete', 'deletefields', 'listfields', 'restore');
    ELSE
        RAISE NOTICE 'type "event_type" already exists, skipping';
    END IF;
END$$;

CREATE OR REPLACE FUNCTION models_updated() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated = current_timestamp;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS positions (
    position INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    timestamp TIMESTAMPTZ,
    user_id INTEGER NOT NULL,
    information JSON,
    migration_index INTEGER NOT NULL
);

-- Note that this schema (and indices, ...) also affect migration_events!
CREATE TABLE IF NOT EXISTS events (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    position INTEGER REFERENCES positions(position) ON DELETE CASCADE,
    fqid VARCHAR(48) NOT NULL,
    type event_type NOT NULL,
    data JSONB,
    weight INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS event_position_idx ON events (position);
CREATE INDEX IF NOT EXISTS event_fqid_idx ON events (fqid);
CREATE INDEX IF NOT EXISTS event_data_meeting_id_idx ON events ((data->>'meeting_id')) WHERE data->>'meeting_id' IS NOT NULL;

-- For the `reserve_ids` feature
CREATE TABLE IF NOT EXISTS id_sequences (
    collection VARCHAR(32) PRIMARY KEY,
    id INTEGER NOT NULL
);

-- Helper tables
CREATE TABLE IF NOT EXISTS collectionfields (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    collectionfield VARCHAR(255) UNIQUE NOT NULL,
    position INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS collectionfields_collectionfield_idx on collectionfields (collectionfield);

CREATE TABLE IF NOT EXISTS events_to_collectionfields (
    event_id BIGINT, -- no reference to events(id) here since it is swapped with migration_events on
    -- each migration. Since the events are append only (except for migrations, but this table is
    -- cleared there), we does not have to worry about data cosistency. Joining etc. still works, even
    -- if there is no foreign key relationship.
    collectionfield_id BIGINT REFERENCES collectionfields(id) ON DELETE CASCADE,
    CONSTRAINT events_to_collectionfields_pkey PRIMARY KEY (event_id, collectionfield_id)
);

CREATE TABLE IF NOT EXISTS models (
    fqid VARCHAR(48) PRIMARY KEY,
    data JSONB NOT NULL,
    deleted BOOLEAN NOT NULL,
    updated TIMESTAMP NOT NULL DEFAULT current_timestamp
);

-- The following field was introduced with an update. To make sure the column exists the table
-- is altered and the column added. This could maybe be deleted in the future.
ALTER TABLE models ADD COLUMN IF NOT EXISTS updated timestamp NOT NULL DEFAULT current_timestamp;

-- Trigger for setting the models updated column
DROP TRIGGER IF EXISTS models_updated_trigger ON models;
CREATE TRIGGER models_updated_trigger
    BEFORE INSERT OR UPDATE ON models
    FOR EACH ROW EXECUTE FUNCTION models_updated();

-- Migrations
CREATE TABLE IF NOT EXISTS migration_keyframes (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    position INTEGER REFERENCES positions(position) ON DELETE CASCADE NOT NULL,
    migration_index INTEGER NOT NULL,
    UNIQUE (position, migration_index)
);
CREATE INDEX IF NOT EXISTS migration_keyframes_idx ON migration_keyframes (position, migration_index);

CREATE TABLE IF NOT EXISTS migration_keyframe_models (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    keyframe_id INTEGER REFERENCES migration_keyframes(id) ON DELETE CASCADE NOT NULL,
    fqid VARCHAR(48) NOT NULL,
    data JSONB NOT NULL,
    deleted BOOLEAN NOT NULL,
    UNIQUE (keyframe_id, fqid)
);
CREATE INDEX IF NOT EXISTS migration_keyframe_models_idx ON migration_keyframe_models (keyframe_id, fqid);

CREATE TABLE IF NOT EXISTS migration_events (LIKE events INCLUDING ALL);

CREATE TABLE IF NOT EXISTS migration_positions (
    position INTEGER PRIMARY KEY,
    migration_index INTEGER NOT NULL
);
