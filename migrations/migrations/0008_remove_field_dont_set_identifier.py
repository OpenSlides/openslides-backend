from datastore.migrations import RemoveFieldMigration


class Migration(RemoveFieldMigration):
    """
    This migration removes field `motion_state/dont_set_identifier`
    from database-events
    """

    target_migration_index = 9

    collection = "motion_state"
    field = "dont_set_identifier"
