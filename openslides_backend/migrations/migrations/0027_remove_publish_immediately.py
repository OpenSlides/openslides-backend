from openslides_backend.migrations import RemoveFieldsMigration


class Migration(RemoveFieldsMigration):
    """
    This migration removes the field `poll.publish_immediately` and
    `option.publish_immediately`.
    There was a bug, which introduced it in poll.create, poll.update
    and option.update.
    """

    target_migration_index = 28

    collection_fields_map = {
        "poll": ["publish_immediately"],
        "option": ["publish_immediately"],
        "user": ["meeting_id"],
    }
