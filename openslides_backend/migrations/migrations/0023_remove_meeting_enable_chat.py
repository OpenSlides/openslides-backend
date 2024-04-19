from openslides_backend.migrations import RemoveFieldsMigration


class Migration(RemoveFieldsMigration):
    """
    This migration removes the field `meeting/enable_chat`.
    """

    target_migration_index = 24
    collection_fields_map = {"meeting": ["enable_chat"]}
