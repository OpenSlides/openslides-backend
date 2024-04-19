from openslides_backend.migrations import RemoveFieldsMigration

# Extracted from openslides_backend/action/actions/agenda_item/agenda_creation.py
agenda_creation_properties = [
    "agenda_create",
    "agenda_type",
    "agenda_parent_id",
    "agenda_comment",
    "agenda_duration",
    "agenda_weight",
]

# Collections which can possibly have agenda items
collections = [
    "assignment",
    "motion",
    "motion_block",
    "topic",
]


class Migration(RemoveFieldsMigration):
    """
    This migration all agenda_creation properties from multiple collections.
    """

    target_migration_index = 34
    collection_fields_map = {
        collection: agenda_creation_properties for collection in collections
    }
