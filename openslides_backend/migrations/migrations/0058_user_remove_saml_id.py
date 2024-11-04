from datastore.migrations import RemoveFieldsMigration


class Migration(RemoveFieldsMigration):
    """
    This migration removes field `user/saml_id` from database-events
    """

    target_migration_index = 59

    collection_fields_map = {"user": ["saml_id"]}
