from openslides_backend.migrations import RemoveFieldsMigration


class Migration(RemoveFieldsMigration):
    """
    This migration removes field `motion_state/dont_set_identifier`
    from database-events
    """

    target_migration_index = 9

    collection_fields_map = {"motion_state": ["dont_set_identifier"]}
