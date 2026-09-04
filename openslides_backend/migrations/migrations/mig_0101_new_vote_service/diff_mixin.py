# Code generated. DO NOT EDIT.
# Import DiffMixin to the migration file and extend it in the Migration class.


class DiffMixin:
    typed_migration_tables = {
        "group": ([], {"permissions": "varchar(256)[]"}),
        "meeting": (
            [
                "assignment_poll_sort_poll_result_by_votes",
                "poll_sort_poll_result_by_votes",
                "assignment_poll_default_type",
                "motion_poll_default_type",
                "poll_default_type",
                "assignment_poll_default_method",
                "poll_default_method",
            ],
            {
                "assignment_poll_default_group_ids": "integer[]",
                "motion_poll_default_group_ids": "integer[]",
                "topic_poll_default_group_ids": "integer[]",
                "assignment_poll_default_onehundred_percent_base": "varchar(256)",
                "motion_poll_default_onehundred_percent_base": "varchar(256)",
                "poll_default_onehundred_percent_base": "varchar(256)",
            },
        ),
        "meeting_user": ([], {"vote_delegated_to_id": "integer"}),
        "option": (
            ["yes", "no", "abstain", "text"],
            {
                "content_object_id": "varchar(256)",
                "poll_id": "integer",
                "vote_ids": "integer[]",
            },
        ),
        "poll": (
            [
                "global_yes",
                "global_no",
                "global_abstain",
                "min_votes_amount",
                "max_votes_amount",
                "max_votes_per_option",
                "type",
                "entitled_users_at_stop",
                "votescast",
                "votesinvalid",
            ],
            {
                "content_object_id": "varchar(256)",
                "global_option_id": "integer",
                "meeting_id": "integer",
                "onehundred_percent_base": "varchar(256)",
                "pollmethod": "varchar(256)",
                "state": "varchar(256)",
                "voted_ids": "integer[]",
                "option_ids": "integer[]",
            },
        ),
        "poll_candidate": (
            ["weight"],
            {"poll_candidate_list_id": "integer", "user_id": "integer"},
        ),
        "poll_candidate_list": (
            [],
            {"option_id": "integer", "poll_candidate_ids": "integer[]"},
        ),
        "vote": (
            ["user_token", "value", "weight"],
            {
                "user_id": "integer",
                "delegated_user_id": "integer",
                "option_id": "integer",
            },
        ),
    }
