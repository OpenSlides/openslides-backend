from openslides_backend.migrations import AddFieldsMigration


class Migration(AddFieldsMigration):
    """
    This migration adds organization genders to the one organization.
    """

    target_migration_index = 43

    defaults = {
        "organization": {
            "genders": ["male", "female", "diverse", "non-binary"],
        }
    }
