from datastore.migrations import RemoveFieldMigration


class Migration(RemoveFieldMigration):
    """
    This migration removes field `meeting/url_name`
    from database-events.
    """

    target_migration_index = 18

    collection = "meeting"
    field = "url_name"
