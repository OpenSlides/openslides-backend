DROP VIEW "poll";
ALTER TABLE poll_t ALTER COLUMN config_id SET NOT NULL;
ALTER TABLE poll_t ALTER COLUMN visibility SET NOT NULL;
ALTER TABLE poll_t ALTER COLUMN state TYPE enum_poll_state USING state::enum_poll_state;
ALTER TABLE poll_t ALTER COLUMN state SET DEFAULT 'created';

CREATE VIEW "poll" AS SELECT *,
array(select po.id from poll_option_t po where po.poll_id = p.id ORDER BY po.id) as option_ids,
array(select pb.id from poll_ballot_t pb where pb.poll_id = p.id ORDER BY pb.id) as ballot_ids,
array(select pb.id from poll_ballot_user_t pb where pb.poll_id = p.id ORDER BY pb.id) as ballot_user_ids,
array(select n.group_id from nm_group_poll_ids_poll_t n where n.poll_id = p.id ORDER BY n.group_id) as entitled_group_ids,
array(select pe.id from poll_entitled_user_t pe where pe.poll_id = p.id ORDER BY pe.id) as entitled_user_ids,
array(select pt.id from projection_t pt where pt.content_object_id_poll_id = p.id ORDER BY pt.id) as projection_ids
FROM poll_t p;
