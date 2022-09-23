from datastore.migrations import AddFieldsMigration


class Migration(AddFieldsMigration):
    """
    This migration adds users_enable_vote_delegations to all meetings.
    """

    target_migration_index = 35

    defaults = {"meeting": {"users_enable_vote_delegations": True}}
