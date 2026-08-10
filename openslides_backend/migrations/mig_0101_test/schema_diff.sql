-- EDIT SECTION --

-- REMOVE SECTION --
DROP TABLE deleted_t CASCADE;
DROP TRIGGER equal_meeting_id_on_assignment_candidate_t_assignment_id ON assignment_candidate_t;
DROP TRIGGER equal_meeting_id_on_assignment_t_candidate_ids ON assignment_t;

-- RENAME SECTION --

-- ADD SECTION --
