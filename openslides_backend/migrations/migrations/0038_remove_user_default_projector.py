from datastore.migrations import RemoveFieldsMigration


class Migration(RemoveFieldsMigration):
    """
    This migration removes the field `meeting/default_projector_$user_ids`.
    """

    target_migration_index = 39
    collection_fields_map = {"meeting": ["default_projector_$user_ids"]}
