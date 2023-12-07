-- this script can only be used for an empty database without used sequences
BEGIN;
INSERT INTO themeT (name, accent_500, primary_500, warn_500, organization_id) values ('standard theme', 2201331, 3241878, 15754240, 1);
INSERT INTO organizationT (name, theme_id, default_language) values ('Intevation', 1, 'en');

INSERT INTO committeeT (name, organization_id) VALUES ('c1', 1), ('c2', 1), ('c3', 1), ('c4', 1);
-- INSERT INTO forwarding_committee_to_committee values (1, 2), (1, 3), (4, 1);

-- meeting1 in committee 1 with 2 groups, simple workflow and 1 reference projector
INSERT INTO meetingT (default_group_id, admin_group_id,
    motions_default_workflow_id, motions_default_amendment_workflow_id,
    motions_default_statute_amendment_workflow_id,
    committee_id, reference_projector_id, name)
    VALUES (1, 2, 1, 1, 1, 1, 1, 'meeting1');
INSERT INTO motion_workflowT (name, sequential_number, first_state_id, meeting_id)
    VALUES ('Simple Workflow', 1, 1, 1);
INSERT INTO motion_stateT (name, weight, workflow_id, meeting_id, allow_create_poll, allow_support, set_workflow_timestamp)
    VALUES ('submitted', 1, 1, 1, true, true, true);
INSERT INTO motion_stateT (name, weight, workflow_id, meeting_id, 
    recommendation_label, css_class, merge_amendment_into_final) VALUES
    ('accepted', 2, 1, 1, 'Acceptance', 'green', 'do_merge'),
    ('rejected', 3, 1, 1, 'Rejection', 'red', 'do_not_merge'),
    ('not decided', 4, 1, 1, 'No decision', 'grey', 'do_not_merge');
-- INSERT INTO motion_state_to_stateT (previous_state_id, next_state_id) VALUES
--    (1, 2), (1, 3), (1,4);
INSERT INTO projectorT (name, sequential_number, meeting_id) VALUES ('Projektor 1', 1, 1);

-- -- meeting2 in committee 2 with 2 groups, simple workflow and 1 reference projector
INSERT INTO meetingT (default_group_id, admin_group_id,
    motions_default_workflow_id, motions_default_amendment_workflow_id,
    motions_default_statute_amendment_workflow_id,
    committee_id, reference_projector_id, name)
    VALUES (3, 4, 2, 2, 2, 2, 2, 'meeting2');
INSERT INTO groupT (name, meeting_id, permissions)
    VALUES
    ('Default', 2, '{
        "agenda_item.can_see_internal",
        "list_of_speakers.can_see",
        "mediafile.can_see",
        "meeting.can_see_frontpage",
        "motion.can_see",
        "projector.can_see",
        "user.can_see"
    }'), ('Admin', 2, DEFAULT);
-- Update a specific cell
UPDATE groupt set permissions[3] = 'user.can_manage'  where name = 'Default';
INSERT INTO motion_workflowT (name, sequential_number, first_state_id, meeting_id)
    VALUES ('Simple Workflow', 1, 5, 2);
INSERT INTO motion_stateT (name, weight, workflow_id, meeting_id, allow_create_poll, allow_support, set_workflow_timestamp)
    VALUES ('submitted', 1, 2, 2, true, true, true);
INSERT INTO motion_stateT (name, weight, workflow_id, meeting_id, 
    recommendation_label, css_class, merge_amendment_into_final) VALUES
    ('accepted', 2, 2, 2, 'Acceptance', 'green', 'do_merge'),
    ('rejected', 3, 2, 2, 'Rejection', 'red', 'do_not_merge'),
    ('not decided', 4, 2, 2, 'No decision', 'grey', 'do_not_merge');
-- INSERT INTO motion_state_to_state (previous_state_id, next_state_id) VALUES
--    (5, 6), (5, 7), (8, 5);
INSERT INTO projectorT (name, sequential_number, meeting_id) VALUES ('Projektor 2', 1, 2);

-- -- user 1 to 4 with relations to meetings and committes as managers
-- INSERT INTO userT (username) values ('u1_m1'), ('u2_m2'), ('u3_c1manager'), ('u4_m1m2c1managerc3manager');
-- INSERT INTO group_to_user (user_id, group_id) values (1, 1), (2, 4), (4, 1), (4, 3);
-- INSERT INTO committee_to_user (user_id, committee_id) values (3, 1), (4, 1), (4,3);

COMMIT;