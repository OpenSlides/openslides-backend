from datastore.migrations import RemoveFieldsMigration


class Migration(RemoveFieldsMigration):
    """
    This migration removes the field `poll.publish_immediately`.
    There was a bug, which introduced it in poll.create and poll.update.
    """

    target_migration_index = 28

    collection_fields_map = {"poll": ["publish_immediately"]}
