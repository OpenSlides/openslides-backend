from datastore.migrations import RenameFieldMigration


class Migration(RenameFieldMigration):
    """
    This migration renames:
    user/guest
    into
    user/external.
    This is needed to have a consistent naming of the field.
    """

    target_migration_index = 68

    collection = "user"
    old_field = "guest"
    new_field = "external"
