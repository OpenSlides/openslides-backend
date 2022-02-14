from datastore.migrations import RemoveFieldMigration


class Migration(RemoveFieldMigration):
    """
    This migration removes the field `motion/workflow_id`.
    There was a bug, which introduced it in motion.update.
    """

    target_migration_index = 16

    collection = "motion"
    field = "workflow_id"
