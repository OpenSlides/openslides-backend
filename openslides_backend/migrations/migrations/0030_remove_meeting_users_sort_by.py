from openslides_backend.migrations import RemoveFieldsMigration


class Migration(RemoveFieldsMigration):
    """
    This migration removes the field `meeting/users_sort_by`.
    """

    target_migration_index = 31
    collection_fields_map = {"meeting": ["users_sort_by"]}
