from openslides_backend.migrations import AddFieldMigration


class Migration(AddFieldMigration):
    """
    This migration adds `organization/limit_of_users` with a
    default of 0 (no limit) to each organization.
    """

    target_migration_index = 8

    collection = "organization"
    field = "limit_of_users"
    default = 0
