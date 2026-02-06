"""
Migration 0103: Add keycloak_id column to user view.

The user_t table has keycloak_id but the user VIEW was created before this column
was added. Views with SELECT * don't automatically update when columns are added.

This migration recreates the user view to include keycloak_id.
"""

from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.migrations.migration_helper import (
    MigrationHelper,
    MigrationState,
)

# No data migration needed - just updating the view
ORIGIN_COLLECTIONS: list[str] = []


def data_definition(curs: Cursor[DictRow]) -> None:
    """Recreate user view to include keycloak_id column."""
    # Drop and recreate the view
    curs.execute('DROP VIEW IF EXISTS "user" CASCADE;')

    curs.execute('''
CREATE VIEW "user" AS SELECT
    u.id,
    u.username,
    u.member_number,
    u.saml_id,
    u.keycloak_id,
    u.pronoun,
    u.title,
    u.first_name,
    u.last_name,
    u.is_active,
    u.is_physical_person,
    u.password,
    u.default_password,
    u.can_change_own_password,
    u.email,
    u.default_vote_weight,
    u.last_email_sent,
    u.is_demo_user,
    u.last_login,
    u.external,
    u.gender_id,
    u.organization_management_level,
    u.home_committee_id,
    u.organization_id,
    (select array_agg(n.meeting_id ORDER BY n.meeting_id) from nm_meeting_present_user_ids_user_t n where n.user_id = u.id) as is_present_in_meeting_ids,
    (
      SELECT array_remove(array_agg(DISTINCT _.committee_id ORDER BY _.committee_id), NULL)
      FROM (
        SELECT m.committee_id FROM meeting_user_t mu
          JOIN nm_group_meeting_user_ids_meeting_user_t gmu ON mu.id = gmu.meeting_user_id
          JOIN meeting_t m ON m.id = mu.meeting_id
        WHERE mu.user_id = u.id
        UNION
        SELECT cmu.committee_id FROM nm_committee_manager_ids_user_t cmu WHERE cmu.user_id = u.id
        UNION
        SELECT u.home_committee_id WHERE u.home_committee_id IS NOT NULL
      ) _
    ) AS committee_ids,
    (select array_agg(n.committee_id ORDER BY n.committee_id) from nm_committee_manager_ids_user_t n where n.user_id = u.id) as committee_management_ids,
    (select array_agg(m.id ORDER BY m.id) from meeting_user_t m where m.user_id = u.id) as meeting_user_ids,
    (select array_agg(n.poll_id ORDER BY n.poll_id) from nm_poll_voted_ids_user_t n where n.user_id = u.id) as poll_voted_ids,
    (select array_agg(o.id ORDER BY o.id) from option_t o where o.content_object_id_user_id = u.id) as option_ids,
    (select array_agg(v.id ORDER BY v.id) from vote_t v where v.user_id = u.id) as vote_ids,
    (select array_agg(v.id ORDER BY v.id) from vote_t v where v.delegated_user_id = u.id) as delegated_vote_ids,
    (select array_agg(p.id ORDER BY p.id) from poll_candidate_t p where p.user_id = u.id) as poll_candidate_ids,
    (select array_agg(h.id ORDER BY h.id) from history_position_t h where h.user_id = u.id) as history_position_ids,
    (select array_agg(h.id ORDER BY h.id) from history_entry_t h where h.model_id_user_id = u.id) as history_entry_ids,
    (SELECT array_agg(DISTINCT mu.meeting_id ORDER BY mu.meeting_id) FROM meeting_user_t mu WHERE mu.user_id = u.id) AS meeting_ids
FROM user_t u;
    ''')

    # Add comments
    curs.execute("""
        COMMENT ON COLUMN "user".committee_ids IS 'Calculated field: Returns committee_ids, where the user is manager or member in a meeting';
    """)
    curs.execute("""
        COMMENT ON COLUMN "user".meeting_ids IS 'Calculated. All ids from meetings calculated via meeting_user.';
    """)

    curs.connection.commit()

    MigrationHelper.set_database_migration_info(
        curs, 103, MigrationState.FINALIZATION_REQUIRED
    )
