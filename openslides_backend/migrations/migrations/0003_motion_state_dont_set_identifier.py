from openslides_backend.migrations import AddFieldMigration


class Migration(AddFieldMigration):
    """
    This migration adds `motion_state/dont_set_identifier` with a
    default of False to each motion_state.
    """

    target_migration_index = 4

    collection = "motion_state"
    field = "dont_set_identifier"
    default = False
