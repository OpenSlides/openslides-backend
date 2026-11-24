from openslides_backend.migrations.base import BaseMigration


class Migration(BaseMigration):
    """
    To mitigate the effects of the changes made to the trigger naming system a while back,
    all triggers should be blanket thrown away and recreated.
    This migration does that.
    """

    ORIGIN_COLLECTIONS = [
        "action_worker",
        "agenda_item",
        "assignment",
        "assignment_candidate",
        "chat_group",
        "chat_message",
        "committee",
        "gender",
        "group",
        "history_entry",
        "history_position",
        "import_preview",
        "list_of_speakers",
        "mediafile",
        "meeting",
        "meeting_mediafile",
        "meeting_user",
        "motion",
        "motion_block",
        "motion_category",
        "motion_change_recommendation",
        "motion_comment",
        "motion_comment_section",
        "motion_editor",
        "motion_state",
        "motion_submitter",
        "motion_supporter",
        "motion_workflow",
        "motion_working_group_speaker",
        "option",
        "organization",
        "organization_tag",
        "personal_note",
        "point_of_order_category",
        "poll",
        "poll_candidate",
        "poll_candidate_list",
        "projection",
        "projector",
        "projector_countdown",
        "projector_message",
        "speaker",
        "structure_level",
        "structure_level_list_of_speakers",
        "tag",
        "theme",
        "topic",
        "user",
        "vote",
    ]

    def data_preparation(self) -> None:
        """
        Abuses the data preparation method a bit to delete all triggers.
        """
        self.execute_query(
            "SELECT event_object_table, trigger_name FROM information_schema.triggers GROUP BY event_object_table, trigger_name;"
        )
        for trigger in self.cursor.fetchall():
            eot = trigger["event_object_table"]
            tn = trigger["trigger_name"]
            self.execute_query(f"DROP TRIGGER {tn} ON {eot};\n")
