DROP VIEW "poll";
ALTER TABLE poll_t ALTER COLUMN config_id SET NOT NULL;
ALTER TABLE poll_t ALTER COLUMN visibility SET NOT NULL;
ALTER TABLE poll_t ALTER COLUMN state TYPE enum_poll_state USING state::enum_poll_state;
ALTER TABLE poll_t ALTER COLUMN state SET DEFAULT 'created';

CREATE OR REPLACE VIEW "poll" AS SELECT *,
(select array_agg(po.id ORDER BY po.id) from poll_option_t po where po.poll_id = p.id) as option_ids,
(select array_agg(pb.id ORDER BY pb.id) from poll_ballot_t pb where pb.poll_id = p.id) as ballot_ids,
(select array_agg(pb.id ORDER BY pb.id) from poll_ballot_user_t pb where pb.poll_id = p.id) as ballot_user_ids,
(select array_agg(n.group_id ORDER BY n.group_id) from nm_group_poll_ids_poll_t n where n.poll_id = p.id) as entitled_group_ids,
(select array_agg(pe.id ORDER BY pe.id) from poll_entitled_user_t pe where pe.poll_id = p.id) as entitled_user_ids,
(select array_agg(pt.id ORDER BY pt.id) from projection_t pt where pt.content_object_id_poll_id = p.id) as projection_ids
FROM poll_t p;
