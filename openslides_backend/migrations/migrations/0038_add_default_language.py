from datastore.migrations import AddFieldsMigration


class Migration(AddFieldsMigration):
    """
    This migration adds default_language to organization.
    """

    target_migration_index = 39

    defaults = {"organization": {"default_language": "en"}}
