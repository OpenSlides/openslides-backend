from openslides_backend.migrations import RemoveFieldsMigration


class Migration(RemoveFieldsMigration):
    """
    This migration removes the fields committee/template_meeting_ids and meeting/template_for_committee_id.
    """

    target_migration_index = 19

    collection_fields_map = {
        "meeting": ["template_for_committee_id"],
        "committee": ["template_meeting_ids"],
    }
