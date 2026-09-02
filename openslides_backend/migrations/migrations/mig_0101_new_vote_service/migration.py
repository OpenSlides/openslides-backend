from openslides_backend.migrations.base import BaseMigration


class Migration(BaseMigration):
    # renames = (
    #     {},
    #     {
    #         "projector": {
    #             "used_as_default_projector_for_poll_in_meeting_id": "used_as_default_projector_for_topic_poll_in_meeting_id"
    #         },
    #         "meeting": {
    #             "default_projector_poll_ids": "default_projector_topic_poll_ids",
    #             "motion_poll_projection_name_order_first": "poll_projection_name_order_first",
    #             "motion_poll_projection_max_columns": "poll_projection_max_columns",
    #             "assignment_poll_enable_max_votes_per_option": "poll_enable_max_votes_per_option",
    #             "poll_default_method": "topic_poll_default_method",
    #         },
    #         "poll": {"is_pseudoanonymized": "anonymized"},
    #     },
    # )

    @staticmethod
    def find_meeting_user(user_id: int, meeting_id: int) -> int | None:
        pass
