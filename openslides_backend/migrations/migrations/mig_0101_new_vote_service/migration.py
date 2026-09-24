from typing import Any

from psycopg import Cursor
from psycopg.rows import DictRow

from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.migrations.base import BaseMigration
from openslides_backend.migrations.patterns import Join, JoinOn
from openslides_backend.shared.filters import FilterOperator, Or

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

    def data_manipulation(
        self, curs: Cursor[DictRow], stash: dict[str, Any] | None
    ) -> None:
        self.update_all_entries(
            curs, "meeting", {"topic_poll_default_method": "selection"}
        )
        # TODO: update intermediate table
        # self.update_from_mig_table(
        #     curs,
        #     "meeting_user",
        #     ["vote_delegated_to_ids"],
        #     [
        #         sql.SQL("ARRAY[{source_column}]").format(
        #             source_column=sql.Identifier("vote_delegated_to_id")
        #         )
        #     ],
        # )
        self.update_from_mig_table(
            curs,
            "poll",
            {"anonymized": "is_pseudoanonymized"},
        )
        poll_type_to_visibility_map = {
            "analog": "manually",
            "named": "open",
            "pseudoanonymous": "secret",
            "cryptographic": "secret",
        }
        poll_onehundred_percent_bases_map: dict[str, dict[str, str | bool]] = {
            "Y": {
                "onehundred_percent_base": "no_general",
                "strike_out": False,
            },
            "N": {
                "onehundred_percent_base": "no_general",
                "strike_out": True,
            },
            "YN": {
                "onehundred_percent_base": "yes_no",
                "strike_out": False,
            },
            "YNA": {
                "onehundred_percent_base": "yes_no_abstain",
                "strike_out": False,
            },
            "valid": {
                "onehundred_percent_base": "valid",
                "strike_out": False,
            },
            "cast": {
                "onehundred_percent_base": "cast",
                "strike_out": False,
            },
            "entitled": {
                "onehundred_percent_base": "entitled",
                "strike_out": False,
            },
            "entitled_present": {
                "onehundred_percent_base": "entitled_present",
                "strike_out": False,
            },
            "disabled": {
                "onehundred_percent_base": "disabled",
                "strike_out": False,
            },
        }
        self.update_from_values_map(
            curs,
            "poll",
            [
                {"type": poll_type, "visibility": poll_visibility}
                for poll_type, poll_visibility in poll_type_to_visibility_map.items()
            ],
            ["type"],
        )
        self.update_matching_entries(
            curs,
            "poll",
            {"state": "finished", "published": True},
            FilterOperator("state", "=", "published"),
        )
        # self.update_all_entries(
        #     curs,
        #     "poll",
        #     {"allow_invalid": False, "allow_vote_split": False},
        # )
        self.update_array(
            curs,
            "group",
            "permissions",
            replace={"poll.can_manage": "agenda_item.can_manage_polls"},
        )
        self.create_meeting_poll_defaults(
            curs, poll_type_to_visibility_map, poll_onehundred_percent_bases_map
        )

    @staticmethod
    def create_meeting_poll_defaults(
        curs: Cursor[DictRow],
        poll_type_to_visibility_map: dict[str, str],
        poll_onehundred_percent_bases_map: dict[str, dict[str, str | bool]],
    ) -> None:
        # From meeting to meeting_poll_default

        fields_maps_by_poll_type = {
            "assignment": {
                "group_ids": "assignment_poll_default_group_ids",
                "sort_result_by_votes": "assignment_poll_sort_poll_result_by_votes",
                "method": "assignment_poll_default_method",
                "visibility": "assignment_poll_default_type",  # change like poll/type
                "onehundred_percent_base": "assignment_poll_default_onehundred_percent_base",  # change like poll/onehundred_percent_base
                # * For assignment polls, meeting/assignment_poll_default_method:
                # * Y
                #     * meeting_poll_default/method -> selection
                # * N
                #     * meeting_poll_default/method -> selection
                #     * meeting_poll_default/strike_out -> true
                # * YN
                #     * meeting_poll_default/method -> rating_approval
                # * YNA
                #     * meeting_poll_default/method -> rating_approval
                #     * meeting_poll_default/allow_abstain -> true
            },
            "topic": {
                "group_ids": "topic_poll_default_group_ids",
                "sort_result_by_votes": "topic_poll_sort_poll_result_by_votes",
                "method": "assignment_poll_default_method",
                "visibility": "poll_default_type",  # change like poll/type
                "onehundred_percent_base": "poll_default_onehundred_percent_base",  # change like poll/onehundred_percent_base
                # for all set: display_chart: pie
            },
            "motion": {
                "group_ids": "motion_poll_default_group_ids",
                "visibility": "motion_poll_default_type",  # change like poll/type
                "onehundred_percent_base": "motion_poll_default_onehundred_percent_base",  # change like poll/onehundred_percent_base
            },
        }

        for poll_type, fields_map in fields_maps_by_poll_type.items():
            # Values should be changed and/or used for creating meeting_poll_default:
            #     meeting/assignment_poll_default_method:
            #     Y -> selection
            #     N -> selection (+ meeting_poll_default/strike_out -> true)
            #     YN -> rating_approval
            #     YNA -> rating_approval (+ meeting_poll_default/allow_abstain -> true)
            #     meeting/motion_poll_default_method:
            #     YNA: meeting_poll_default/allow_abstain -> true
            #     meeting/poll_default_method:
            #     N: meeting_poll_default/strike_out -> true

            values_join_on = [
                fields_map["onehundred_percent_base"],
                fields_map["visibility"],
            ]
            if poll_type == "assignment":
                generate_from_map = [
                    {
                        fields_map["onehundred_percent_base"]: source_ohp_base,
                        "onehundred_percent_base": target_ohp_base_values[
                            "onehundred_percent_base"
                        ],
                        fields_map["visibility"]: type_,
                        "visibility": visibility,
                        "assignment_poll_default_method": source_method,
                        "method": target_method,
                        # "strike_out": target_method_values["strike_out"],
                        # "allow_abstain": target_method_values["allow_abstain"],
                    }
                    for source_ohp_base, target_ohp_base_values in poll_onehundred_percent_bases_map.items()
                    for type_, visibility in poll_type_to_visibility_map.items()
                    for source_method, target_method in {
                        "Y": "selection",
                        "N": "selection",
                        "YN": "rating_approval",
                        "YNA": "rating_approval",
                    }.items()
                ]
                values_join_on.append("assignment_poll_default_method")
            else:
                generate_from_map = [
                    {
                        fields_map["onehundred_percent_base"]: source_ohp_base,
                        "onehundred_percent_base": target_ohp_base_values[
                            "onehundred_percent_base"
                        ],
                        fields_map["visibility"]: type_,
                        "visibility": visibility,
                        **({"display_chart": "pie"} if poll_type == "topic" else {}),
                        "method": "approval" if poll_type == "motion" else "selection",
                    }
                    for source_ohp_base, target_ohp_base_values in poll_onehundred_percent_bases_map.items()
                    for type_, visibility in poll_type_to_visibility_map.items()
                ]
            new_ids = list(
                BaseMigration.insert_from_other_table(
                    curs,
                    target_collection="meeting_poll_default",
                    copy_from_source_tables={
                        "meeting_m": {
                            "id": "meeting_id",
                            **(
                                {
                                    fields_map[
                                        "sort_result_by_votes"
                                    ]: "sort_result_by_votes"
                                }
                                if "sort_result_by_votes" in fields_map
                                else {}
                            ),
                        }
                    },
                    values_map=generate_from_map,
                    join_values_on_columns=values_join_on,
                ).keys()
            )
            meeting_t = HelperGetNames.get_table_name("meeting_poll_default")
            poll_default_t = HelperGetNames.get_table_name("meeting_poll_default")
            BaseMigration.update_from_other_table(
                curs,
                target_collection="meeting",
                source_tables=[
                    Join(
                        poll_default_t,
                        [JoinOn("meeting_id", (meeting_t, "id"))],
                        FilterOperator("id", "in", new_ids),
                    )
                ],
                copy_from_source_tables={
                    poll_default_t: {"id": f"{poll_type}_poll_config_id"}
                },
            )
            meeting_m = HelperGetNames.get_table_name("meeting", True)
            BaseMigration.update_from_other_table(
                curs,
                target_collection="meeting_poll_default",
                source_tables=[
                    Join(
                        meeting_m,
                        [JoinOn("id", (poll_default_t, "meeting_id"))],
                        FilterOperator("id", "in", new_ids),
                    )
                ],
                copy_from_source_tables={
                    meeting_m: {f"{poll_type}_poll_default_group_ids": "group_ids"}
                },
                filter_target_table=FilterOperator("id", "in", new_ids),
            )
            BaseMigration.update_from_other_table(
                curs,
                target_collection="meeting_poll_default",
                source_tables=[
                    Join(
                        meeting_m,
                        [JoinOn("id", (poll_default_t, "meeting_id"))],
                        Or(
                            FilterOperator(column, "=", "N")
                            for column in [
                                "assignment_poll_default_method",
                                "motion_poll_default_method",
                                "poll_default_method",
                            ]
                        ),
                    )
                ],
                filter_target_table=FilterOperator("id", "in", new_ids),
                # new_values={"strike_out": True},
            )
            BaseMigration.update_from_other_table(
                curs,
                target_collection="meeting_poll_default",
                source_tables=[
                    Join(
                        meeting_m,
                        [JoinOn("id", (poll_default_t, "meeting_id"))],
                        Or(
                            FilterOperator(column, "=", "YNA")
                            for column in [
                                "assignment_poll_default_method",
                                "motion_poll_default_method",
                                "poll_default_method",
                            ]
                        ),
                    )
                ],
                filter_target_table=FilterOperator("id", "in", new_ids),
                # new_values={"allow_abstain": True},
            )
