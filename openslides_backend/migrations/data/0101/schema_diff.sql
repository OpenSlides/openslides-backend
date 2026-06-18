ALTER TABLE agenda_item_t ADD COLUMN type
        CONSTRAINT default_agenda_item_t_type DEFAULT This was added.;
ALTER TABLE assignment_t ADD COLUMN category_id;
ALTER TABLE meeting_t ADD COLUMN assignment_category_ids;
ALTER TABLE agenda_item_t ALTER COLUMN type DROP CONSTRAINT default_agenda_item_t_type;
ALTER TABLE agenda_item_t ALTER COLUMN type ADD
        CONSTRAINT default_agenda_item_t_type DEFAULT This was changed.;
