-- EDIT SECTION --

-- REMOVE SECTION --
DROP TABLE deleted_t CASCADE;
ALTER TABLE agenda_item_t DROP COLUMN closed CASCADE;
ALTER TABLE agenda_item_t DROP COLUMN parent_id CASCADE;
ALTER TABLE chat_group_t DROP CONSTRAINT unique_chat_group_meeting_id_name;
ALTER TABLE committee_t DROP COLUMN parent_id CASCADE;
ALTER TABLE history_entry_t DROP COLUMN model_id CASCADE;
ALTER TABLE mediafile_t DROP COLUMN parent_id CASCADE;
DROP TABLE gm_meeting_mediafile_attachment_ids_t CASCADE;
DROP TABLE gm_motion_state_extension_reference_ids_t CASCADE;
DROP TABLE gm_organization_tag_tagged_ids_t CASCADE;
DROP TABLE nm_group_meeting_user_ids_meeting_user_t CASCADE;
DROP TRIGGER equal_meeting_id_on_agenda_item_t_content_object_id_assieb89ee8 ON agenda_item_t;
DROP TRIGGER equal_meeting_id_on_assignment_t_agenda_item_id ON assignment_t;
DROP TRIGGER equal_meeting_id_on_agenda_item_t_content_object_id_motion_id ON agenda_item_t;
DROP TRIGGER equal_meeting_id_on_motion_t_agenda_item_id ON motion_t;
DROP TRIGGER equal_meeting_id_on_agenda_item_t_parent_id ON agenda_item_t;
DROP TRIGGER equal_meeting_id_on_agenda_item_t_child_ids ON agenda_item_t;
DROP TRIGGER equal_meeting_id_on_assignment_candidate_t_assignment_id ON assignment_candidate_t;
DROP TRIGGER equal_meeting_id_on_assignment_t_candidate_ids ON assignment_t;
DROP TRIGGER equal_meeting_id_on_meeting_mediafile_t_attachment_ids_a02016b9 ON meeting_mediafile_t;
DROP TRIGGER equal_meeting_id_on_assignment_t_attachment_meeting_media9bbdf7 ON assignment_t;
DROP TRIGGER equal_meeting_id_on_meeting_mediafile_t_attachment_ids_topic_t ON meeting_mediafile_t;
DROP TRIGGER equal_meeting_id_on_topic_t_attachment_meeting_mediafile_ids ON topic_t;
DROP TRIGGER equal_meeting_id_on_chat_group_t_read_group_ids ON chat_group_t;
DROP TRIGGER equal_meeting_id_on_group_t_read_chat_group_ids ON group_t;
DROP TRIGGER equal_meeting_id_on_chat_group_t_read_group_ids_intermediate ON nm_chat_group_read_group_ids_group_t;
DROP TRIGGER equal_meeting_id_on_group_t_meeting_user_ids ON group_t;
DROP TRIGGER equal_meeting_id_on_meeting_user_t_group_ids ON meeting_user_t;
DROP TRIGGER equal_owner_id_on_mediafile_t_parent_id ON mediafile_t;
DROP TRIGGER equal_owner_id_on_mediafile_t_child_ids ON mediafile_t;
DROP TRIGGER equal_meeting_id_on_motion_t_state_extension_reference_ia334c80 ON motion_t;
DROP TRIGGER equal_meeting_id_on_motion_t_referenced_in_motion_state_cb2bfc0 ON motion_t;

-- RENAME SECTION --

-- ADD SECTION --

-- VIEWS UPDATE SECTION --
CREATE OR REPLACE VIEW "agenda_item" AS SELECT *,
(select array_agg(g.tag_id ORDER BY g.tag_id) from gm_tag_tagged_ids_t g where g.tagged_id_agenda_item_id = a.id) as tag_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_agenda_item_id = a.id) as projection_ids
FROM agenda_item_t a;


CREATE OR REPLACE VIEW "assignment" AS SELECT *,
(select array_agg(ac.id ORDER BY ac.id) from assignment_candidate_t ac where ac.assignment_id = a.id) as candidate_ids,
(select array_agg(p.id ORDER BY p.id) from poll_t p where p.content_object_id_assignment_id = a.id) as poll_ids,
(select ai.id from agenda_item_t ai where ai.content_object_id_assignment_id = a.id) as agenda_item_id,
(select l.id from list_of_speakers_t l where l.content_object_id_assignment_id = a.id) as list_of_speakers_id,
(select array_agg(g.tag_id ORDER BY g.tag_id) from gm_tag_tagged_ids_t g where g.tagged_id_assignment_id = a.id) as tag_ids,
(select array_agg(g.meeting_mediafile_id ORDER BY g.meeting_mediafile_id) from gm_meeting_mediafile_attachment_ids_t g where g.attachment_id_assignment_id = a.id) as attachment_meeting_mediafile_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_assignment_id = a.id) as projection_ids
FROM assignment_t a;


CREATE OR REPLACE VIEW "committee" AS SELECT *,
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
(select array_agg(n.all_parent_id ORDER BY n.all_parent_id) from nm_committee_all_child_ids_committee_t n where n.all_child_id = c.id) as all_parent_ids,
(select array_agg(n.all_child_id ORDER BY n.all_child_id) from nm_committee_all_child_ids_committee_t n where n.all_parent_id = c.id) as all_child_ids,
(select array_agg(u.id ORDER BY u.id) from user_t u where u.home_committee_id = c.id) as native_user_ids,
(select array_agg(n.forward_to_committee_id ORDER BY n.forward_to_committee_id) from nm_committee_forward_to_committee_ids_committee_t n where n.receive_forwardings_from_committee_id = c.id) as forward_to_committee_ids,
(select array_agg(n.receive_forwardings_from_committee_id ORDER BY n.receive_forwardings_from_committee_id) from nm_committee_forward_to_committee_ids_committee_t n where n.forward_to_committee_id = c.id) as receive_forwardings_from_committee_ids
FROM committee_t c;

comment on column "committee".user_ids is 'Calculated field: All users which are in a group of a meeting, belonging to the committee or beeing manager of the committee';

CREATE OR REPLACE VIEW "group" AS SELECT *,
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

CREATE OR REPLACE VIEW "history_entry" AS SELECT * FROM history_entry_t h;


CREATE OR REPLACE VIEW "mediafile" AS SELECT *,
(select array_agg(mm.id ORDER BY mm.id) from meeting_mediafile_t mm where mm.mediafile_id = m.id) as meeting_mediafile_ids
FROM mediafile_t m;


CREATE OR REPLACE VIEW "meeting" AS SELECT *,
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

CREATE OR REPLACE VIEW "meeting_user" AS SELECT *,
(select array_agg(p.id ORDER BY p.id) from personal_note_t p where p.meeting_user_id = m.id) as personal_note_ids,
(select array_agg(s.id ORDER BY s.id) from speaker_t s where s.meeting_user_id = m.id) as speaker_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_supporter_t ms where ms.meeting_user_id = m.id) as motion_supporter_ids,
(select array_agg(me.id ORDER BY me.id) from motion_editor_t me where me.meeting_user_id = m.id) as motion_editor_ids,
(select array_agg(mw.id ORDER BY mw.id) from motion_working_group_speaker_t mw where mw.meeting_user_id = m.id) as motion_working_group_speaker_ids,
(select array_agg(ms.id ORDER BY ms.id) from motion_submitter_t ms where ms.meeting_user_id = m.id) as motion_submitter_ids,
(select array_agg(a.id ORDER BY a.id) from assignment_candidate_t a where a.meeting_user_id = m.id) as assignment_candidate_ids,
(select array_agg(mu.id ORDER BY mu.id) from meeting_user_t mu where mu.vote_delegated_to_id = m.id) as vote_delegations_from_ids,
(select array_agg(c.id ORDER BY c.id) from chat_message_t c where c.meeting_user_id = m.id) as chat_message_ids,
(select array_agg(n.structure_level_id ORDER BY n.structure_level_id) from nm_meeting_user_structure_level_ids_structure_level_t n where n.meeting_user_id = m.id) as structure_level_ids
FROM meeting_user_t m;


CREATE OR REPLACE VIEW "motion" AS SELECT *,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.lead_motion_id = m.id) as amendment_ids,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.sort_parent_id = m.id) as sort_child_ids,
(select array_agg(mt.id ORDER BY mt.id) from motion_t mt where mt.origin_id = m.id) as derived_motion_ids,
(select array_agg(n.all_origin_id ORDER BY n.all_origin_id) from nm_motion_all_derived_motion_ids_motion_t n where n.all_derived_motion_id = m.id) as all_origin_ids,
(select array_agg(n.all_derived_motion_id ORDER BY n.all_derived_motion_id) from nm_motion_all_derived_motion_ids_motion_t n where n.all_origin_id = m.id) as all_derived_motion_ids,
(select array_cat((select array_agg(n.identical_motion_id_1 ORDER BY n.identical_motion_id_1) from nm_motion_identical_motion_ids_motion_t n where n.identical_motion_id_2 = m.id), (select array_agg(n.identical_motion_id_2 ORDER BY n.identical_motion_id_2) from nm_motion_identical_motion_ids_motion_t n where n.identical_motion_id_1 = m.id))) as identical_motion_ids,
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
(select l.id from list_of_speakers_t l where l.content_object_id_motion_id = m.id) as list_of_speakers_id,
(select array_agg(g.tag_id ORDER BY g.tag_id) from gm_tag_tagged_ids_t g where g.tagged_id_motion_id = m.id) as tag_ids,
(select array_agg(g.meeting_mediafile_id ORDER BY g.meeting_mediafile_id) from gm_meeting_mediafile_attachment_ids_t g where g.attachment_id_motion_id = m.id) as attachment_meeting_mediafile_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_motion_id = m.id) as projection_ids,
(select array_agg(p.id ORDER BY p.id) from personal_note_t p where p.content_object_id_motion_id = m.id) as personal_note_ids
FROM motion_t m;


CREATE OR REPLACE VIEW "organization_tag" AS SELECT * FROM organization_tag_t o;


CREATE OR REPLACE VIEW "topic" AS SELECT *,
(select a.id from agenda_item_t a where a.content_object_id_topic_id = t.id) as agenda_item_id,
(select l.id from list_of_speakers_t l where l.content_object_id_topic_id = t.id) as list_of_speakers_id,
(select array_agg(p.id ORDER BY p.id) from poll_t p where p.content_object_id_topic_id = t.id) as poll_ids,
(select array_agg(p.id ORDER BY p.id) from projection_t p where p.content_object_id_topic_id = t.id) as projection_ids
FROM topic_t t;


CREATE OR REPLACE VIEW "user" AS SELECT *,
(select array_agg(n.meeting_id ORDER BY n.meeting_id) from nm_meeting_present_user_ids_user_t n where n.user_id = u.id) as is_present_in_meeting_ids,
(select array_agg(n.committee_id ORDER BY n.committee_id) from nm_committee_manager_ids_user_t n where n.user_id = u.id) as committee_management_ids,
(select array_agg(m.id ORDER BY m.id) from meeting_user_t m where m.user_id = u.id) as meeting_user_ids,
(select array_agg(n.poll_id ORDER BY n.poll_id) from nm_poll_voted_ids_user_t n where n.user_id = u.id) as poll_voted_ids,
(select array_agg(o.id ORDER BY o.id) from option_t o where o.content_object_id_user_id = u.id) as option_ids,
(select array_agg(v.id ORDER BY v.id) from vote_t v where v.user_id = u.id) as vote_ids,
(select array_agg(v.id ORDER BY v.id) from vote_t v where v.delegated_user_id = u.id) as delegated_vote_ids,
(select array_agg(p.id ORDER BY p.id) from poll_candidate_t p where p.user_id = u.id) as poll_candidate_ids,
(select array_agg(h.id ORDER BY h.id) from history_position_t h where h.user_id = u.id) as history_position_ids,
(
  SELECT array_agg(DISTINCT mu.meeting_id ORDER BY mu.meeting_id)
  FROM meeting_user_t mu
  WHERE mu.user_id = u.id
) AS meeting_ids

FROM user_t u;

comment on column "user".committee_ids is 'Calculated field: Returns committee_ids, where the user is manager or member in a meeting';
comment on column "user".meeting_ids is 'Calculated. All ids from meetings calculated via meeting_user.';
