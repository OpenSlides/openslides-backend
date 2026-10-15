from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from meta.dev.src.alter_schema_helper import AlterSchemaHelper
from openslides_backend.migrations.base import BaseMigration
from openslides_backend.migrations.patterns import (
    ColumnDataSource,
    InsertFromTables,
    Join,
    JoinOn,
    TableDataSource,
    TableRef,
    UpdateFromTables,
    ValuesSource,
)
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.filters import And, Filter, FilterOperator, Not

from .diff_mixin import DiffMixin


class Migration(DiffMixin, BaseMigration):
    renames = (
        {},
        {
            "projector": {
                "used_as_default_projector_for_poll_in_meeting_id": "used_as_default_projector_for_topic_poll_in_meeting_id"
            },
            "meeting": {
                "motion_poll_projection_name_order_first": "poll_projection_name_order_first",
                "motion_poll_projection_max_columns": "poll_projection_max_columns",
            },
            "poll": {"is_pseudoanonymized": "anonymized"},
        },
    )

    migration_tables = {
        "meeting": [
            "assignment_poll_default_group_ids",
            "motion_poll_default_group_ids",
            "topic_poll_default_group_ids",
            "assignment_poll_default_method",
            "motion_poll_default_method",
            "poll_default_method",
            "assignment_poll_default_type",
            "motion_poll_default_type",
            "poll_default_type",
            "assignment_poll_default_onehundred_percent_base",
            "motion_poll_default_onehundred_percent_base",
            "poll_default_onehundred_percent_base",
            "assignment_poll_sort_poll_result_by_votes",
            "assignment_poll_enable_max_votes_per_option",
            "poll_sort_poll_result_by_votes",
            "poll_default_live_voting_enabled",
        ],
        "meeting_user": ["vote_delegated_to_id", "user_id", "meeting_id"],
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
            "meeting_id",
        ],
    }

    @staticmethod
    def validate_data_compatibility(curs: Cursor[DictRow]) -> None:
        errors = []
        for field_name, allowed_pollmethods in {
            "assignment_poll_default_method": ["Y", "N", "YN", "YNA"],
            "motion_poll_default_method": ["YN", "YNA"],
            "poll_default_method": ["N"],
        }.items():
            if entries := curs.execute(
                sql.SQL(
                    "SELECT id from meeting_m where {column} <> ALL({values});"
                ).format(column=sql.Identifier(field_name), values=sql.Placeholder()),
                [allowed_pollmethods],
            ).fetchall():
                errors.append(
                    f"Detected invalid values in field {field_name} for meetings: {[entry['id'] for entry in entries]}. "
                    f"Allowed values are: {allowed_pollmethods}."
                )
        if errors:
            raise BadCodingException("\n".join(errors))

    def data_manipulation(
        self, curs: Cursor[DictRow], stash: dict[str, Any] | None
    ) -> None:
        self.validate_data_compatibility(curs)
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

        self.create_meeting_poll_settings(
            curs, poll_type_to_visibility_map, poll_onehundred_percent_bases_map
        )
        self.migrate_polls(
            curs, poll_type_to_visibility_map, poll_onehundred_percent_bases_map
        )

    def create_meeting_poll_settings(
        self,
        curs: Cursor[DictRow],
        poll_type_to_visibility_map: dict[str, str],
        poll_onehundred_percent_bases_map: dict[str, dict[str, str | bool]],
    ) -> None:
        fields_maps_by_poll_type = {
            "assignment": {
                "group_ids": "assignment_poll_default_group_ids",
                "method": "assignment_poll_default_method",
                "visibility": "assignment_poll_default_type",
                "onehundred_percent_base": "assignment_poll_default_onehundred_percent_base",
                "sort_result_by_votes": "assignment_poll_sort_poll_result_by_votes",
                "enable_cumulative_voting": "assignment_poll_enable_max_votes_per_option",
            },
            "topic": {
                "group_ids": "topic_poll_default_group_ids",
                "method": "poll_default_method",
                "visibility": "poll_default_type",
                "onehundred_percent_base": "poll_default_onehundred_percent_base",
                "sort_result_by_votes": "poll_sort_poll_result_by_votes",
            },
            "motion": {
                "group_ids": "motion_poll_default_group_ids",
                "method": "motion_poll_default_method",
                "visibility": "motion_poll_default_type",
                "onehundred_percent_base": "motion_poll_default_onehundred_percent_base",
            },
        }

        for poll_type, fields_map in fields_maps_by_poll_type.items():
            new_ids = list(
                self.insert_from_other_table(
                    curs,
                    "meeting_poll_setting",
                    copy_from_source_tables=InsertFromTables(
                        copy_data=[
                            TableDataSource(
                                Join(TableRef("meeting", True), []),
                                [
                                    ColumnDataSource("meeting_id", "id"),
                                    ColumnDataSource(
                                        "enable_live_voting",
                                        "poll_default_live_voting_enabled",
                                    ),
                                    *[
                                        ColumnDataSource(
                                            target_field_name,
                                            fields_map[target_field_name],
                                        )
                                        for target_field_name in [
                                            "sort_result_by_votes",
                                            "enable_cumulative_voting",
                                        ]
                                        if target_field_name in fields_map
                                    ],
                                ],
                            )
                        ]
                    ),
                    values_source=ValuesSource(
                        rows=[
                            {
                                fields_map["onehundred_percent_base"]: source_ohp_base,
                                "onehundred_percent_base": target_ohp_base_values[
                                    "onehundred_percent_base"
                                ],
                                fields_map["visibility"]: type_,
                                "visibility": visibility,
                                fields_map["method"]: source_method,
                                "method": target_method,
                            }
                            for source_ohp_base, target_ohp_base_values in poll_onehundred_percent_bases_map.items()
                            for type_, visibility in poll_type_to_visibility_map.items()
                            for source_method, target_method in {
                                "Y": "selection.yes",
                                "N": "selection.no",
                                "YN": "rating_approval.yes_no",
                                "YNA": "rating_approval.yes_no_abstain",
                            }.items()
                        ],
                        join_on_columns=[
                            fields_map["onehundred_percent_base"],
                            fields_map["visibility"],
                            fields_map["method"],
                        ],
                    ),
                ).keys()
            )
            filter_new_meeting_poll_settings = FilterOperator("id", "in", new_ids)
            self.update_from_other_table(
                curs,
                UpdateFromTables(
                    target_table=TableRef("meeting", False),
                    copy_data=[
                        TableDataSource(
                            Join(
                                TableRef("meeting_poll_setting", False),
                                [
                                    JoinOn(
                                        "meeting_id",
                                        TableRef("meeting", False),
                                        "id",
                                    )
                                ],
                                filter_new_meeting_poll_settings,
                            ),
                            [ColumnDataSource(f"{poll_type}_poll_config_id", "id")],
                        )
                    ],
                ),
            )
            # self.update_from_other_table(
            #     curs,
            #     UpdateFromTables(
            #         target_table=TableRef("meeting_poll_setting", False),
            #         copy_data=[
            #             TableDataSource(
            #                 Join(
            #                     TableRef("meeting", True),
            #                     [
            #                         JoinOn(
            #                             "id",
            #                             TableRef("meeting_poll_setting", False),
            #                             "meeting_id",
            #                         )
            #                     ],
            #                     filter_new_meeting_poll_settings,
            #                 ),
            #                 [
            #                     ColumnDataSource(
            #                         "group_ids",
            #                         f"{poll_type}_poll_default_group_ids",
            #                     )
            #                 ],
            #             )
            #         ],
            #     ),
            #     filter_target_table=FilterOperator("id", "in", new_ids),
            # )
        self.update_all_entries(
            curs, "meeting_poll_setting", {"allow_live_voting": True}
        )

    def migrate_polls(
        self,
        curs: Cursor[DictRow],
        poll_type_to_visibility_map: dict[str, str],
        poll_onehundred_percent_bases_map: dict[str, dict[str, str | bool]],
    ) -> None:
        self.rename_column_in_mig_table(
            curs, "poll", "onehundred_percent_base", "onehundred_percent_base_m"
        )
        self.rename_column_in_mig_table(curs, "vote", "value", "value_m")
        curs.execute("ALTER TABLE vote_m ADD COLUMN poll_id integer;")
        curs.execute(
            "UPDATE vote_m SET poll_id = option_m.poll_id FROM option_m WHERE option_m.id = vote_m.option_id;"
        )
        vote_value_map = {"Y": "yes", "N": "no", "A": "abstain"}

        self.update_from_values_map(
            curs,
            "poll",
            ValuesSource(
                [
                    {"type": poll_type, "visibility": poll_visibility}
                    for poll_type, poll_visibility in poll_type_to_visibility_map.items()
                ],
                ["type"],
            ),
            join_values_to_mig_table=True,
        )
        self.update_matching_entries(
            curs,
            "poll",
            {"state": "finished", "published": True},
            FilterOperator("state", "=", "published"),
        )
        self.update_all_entries(
            curs,
            "poll",
            {"allow_invalid": False, "allow_vote_split": False},
        )

        self.migrate_motion_polls(
            curs, poll_onehundred_percent_bases_map, vote_value_map
        )
        self.migrate_assignment_polls_with_candidate_list(
            curs, poll_onehundred_percent_bases_map, vote_value_map
        )

        curs.execute(sql.SQL("""
                INSERT INTO poll_entitled_user_t (
                    poll_id,
                    meeting_user_id,
                    present
                )
                SELECT
                    poll_m.id,
                    meeting_user_t.id,
                    (e->>'present')::boolean
                FROM poll_m
                CROSS JOIN LATERAL jsonb_array_elements(poll_m.entitled_users_at_stop) AS e
                JOIN meeting_user_t
                    ON meeting_user_t.meeting_id = poll_m.meeting_id
                    AND meeting_user_t.user_id = (e->>'user_id')::integer
                RETURNING id;
                """))

    def migrate_motion_polls(
        self,
        curs: Cursor[DictRow],
        poll_onehundred_percent_bases_map: dict[str, dict[str, str | bool]],
        vote_value_map: dict[str, str],
    ) -> None:
        filter_ = self.get_filter_by_content_object_collection("motion")
        poll_t = TableRef("poll", False)
        poll_m = TableRef("poll", True)
        new_poll_configs = list(
            self.insert_from_other_table(
                curs,
                "poll_config_approval",
                copy_from_source_tables=InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(poll_m, [], filter_),
                            value_definition=[
                                ColumnDataSource("id", "id"),
                                ColumnDataSource(
                                    "allow_abstain",
                                    transformed_column_value=sql.SQL(
                                        "({source_column} = 'YNA')"
                                    ).format(
                                        source_column=sql.Identifier(
                                            poll_m.table_name, "pollmethod"
                                        ),
                                    ),
                                ),
                            ],
                        )
                    ]
                ),
                values_source=ValuesSource(
                    rows=[
                        {
                            "onehundred_percent_base_m": onehundred_percent_base_m,
                            "onehundred_percent_base": onehundred_percent_base[
                                "onehundred_percent_base"
                            ],
                        }
                        for onehundred_percent_base_m, onehundred_percent_base in poll_onehundred_percent_bases_map.items()
                    ],
                    join_on_columns=["onehundred_percent_base_m"],
                ),
            ).keys()
        )
        filter_polls = FilterOperator("id", "in", new_poll_configs)
        self.update_from_other_table(
            curs,
            UpdateFromTables(
                target_table=poll_t,
                copy_data=[
                    TableDataSource(
                        Join(
                            TableRef("poll_config_approval", False),
                            [JoinOn("id", poll_t, "id")],
                            filter_polls,
                        ),
                        [
                            ColumnDataSource(
                                "config_id",
                                transformed_column_value=sql.SQL(
                                    "'poll_config_approval/' || ({id_column})::text"
                                ).format(
                                    id_column=sql.Identifier(
                                        TableRef(
                                            "poll_config_approval", False
                                        ).table_name,
                                        "id",
                                    )
                                ),
                            )
                        ],
                    )
                ],
            ),
        )
        option_m = TableRef("option", True)
        self.update_from_other_table(
            curs,
            copy_from_source_tables=UpdateFromTables(
                target_table=poll_t,
                copy_data=[
                    TableDataSource(Join(poll_m, [JoinOn("id", poll_t, "id")])),
                    TableDataSource(
                        source_table=Join(
                            option_m,
                            [JoinOn("poll_id", poll_m, "id")],
                        ),
                        value_definition=[
                            ColumnDataSource(
                                "result",
                                transformed_column_value=sql.SQL(
                                    "jsonb_strip_nulls(jsonb_object(ARRAY[{columns}], ARRAY[{values}]))"
                                ).format(
                                    columns=sql.SQL(",").join(
                                        [
                                            "yes",
                                            "no",
                                            "abstain",
                                            "invalid",
                                            "total_ballots",
                                        ]
                                    ),
                                    values=sql.SQL(", ").join(
                                        [
                                            sql.SQL(
                                                "NULLIF({source_column}::text, '0')"
                                            ).format(
                                                source_column=sql.Identifier(
                                                    option_m.table_name, "yes"
                                                )
                                            ),
                                            sql.SQL(
                                                "NULLIF({source_column}::text, '0')"
                                            ).format(
                                                source_column=sql.Identifier(
                                                    option_m.table_name, "no"
                                                )
                                            ),
                                            sql.SQL(
                                                "NULLIF({source_column}::text, '0')"
                                            ).format(
                                                source_column=sql.Identifier(
                                                    option_m.table_name, "abstain"
                                                )
                                            ),
                                            sql.SQL(
                                                "CASE "
                                                "WHEN poll_t.visibility = 'manually' "
                                                "THEN NULLIF(TRUNC({source_column})::text, '0') "
                                                "ELSE NULL "
                                                "END"
                                            ).format(
                                                source_column=sql.Identifier(
                                                    poll_m.table_name, "votesinvalid"
                                                ),
                                            ),
                                            sql.SQL("TRUNC(poll_m.votescast)::text"),
                                        ]
                                    ),
                                ),
                            )
                        ],
                    ),
                ],
            ),
            filter_target_table=filter_polls,
        )
        vote_m = TableRef("vote", True)
        new_ballot_user_ids = list(
            self.insert_from_other_table(
                curs,
                "poll_ballot_user",
                InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            Join(
                                poll_t,
                                [],
                                And(
                                    FilterOperator("id", "in", new_poll_configs),
                                    FilterOperator("visibility", "!=", "manually"),
                                    FilterOperator("state", "=", "finished"),
                                ),
                            ),
                            [],
                        ),
                        TableDataSource(
                            source_table=Join(
                                vote_m,
                                [JoinOn("poll_id", poll_t, "id")],
                            ),
                            value_definition=[
                                ColumnDataSource("id", "id"),
                                ColumnDataSource("poll_id", "poll_id"),
                            ],
                        ),
                        TableDataSource(
                            Join(
                                TableRef("meeting_user", False),
                                [
                                    JoinOn("user_id", vote_m, "user_id"),
                                    JoinOn("meeting_id", vote_m, "meeting_id"),
                                ],
                            ),
                            [ColumnDataSource("represented_meeting_user_id", "id")],
                        ),
                        TableDataSource(
                            Join(
                                TableRef("meeting_user", True),
                                [
                                    JoinOn("user_id", vote_m, "delegated_user_id"),
                                    JoinOn("meeting_id", vote_m, "meeting_id"),
                                ],
                            ),
                            [ColumnDataSource("acting_meeting_user_id", "id")],
                        ),
                    ]
                ),
            ).keys()
        )
        public_ballot_ids = [
            ballot["poll_ballot_user_id"]
            for ballot in self.insert_from_other_table(
                curs,
                "poll_ballot",
                InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(
                                vote_m,
                                [],
                                FilterOperator("id", "in", new_ballot_user_ids),
                            ),
                            value_definition=[
                                ColumnDataSource("weight", "weight"),
                                ColumnDataSource("poll_id", "poll_id"),
                                ColumnDataSource("poll_ballot_user_id", "id"),
                            ],
                        ),
                        TableDataSource(
                            Join(
                                poll_t,
                                [JoinOn("id", vote_m, "poll_id")],
                                FilterOperator("anonymized", "!=", True),
                            ),
                        ),
                    ]
                ),
                values_source=ValuesSource(
                    rows=[
                        {"value_m": value_m, "value": value}
                        for value_m, value in vote_value_map.items()
                    ],
                    join_on_columns=["value_m"],
                ),
                return_fields=["poll_ballot_user_id"],
            ).values()
        ]
        self.insert_from_other_table(
            curs,
            "poll_ballot",
            InsertFromTables(
                copy_data=[
                    TableDataSource(
                        source_table=Join(
                            vote_m,
                            [],
                            Not(FilterOperator("id", "in", public_ballot_ids)),
                        ),
                        value_definition=[
                            ColumnDataSource("weight", "weight"),
                            ColumnDataSource("poll_id", "poll_id"),
                        ],
                    ),
                    TableDataSource(
                        source_table=Join(
                            poll_t,
                            [JoinOn("id", vote_m, "poll_id")],
                            FilterOperator("id", "in", new_poll_configs),
                        ),
                    ),
                ]
            ),
            values_source=ValuesSource(
                rows=[
                    {"value_m": value_m, "value": value}
                    for value_m, value in vote_value_map.items()
                ],
                join_on_columns=["value_m"],
            ),
        )

    def migrate_assignment_polls_with_candidate_list(
        self,
        curs: Cursor[DictRow],
        poll_onehundred_percent_bases_map: dict[str, dict[str, str | bool]],
        vote_value_map: dict[str, str],
    ) -> None:
        # All diffs - relative to motion
        # Diff 1: filter_
        filter_ = self.get_filter_by_content_object_collection("assignment")
        poll_t = TableRef("poll", False)
        poll_m = TableRef("poll", True)
        new_poll_configs = list(
            self.insert_from_other_table(
                curs,
                "poll_config_approval",
                copy_from_source_tables=InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(poll_m, [], filter_),
                            value_definition=[
                                ColumnDataSource("id", "id"),
                                ColumnDataSource(
                                    "allow_abstain",
                                    transformed_column_value=sql.SQL(
                                        "({source_column} = 'YNA')"
                                    ).format(
                                        source_column=sql.Identifier(
                                            poll_m.table_name, "pollmethod"
                                        ),
                                    ),
                                ),
                            ],
                        ),
                        # Diff 2: whole TableDataSource
                        TableDataSource(
                            Join(
                                TableRef("option", True),
                                [JoinOn("poll_id", poll_m, "id")],
                                self.get_filter_by_content_object_collection(
                                    "poll_candidate_list"
                                ),
                            )
                        ),
                    ]
                ),
                values_source=ValuesSource(
                    rows=[
                        {
                            "onehundred_percent_base_m": onehundred_percent_base_m,
                            "onehundred_percent_base": onehundred_percent_base[
                                "onehundred_percent_base"
                            ],
                        }
                        for onehundred_percent_base_m, onehundred_percent_base in poll_onehundred_percent_bases_map.items()
                    ],
                    join_on_columns=["onehundred_percent_base_m"],
                ),
            ).keys()
        )
        filter_polls = FilterOperator("id", "in", new_poll_configs)
        self.update_from_other_table(
            curs,
            UpdateFromTables(
                target_table=poll_t,
                copy_data=[
                    TableDataSource(
                        Join(
                            TableRef("poll_config_approval", False),
                            [JoinOn("id", poll_t, "id")],
                            filter_polls,
                        ),
                        [
                            ColumnDataSource(
                                "config_id",
                                transformed_column_value=sql.SQL(
                                    "'poll_config_approval/' || ({id_column})::text"
                                ).format(
                                    id_column=sql.Identifier(
                                        TableRef(
                                            "poll_config_approval", False
                                        ).table_name,
                                        "id",
                                    )
                                ),
                            )
                        ],
                    )
                ],
            ),
        )
        option_m = TableRef("option", True)
        self.update_from_other_table(
            curs,
            copy_from_source_tables=UpdateFromTables(
                target_table=poll_t,
                copy_data=[
                    TableDataSource(Join(poll_m, [JoinOn("id", poll_t, "id")])),
                    TableDataSource(
                        source_table=Join(
                            option_m,
                            [JoinOn("poll_id", poll_m, "id")],
                        ),
                        value_definition=[
                            ColumnDataSource(
                                "result",
                                transformed_column_value=sql.SQL(
                                    "jsonb_strip_nulls(jsonb_object(ARRAY[{columns}], ARRAY[{values}]))"
                                ).format(
                                    columns=sql.SQL(",").join(
                                        [
                                            "yes",
                                            "no",
                                            "abstain",
                                            "invalid",
                                            "total_ballots",
                                        ]
                                    ),
                                    values=sql.SQL(", ").join(
                                        [
                                            sql.SQL(
                                                "NULLIF({source_column}::text, '0')"
                                            ).format(
                                                source_column=sql.Identifier(
                                                    option_m.table_name, "yes"
                                                )
                                            ),
                                            sql.SQL(
                                                "NULLIF({source_column}::text, '0')"
                                            ).format(
                                                source_column=sql.Identifier(
                                                    option_m.table_name, "no"
                                                )
                                            ),
                                            sql.SQL(
                                                "NULLIF({source_column}::text, '0')"
                                            ).format(
                                                source_column=sql.Identifier(
                                                    option_m.table_name, "abstain"
                                                )
                                            ),
                                            sql.SQL(
                                                "CASE "
                                                "WHEN poll_t.visibility = 'manually' "
                                                "THEN NULLIF(TRUNC({source_column})::text, '0') "
                                                "ELSE NULL "
                                                "END"
                                            ).format(
                                                source_column=sql.Identifier(
                                                    poll_m.table_name, "votesinvalid"
                                                ),
                                            ),
                                            sql.SQL("TRUNC(poll_m.votescast)::text"),
                                        ]
                                    ),
                                ),
                            )
                        ],
                    ),
                ],
            ),
            filter_target_table=filter_polls,
        )
        vote_m = TableRef("vote", True)
        new_ballot_user_ids = list(
            self.insert_from_other_table(
                curs,
                "poll_ballot_user",
                InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            Join(
                                poll_t,
                                [],
                                And(
                                    FilterOperator("id", "in", new_poll_configs),
                                    FilterOperator("visibility", "!=", "manually"),
                                    FilterOperator("state", "=", "finished"),
                                ),
                            ),
                            [],
                        ),
                        TableDataSource(
                            source_table=Join(
                                vote_m,
                                [JoinOn("poll_id", poll_t, "id")],
                            ),
                            value_definition=[
                                ColumnDataSource("id", "id"),
                                ColumnDataSource("poll_id", "poll_id"),
                            ],
                        ),
                        TableDataSource(
                            Join(
                                TableRef("meeting_user", False),
                                [
                                    JoinOn("user_id", vote_m, "user_id"),
                                    JoinOn("meeting_id", vote_m, "meeting_id"),
                                ],
                            ),
                            [ColumnDataSource("represented_meeting_user_id", "id")],
                        ),
                        TableDataSource(
                            Join(
                                TableRef("meeting_user", True),
                                [
                                    JoinOn("user_id", vote_m, "delegated_user_id"),
                                    JoinOn("meeting_id", vote_m, "meeting_id"),
                                ],
                            ),
                            [ColumnDataSource("acting_meeting_user_id", "id")],
                        ),
                    ]
                ),
            ).keys()
        )
        public_ballot_ids = [
            ballot["poll_ballot_user_id"]
            for ballot in self.insert_from_other_table(
                curs,
                "poll_ballot",
                InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(
                                vote_m,
                                [],
                                FilterOperator("id", "in", new_ballot_user_ids),
                            ),
                            value_definition=[
                                ColumnDataSource("weight", "weight"),
                                ColumnDataSource("poll_id", "poll_id"),
                                ColumnDataSource("poll_ballot_user_id", "id"),
                            ],
                        ),
                        TableDataSource(
                            Join(
                                poll_t,
                                [JoinOn("id", vote_m, "poll_id")],
                                FilterOperator("anonymized", "!=", True),
                            ),
                        ),
                    ]
                ),
                values_source=ValuesSource(
                    rows=[
                        {"value_m": value_m, "value": value}
                        for value_m, value in vote_value_map.items()
                    ],
                    join_on_columns=["value_m"],
                ),
                return_fields=["poll_ballot_user_id"],
            ).values()
        ]
        self.insert_from_other_table(
            curs,
            "poll_ballot",
            InsertFromTables(
                copy_data=[
                    TableDataSource(
                        source_table=Join(
                            vote_m,
                            [],
                            Not(FilterOperator("id", "in", public_ballot_ids)),
                        ),
                        value_definition=[
                            ColumnDataSource("weight", "weight"),
                            ColumnDataSource("poll_id", "poll_id"),
                        ],
                    ),
                    TableDataSource(
                        source_table=Join(
                            poll_t,
                            [JoinOn("id", vote_m, "poll_id")],
                            FilterOperator("id", "in", new_poll_configs),
                        ),
                    ),
                ]
            ),
            values_source=ValuesSource(
                rows=[
                    {"value_m": value_m, "value": value}
                    for value_m, value in vote_value_map.items()
                ],
                join_on_columns=["value_m"],
            ),
        )
        # Diff 3: extra options
        poll_candidate_m = TableRef("poll_candidate", True)
        poll_candidate_list_m = TableRef("poll_candidate_list", True)
        self.insert_from_other_table(
            curs,
            "poll_option",
            InsertFromTables(
                copy_data=[
                    TableDataSource(
                        source_table=Join(
                            option_m,
                            [],
                            FilterOperator("id", "in", new_poll_configs),
                        ),
                        value_definition=[ColumnDataSource("poll_id", "poll_id")],
                    ),
                    TableDataSource(
                        source_table=Join(
                            poll_candidate_list_m,
                            [JoinOn("option_id", option_m, "id")],
                        ),
                    ),
                    TableDataSource(
                        source_table=Join(
                            poll_candidate_m,
                            [
                                JoinOn(
                                    "poll_candidate_list_id",
                                    poll_candidate_list_m,
                                    "id",
                                )
                            ],
                        ),
                        value_definition=[
                            ColumnDataSource("weight", "weight"),
                            ColumnDataSource(
                                "content_object_id",
                                transformed_column_value=sql.SQL(
                                    "'user/' || ({id_column})::text"
                                ).format(
                                    id_column=sql.Identifier(
                                        poll_candidate_m.table_name,
                                        "user_id",
                                    )
                                ),
                            ),
                        ],
                    ),
                ]
            ),
        )

    # -- Helpers specific for this migration --
    @staticmethod
    def get_filter_by_content_object_collection(
        collection: str,
    ) -> Filter:
        return FilterOperator("content_object_id", "%=", f"{collection}/%")

    @staticmethod
    def rename_column_in_mig_table(
        curs: Cursor[DictRow],
        collection: str,
        column_name_old: str,
        column_name_new: str,
    ) -> None:
        curs.execute(
            AlterSchemaHelper.get_rename_table_column(
                TableRef(collection, True).table_name, column_name_old, column_name_new
            )
        )
