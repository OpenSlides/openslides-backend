-- REMOVE SECTION --

-- RENAME SECTION --

-- ADD SECTION --
ALTER TABLE meeting_t
    ADD COLUMN motions_enable_consultation_sequence boolean
        CONSTRAINT default_meeting_motions_enable_consultation_sequence DEFAULT True;


-- EDIT SECTION --

-- VIEWS UPDATE SECTION --
DROP VIEW IF EXISTS "meeting";

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
