from openslides_backend.migrations import RenameFieldMigration


class Migration(RenameFieldMigration):
    """
    This migration renames
    motion/sort_children_ids
    to
    motion/sort_child_ids.
    This is needed, because of a bug in motion.sort.
    """

    target_migration_index = 29

    collection = "motion"
    old_field = "sort_children_ids"
    new_field = "sort_child_ids"
