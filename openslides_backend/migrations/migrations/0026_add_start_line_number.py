from openslides_backend.migrations import AddFieldsMigration


class Migration(AddFieldsMigration):
    """
    This migration adds start_line_number to all motions.
    """

    target_migration_index = 27

    defaults = {
        "motion": {
            "start_line_number": 1,
        }
    }
