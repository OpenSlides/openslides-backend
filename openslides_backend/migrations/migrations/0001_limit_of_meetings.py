from openslides_backend.migrations import AddFieldMigration


class Migration(AddFieldMigration):
    """
    This migration adds `organization/limit_of_meetings` with a
    default of 0 (no limit) to each organization.
    """

    target_migration_index = 2

    collection = "organization"
    field = "limit_of_meetings"
    default = 0
