from openslides_backend.migrations import RemoveFieldsMigration


class Migration(RemoveFieldsMigration):
    """
    This migration removes the fields url_name and users_pdf_url from meeting.
    """

    target_migration_index = 17

    collection_fields_map = {"meeting": ["url_name", "users_pdf_url"]}
