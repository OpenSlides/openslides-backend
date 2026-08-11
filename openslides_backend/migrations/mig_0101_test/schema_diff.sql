-- EDIT SECTION --

-- REMOVE SECTION --
DROP TABLE deleted_t CASCADE;
DROP TRIGGER equal_meeting_id_on_agenda_item_t_content_object_id_assieb89ee8 ON agenda_item_t;
DROP TRIGGER equal_meeting_id_on_assignment_t_agenda_item_id ON assignment_t;
DROP TRIGGER equal_meeting_id_on_assignment_candidate_t_assignment_id ON assignment_candidate_t;
DROP TRIGGER equal_meeting_id_on_assignment_t_candidate_ids ON assignment_t;
DROP TRIGGER equal_meeting_id_on_chat_group_t_read_group_ids ON chat_group_t;
DROP TRIGGER equal_meeting_id_on_group_t_read_chat_group_ids ON group_t;
DROP TRIGGER equal_meeting_id_on_chat_group_t_read_group_ids_intermediate ON nm_chat_group_read_group_ids_group_t;

-- RENAME SECTION --

-- ADD SECTION --
