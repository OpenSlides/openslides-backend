from datastore.migrations import RemoveFieldMigration


class Migration(RemoveFieldMigration):
    """
    This migration removes field `meeting/users_pdf_url`
    from database-events
    """

    target_migration_index = 17

    collection = "meeting"
    field = "users_pdf_url"
