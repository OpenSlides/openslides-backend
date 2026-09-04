from openslides_backend.migrations.base import BaseMigration

from .diff_mixin import DiffMixin


class Migration(DiffMixin, BaseMigration):
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
    #         },
    #         "poll": {"is_pseudoanonymized": "anonymized"},
    #     },
    # )

    migration_tables = {
        "group": ["permissions"],
        "meeting": [
            "assignment_poll_default_group_ids",
            "motion_poll_default_group_ids",
            "topic_poll_default_group_ids",
            "assignment_poll_sort_poll_result_by_votes",
            "poll_sort_poll_result_by_votes",
            "assignment_poll_default_type",
            "motion_poll_default_type",
            "poll_default_type",
            "assignment_poll_default_onehundred_percent_base",
            "motion_poll_default_onehundred_percent_base",
            "poll_default_onehundred_percent_base",
            "assignment_poll_default_method",
            "poll_default_method",
        ],
        "meeting_user": ["vote_delegated_to_id"],
        "option": [
            "yes",
            "no",
            "abstain",
            "text",
            "content_object_id",
            "poll_id",
            "vote_ids",
        ],
        "poll": [
            "global_yes",
            "global_no",
            "global_abstain",
            "content_object_id",
            "global_option_id",
            "min_votes_amount",
            "max_votes_amount",
            "max_votes_per_option",
            "meeting_id",
            "onehundred_percent_base",
            "pollmethod",
            "state",
            "type",
            "voted_ids",
            "entitled_users_at_stop",
            "option_ids",
            "votescast",
            "votesinvalid",
        ],
        "poll_candidate": ["poll_candidate_list_id", "user_id", "weight"],
        "poll_candidate_list": ["option_id", "poll_candidate_ids"],
        "vote": [
            "user_id",
            "delegated_user_id",
            "user_token",
            "option_id",
            "value",
            "weight",
        ],
    }

    @staticmethod
    def find_meeting_user(user_id: int, meeting_id: int) -> int | None:
        pass
