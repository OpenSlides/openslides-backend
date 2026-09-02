-- EDIT SECTION --

-- REMOVE SECTION --

-- RENAME SECTION --

-- ADD SECTION --
ALTER TABLE action_worker_t ADD COLUMN created;
UPDATE TABLE committee_t SET organization_id = 1 WHERE organization_id IS NULL;
ALTER TABLE committee_t ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE meeting_t ADD COLUMN name
        CONSTRAINT default_meeting_t_name DEFAULT OpenSlides;
UPDATE TABLE meeting_t SET name = 'OpenSlides' WHERE TRUE;
ALTER TABLE meeting_t ALTER COLUMN name SET NOT NULL;

-- VIEWS UPDATE SECTION --
