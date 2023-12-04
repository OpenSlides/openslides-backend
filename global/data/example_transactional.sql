-- this script can only be used for an empty database without used sequences
BEGIN;
-- INSERT INTO themeT (name, accent_500, primary_500, warn_500) values ('standard theme', 2201331, 3241878, 15754240);
-- INSERT INTO organizationT (name, theme_id, default_language) values ('Intevation', 1, 'en');

-- INSERT INTO committeeT (name) VALUES ('c1'), ('c2'), ('c3'), ('c4');
-- INSERT INTO forwarding_committee_to_committee values (1, 2), (1, 3), (4, 1);

-- -- meeting1 in committee 1 with 2 groups, simple workflow and 1 reference projector
-- INSERT INTO meetingT (default_group_id, admin_group_id,
--     motions_default_workflow_id, motions_default_amendment_workflow_id,
--     motions_default_statute_amendment_workflow_id,
--     committee_id, reference_projector_id, name)
--     VALUES (1, 2, 1, 1, 1, 1, 1, 'meeting1');
INSERT INTO groupT (name, permissions)
    VALUES
    ('Standard', '{
        "agenda_item.can_see_internal",
        "assignment.can_see",
        "projector.can_see",
        "user.can_see"
    }'), ('Admin', DEFAULT);

-- Update a specific cell
UPDATE groupt set permissions[3] = 'motion.can_see'  where name = 'Standard';

-- INSERT INTO motion_workflow (name, sequential_number, first_state_id, meeting_id)
--     VALUES ('Simple Workflow', 1, 1, 1);
-- INSERT INTO motion_state (name, weight, workflow_id, meeting_id, allow_create_poll, allow_support, set_created_timestamp)
--     VALUES ('submitted', 1, 1, 1, true, true, true);
-- INSERT INTO motion_state (name, weight, workflow_id, meeting_id, 
--     recommendation_label, css_class, merge_amendment_into_final) VALUES
--     ('accepted', 2, 1, 1, 'Acceptance', 'green', 'do_merge'),
--     ('rejected', 3, 1, 1, 'Rejection', 'red', 'do_not_merge'),
--     ('not decided', 4, 1, 1, 'No decision', 'grey', 'do_not_merge');
-- INSERT INTO motion_state_to_state (previous_state_id, next_state_id) VALUES
--     (1, 2), (1, 3), (1,4);
-- INSERT INTO projector (name, sequential_number, meeting_id) VALUES ('Projektor 1', 1, 1);

-- -- meeting2 in committee 2 with 2 groups, simple workflow and 1 reference projector
-- INSERT INTO meetingT (default_group_id, admin_group_id,
--     motions_default_workflow_id, motions_default_amendment_workflow_id,
--     motions_default_statute_amendment_workflow_id,
--     committee_id, reference_projector_id, name)
--     VALUES (3, 4, 2, 2, 2, 2, 2, 'meeting2');
-- INSERT INTO groupT (name, meeting_id, permissions)
--     VALUES
--     ('Default', 2, ARRAY[
--         'agenda_item.can_see_internal',
--         'assignment.can_see',
--         'list_of_speakers.can_see',
--         'mediafile.can_see',
--         'meeting.can_see_frontpage',
--         'motion.can_see',
--         'projector.can_see',
--         'user.can_see'
--     ]), ('Admin', 2, DEFAULT);
-- INSERT INTO motion_workflow (name, sequential_number, first_state_id, meeting_id)
--     VALUES ('Simple Workflow', 1, 5, 2);
-- INSERT INTO motion_state (name, weight, workflow_id, meeting_id, allow_create_poll, allow_support, set_created_timestamp)
--     VALUES ('submitted', 1, 2, 2, true, true, true);
-- INSERT INTO motion_state (name, weight, workflow_id, meeting_id, 
--     recommendation_label, css_class, merge_amendment_into_final) VALUES
--     ('accepted', 2, 2, 2, 'Acceptance', 'green', 'do_merge'),
--     ('rejected', 3, 2, 2, 'Rejection', 'red', 'do_not_merge'),
--     ('not decided', 4, 2, 2, 'No decision', 'grey', 'do_not_merge');
-- INSERT INTO motion_state_to_state (previous_state_id, next_state_id) VALUES
--     (5, 6), (5, 7), (8, 5);
-- INSERT INTO projector (name, sequential_number, meeting_id) VALUES ('Projektor 2', 1, 2);

-- -- user 1 to 4 with relations to meetings and committes as managers
-- INSERT INTO userT (username) values ('u1_m1'), ('u2_m2'), ('u3_c1manager'), ('u4_m1m2c1managerc3manager');
-- INSERT INTO group_to_user (user_id, group_id) values (1, 1), (2, 4), (4, 1), (4, 3);
-- INSERT INTO committee_to_user (user_id, committee_id) values (3, 1), (4, 1), (4,3);

COMMIT;