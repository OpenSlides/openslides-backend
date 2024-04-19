from openslides_backend.migrations import RenameFieldMigration


class Migration(RenameFieldMigration):
    """
    This migration renames
    projector_countdown/used_as_list_of_speaker_countdown_meeting_id
    to
    projector_countdown/used_as_list_of_speakers_countdown_meeting_id.
    """

    target_migration_index = 12

    collection = "projector_countdown"
    old_field = "used_as_list_of_speaker_countdown_meeting_id"
    new_field = "used_as_list_of_speakers_countdown_meeting_id"
