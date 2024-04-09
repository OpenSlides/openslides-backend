from openslides_backend.migrations import RemoveFieldsMigration


class Migration(RemoveFieldsMigration):
    """
    This migration removes the field `motion/workflow_id`.
    There was a bug, which introduced it in motion.update.
    """

    target_migration_index = 16

    collection_fields_map = {"motion": ["workflow_id"]}
