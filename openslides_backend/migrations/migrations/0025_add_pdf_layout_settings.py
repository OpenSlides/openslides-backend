from openslides_backend.migrations import AddFieldsMigration


class Migration(AddFieldsMigration):
    """
    This migration adds pdf layout settings to all meetings.
    """

    target_migration_index = 26

    defaults = {
        "meeting": {
            "export_pdf_line_height": 1.25,
            "export_pdf_page_margin_left": 20,
            "export_pdf_page_margin_top": 25,
            "export_pdf_page_margin_right": 20,
            "export_pdf_page_margin_bottom": 20,
        }
    }
