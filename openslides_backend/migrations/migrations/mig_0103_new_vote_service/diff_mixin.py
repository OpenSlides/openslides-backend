# Code generated. DO NOT EDIT.
# Import DiffMixin to the migration file and extend it in the Migration class.


class DiffMixin:
    typed_migration_tables = {
        "group": ([], {"permissions": "varchar(256)[]"}),
        "meeting": (
            [
                "assignment_poll_default_group_ids",
                "motion_poll_default_group_ids",
                "topic_poll_default_group_ids",
                "assignment_poll_default_type",
                "motion_poll_default_type",
                "poll_default_type",
                "assignment_poll_default_method",
                "motion_poll_default_method",
                "poll_default_method",
                "assignment_poll_sort_poll_result_by_votes",
                "assignment_poll_enable_max_votes_per_option",
                "poll_sort_poll_result_by_votes",
                "poll_default_live_voting_enabled",
            ],
            {
                "assignment_poll_default_onehundred_percent_base": "varchar(256)",
                "motion_poll_default_onehundred_percent_base": "varchar(256)",
                "poll_default_onehundred_percent_base": "varchar(256)",
            },
        ),
        "meeting_user": (
            ["vote_delegated_to_id", "user_id", "meeting_id"],
            {},
        ),
        "option": (
            [
                "yes",
                "no",
                "abstain",
                "text",
                "content_object_id",
                "poll_id",
                "used_as_global_option_in_poll_id",
                "vote_ids",
                "weight",
            ],
            {},
        ),
        "poll": (
            [
                "global_yes",
                "global_no",
                "content_object_id",
                "global_option_id",
                "min_votes_amount",
                "max_votes_amount",
                "max_votes_per_option",
                "meeting_id",
                "entitled_users_at_stop",
                "votescast",
                "votesinvalid",
                "is_pseudoanonymized",
            ],
            {
                "type": "varchar(256)",
                "onehundred_percent_base": "varchar(256)",
                "pollmethod": "varchar(256)",
                "state": "varchar(256)",
            },
        ),
        "poll_candidate": (["poll_candidate_list_id", "user_id", "weight"], {}),
        "poll_candidate_list": (["option_id"], {}),
        "vote": (
            [
                "user_id",
                "delegated_user_id",
                "user_token",
                "option_id",
                "value",
                "weight",
                "meeting_id",
            ],
            {},
        ),
    }
