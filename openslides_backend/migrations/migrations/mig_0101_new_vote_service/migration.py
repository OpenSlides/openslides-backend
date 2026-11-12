from textwrap import dedent
from typing import Any

from psycopg import sql

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
from openslides_backend.shared.filters import (
    And,
    Filter,
    FilterOperator,
    Not,
    Or,
    SqlArguments,
)

from .diff_mixin import DiffMixin


class Migration(DiffMixin, BaseMigration):
    ORIGIN_COLLECTIONS = [
        "poll_ballot",
        "poll_ballot_user",
        "poll_config_approval",
        "poll_config_rating_approval",
        "poll_config_rating_score",
        "poll_config_selection",
        "poll_entitled_user",
        "poll_option",
    ]
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
        "meeting_user": ["user_id", "meeting_id", "vote_delegated_to_id"],
        "option": [
            "yes",
            "no",
            "abstain",
            "text",
            "content_object_id",
            "poll_id",
            "used_as_global_option_in_poll_id",
            "weight",
        ],
        "poll": [
            "global_yes",
            "global_no",
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
            "entitled_users_at_stop",
            "votescast",
            "votesinvalid",
            "is_pseudoanonymized",
        ],
        "poll_candidate": ["poll_candidate_list_id", "user_id", "weight"],
        "poll_candidate_list": ["option_id"],
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

    def check_prerequisites(self) -> str:
        errors = []
        # poll/state
        if message := self._check_allowed_values(
            "poll", "state", ["created", "finished", "published"], False
        ):
            errors.append(message)

        # onehundred_percent_base by poll type
        for poll_filter, allowed_bases, option_filter_query in (
            (
                None,
                [
                    "YN",
                    "YNA",
                    "valid",
                    "cast",
                    "entitled",
                    "entitled_present",
                    "disabled",
                ],
                """
                AND (
                    poll.content_object_id LIKE 'motion/%%'
                    OR (
                        poll.content_object_id LIKE 'assignment/%%'
                        AND (
                            option.content_object_id LIKE 'poll_candidate_list/%%'
                            OR (
                                option.content_object_id LIKE 'user/%%'
                                AND poll.max_votes_per_option <= 1
                                AND poll.global_yes <> TRUE
                                AND poll.global_no <> TRUE
                                AND poll.global_option_id IS NULL
                            )
                        )
                    )
                )
                """,
            ),
            (self._get_filter_by_content_object_collection("topic"), ["Y", "N"], None),
            (
                And(
                    self._get_filter_by_content_object_collection("assignment"),
                    FilterOperator("max_votes_per_option", ">", 1),
                ),
                ["Y", "valid", "cast", "entitled", "entitled_present", "disabled"],
                " AND option.content_object_id LIKE 'user/%%'",
            ),
            (
                And(
                    self._get_filter_by_content_object_collection("assignment"),
                    FilterOperator("global_option_id", "!=", None),
                    Or(
                        FilterOperator("global_yes", "=", True),
                        FilterOperator("global_no", "=", True),
                    ),
                ),
                [
                    "Y",
                    "N",
                    "valid",
                    "cast",
                    "entitled",
                    "entitled_present",
                    "disabled",
                ],
                " AND option.content_object_id LIKE 'user/%%'",
            ),
        ):
            if message := self._check_allowed_values(
                "poll",
                "onehundred_percent_base",
                allowed_bases,
                False,
                poll_filter,
                option_filter_query,
            ):
                errors.append(message)

        # pollmethod for selection polls
        if message := self._check_allowed_values(
            "poll",
            "pollmethod",
            ["Y", "N"],
            False,
            None,
            dedent("""
                AND (
                    poll.content_object_id LIKE 'topic/%%'
                    OR(
                        poll.content_object_id LIKE 'assignment/%%'
                        AND option.content_object_id LIKE 'user/%%'
                        AND (poll.global_yes = TRUE OR poll.global_no = TRUE)
                        AND (poll.global_option_id IS NOT NULL)
                    )
                )
                """),
        ):
            errors.append(message)

        # Correct option/content_object_id
        self.execute_query("""
            SELECT o.id
            FROM poll_t p
            JOIN option_t o ON o.poll_id = p.id
            WHERE p.content_object_id LIKE 'motion/%' AND o.content_object_id NOT LIKE 'motion/%';
            """)
        if entries := self.cursor.fetchall():
            errors.append(
                f"Invalid option/content_object_id: collection must be 'motion' if collection of poll/content_object_id is 'motion'.\n"
                f"Affected option ids: {[entry['id'] for entry in entries]}."
            )

        self.execute_query("""
            SELECT o.id
            FROM option_t o
            JOIN poll_t p ON o.poll_id = p.id
            WHERE p.content_object_id LIKE 'assignment/%' AND o.content_object_id LIKE 'motion/%';
            """)
        if entries := self.cursor.fetchall():
            errors.append(
                f"Invalid option/content_object_id: collection must be 'user' or 'poll_candidate_list' if collection of poll/content_object_id is 'assignment'.\n"
                f"Affected option ids: {[entry['id'] for entry in entries]}."
            )

        # option/text for topic polls
        self.execute_query("""
            SELECT o.id
            FROM poll_t p
            JOIN option_t o ON o.poll_id = p.id
            WHERE p.content_object_id LIKE 'topic/%' AND o.text IS NULL OR o.text = '';
            """)
        if entries := self.cursor.fetchall():
            errors.append(
                f"Invalid option/text: can not be empty if collection of poll/content_object_id is 'topic'.\n"
                f"Affected option ids: {[entry['id'] for entry in entries]}."
            )

        # Global option exists if global_yes or global_no is True
        self.execute_query(
            "SELECT id FROM poll WHERE (global_yes = TRUE OR global_no = TRUE) AND (global_option_id IS NULL);"
        )
        if entries := self.cursor.fetchall():
            errors.append(
                "poll/global_yes or poll/global_no can be set to 'True' only if poll/global_option_id is defined.\n"
                f"Affected poll ids: {[entry['id'] for entry in entries]}."
            )

        # Valid option/used_as_global_option_in_poll_id
        self.execute_query("""
            SELECT id
            FROM option o
            WHERE o.used_as_global_option_in_poll_id IS NOT NULL AND o.used_as_global_option_in_poll_id != o.poll_id;
            """)
        if entries := self.cursor.fetchall():
            errors.append(
                "option/used_as_global_option_in_poll_id must be equal to option/poll_id or Null.\n"
                f"Affected option ids: {[entry['id'] for entry in entries]}."
            )

        # Global option is the only selected option
        self.execute_query("""
            SELECT array_agg(v.id) AS ids
            FROM vote_t v
            JOIN option o ON o.id = v.option_id
            GROUP BY o.poll_id, v.user_token
            HAVING COUNT(v.id) > 1 AND BOOL_OR(o.used_as_global_option_in_poll_id IS NOT NULL);
            """)
        if entries := self.cursor.fetchall():
            errors.append(
                "When global option is selected, it must be the only selected option in a split vote.\n"
                f"Affected vote ids groups: {[entry['ids'] for entry in entries]}."
            )

        # One option and vote per single-option poll
        self.execute_query("""
            SELECT DISTINCT(p.id)
            FROM poll p
            JOIN option_t o ON o.poll_id = p.id
            WHERE (
                (
                    p.content_object_id LIKE 'motion/%'
                    OR (
                        p.content_object_id LIKE 'assignment/%'
                        AND o.content_object_id LIKE 'poll_candidate_list/%'
                    )
                )
                AND CARDINALITY(p.option_ids) > 1
            );
            """)
        if entries := self.cursor.fetchall():
            errors.append(
                "Only one option should exist when poll/content_object_id collection is 'motion' or poll/content_object_id collection is 'assignment' and option/content_object_id collection is 'poll_candidate_list'.\n"
                f"Affected poll ids: {[entry['id'] for entry in entries]}."
            )

        self.execute_query("""
            SELECT array_agg(v.id) AS ids
            FROM vote_t v
            JOIN option_t o ON o.id = v.option_id
            JOIN poll_t p ON p.id = o.poll_id
            WHERE (
                p.content_object_id LIKE 'motion/%'
                OR (
                    p.content_object_id LIKE 'assignment/%'
                    AND o.content_object_id LIKE 'poll_candidate_list/%'
                )
            )
            GROUP BY o.poll_id, v.user_token
            HAVING COUNT(v.id) > 1;
            """)
        if entries := self.cursor.fetchall():
            errors.append(
                "Only one vote per user should exist when poll/content_object_id collection is 'motion' or poll/content_object_id collection is 'assignment' and option/content_object_id collection is 'poll_candidate_list'.\n"
                f"Affected vote ids groups: {[entry['ids'] for entry in entries]}."
            )

        # vote/value
        if message := self._check_allowed_values(
            "vote", "value", ["Y", "N", "A"], False
        ):
            errors.append(message)

        # Same weight per user_token + poll_id for selection and rating-approval polls
        self.execute_query("""
            SELECT array_agg(v.id) AS ids
            FROM vote_t v
            JOIN option_t o ON o.id = v.option_id
            JOIN poll_t p ON p.id = o.poll_id
            WHERE (
                p.content_object_id LIKE 'topic/%'
                OR(
                    p.content_object_id LIKE 'assignment/%'
                    AND o.content_object_id LIKE 'user/%'
                    AND p.max_votes_per_option <= 1
                )
            )
            GROUP BY o.poll_id, v.user_token
            HAVING COUNT(DISTINCT(v.weight)) > 1;
            """)
        if entries := self.cursor.fetchall():
            errors.append(
                "All parts of a split vote must have the same weight.\n"
                f"Affected vote ids groups: {[entry['ids'] for entry in entries]}."
            )

        # Fields that get merged for multi-option polls have same values
        for column in ["user_id", "delegated_user_id"]:
            self.execute_query(sql.SQL("""
                    SELECT array_agg(v.id) AS ids
                    FROM vote_t v
                    JOIN option_t o ON o.id = v.option_id
                    JOIN poll_t p ON p.id = o.poll_id
                    WHERE (
                        p.content_object_id LIKE 'topic/%'
                        OR (
                            p.content_object_id LIKE 'assignment/%'
                            AND o.content_object_id LIKE 'user/%'
                        )
                    )
                    GROUP BY o.poll_id, v.user_token
                    HAVING COUNT(DISTINCT(v.{column})) > 1;
                    """).format(column=sql.Identifier(column)))
            if entries := self.cursor.fetchall():
                errors.append(
                    f"vote/{column} must be the same for all the votes with the same poll_id + user_token. \n"
                    f"Affected vote ids groups: {[entry['ids'] for entry in entries]}."
                )

        if errors:
            errors = [
                "Some entries contain forbidden values and can not be migrated:"
            ] + errors
            return "\n\n".join(errors)
        return ""

    def data_manipulation(self, stash: dict[str, Any] | None) -> None:
        self.insert_from_other_table(
            "nm_meeting_user_vote_delegated_to_ids_meeting_user_t",
            InsertFromTables(
                copy_data=[
                    TableDataSource(
                        Join(
                            TableRef("meeting_user", True),
                            [],
                            FilterOperator("vote_delegated_to_id", "!=", None),
                        ),
                        [
                            ColumnDataSource(
                                "vote_delegated_to_id", "vote_delegated_to_id"
                            ),
                            ColumnDataSource("vote_delegations_from_id", "id"),
                        ],
                    )
                ],
            ),
            return_fields=["vote_delegations_from_id", "vote_delegations_from_id"],
        )
        poll_type_to_visibility_map = {
            "analog": "manually",
            "named": "open",
            "pseudoanonymous": "secret",
            "cryptographic": "secret",
        }
        poll_onehundred_percent_bases_map = {
            "Y": "no_general",
            "N": "no_general",
            "YN": "yes_no",
            "YNA": "yes_no_abstain",
        }

        self.create_meeting_poll_settings(
            poll_type_to_visibility_map, poll_onehundred_percent_bases_map
        )
        self.migrate_polls(
            poll_type_to_visibility_map, poll_onehundred_percent_bases_map
        )

    def create_meeting_poll_settings(
        self,
        poll_type_to_visibility_map: dict[str, str],
        poll_onehundred_percent_bases_map: dict[str, str],
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
        meeting_m = TableRef("meeting", True)
        base_values_source = [
            {"origin": origin, "target": target}
            for origin, target in poll_onehundred_percent_bases_map.items()
        ]
        for poll_type, default_base in (
            ("assignment", "valid"),
            ("topic", "valid"),
            ("motion", "yes_no_abstain"),
        ):
            field_name = fields_maps_by_poll_type[poll_type]["onehundred_percent_base"]
            self.update_from_values_map(
                meeting_m,
                ValuesSource(
                    [*base_values_source, {"origin": None, "target": default_base}],
                    ["origin"],
                    {"origin": field_name, "target": field_name},
                ),
            )
        methods_map = {
            "assignment": {
                "map": (
                    ("Y", "selection.yes"),
                    ("N", "selection.no"),
                    ("YN", "rating_approval.yes_no"),
                    ("YNA", "rating_approval.yes_no_abstain"),
                    ("yna", "rating_approval.yes_no_abstain"),
                ),
                "default": "selection.yes",
            },
            "motion": {
                "map": (
                    ("YN", "approval.yes_no"),
                    ("YNA", "approval.yes_no_abstain"),
                ),
                "default": "approval.yes_no_abstain",
            },
        }

        for poll_type, fields_map in fields_maps_by_poll_type.items():
            method_sql = (
                sql.SQL("'selection.yes'::enum_meeting_poll_setting_method")
                if poll_type == "topic"
                else sql.SQL("CASE {case} END").format(
                    case=sql.SQL(" ").join(
                        [
                            sql.SQL(
                                "WHEN {column} = {origin} THEN {target}::enum_meeting_poll_setting_method"
                            ).format(
                                column=sql.Identifier(
                                    fields_maps_by_poll_type[poll_type]["method"]
                                ),
                                origin=sql.Literal(origin),
                                target=sql.Literal(target),
                            )
                            for origin, target in methods_map[poll_type]["map"]
                        ]
                        + [
                            sql.SQL(
                                "ELSE {default}::enum_meeting_poll_setting_method"
                            ).format(
                                default=sql.Literal(methods_map[poll_type]["default"])
                            )
                        ]
                    )
                )
            )
            new_ids = [
                entry["id"]
                for entry in self.insert_from_other_table(
                    "meeting_poll_setting",
                    copy_from_source_tables=InsertFromTables(
                        copy_data=[
                            TableDataSource(
                                Join(TableRef("meeting", True), []),
                                [
                                    ColumnDataSource("meeting_id", "id"),
                                    ColumnDataSource(
                                        "allow_live_voting",
                                        transformed_column_value=sql.Literal(True),
                                    ),
                                    ColumnDataSource(
                                        "method", transformed_column_value=method_sql
                                    ),
                                    ColumnDataSource(
                                        "onehundred_percent_base",
                                        fields_map["onehundred_percent_base"],
                                    ),
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
                                fields_map["visibility"]: type_,
                                "visibility": visibility,
                            }
                            for type_, visibility in poll_type_to_visibility_map.items()
                        ],
                        join_on_columns=[fields_map["visibility"]],
                    ),
                )
            ]
            filter_new_meeting_poll_settings = FilterOperator("id", "in", new_ids)
            self.update_from_other_table(
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
            meeting_poll_setting_t = TableRef("meeting_poll_setting", False)
            group_ids_field = fields_map["group_ids"]
            self.insert_from_other_table(
                "nm_group_uimpsi_meeting_poll_setting_t",
                InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            Join(
                                meeting_poll_setting_t,
                                [],
                                filter_new_meeting_poll_settings,
                            ),
                            [ColumnDataSource("meeting_poll_setting_id", "id")],
                        ),
                        TableDataSource(
                            Join(
                                TableRef("meeting", True),
                                [JoinOn("id", meeting_poll_setting_t, "meeting_id")],
                                FilterOperator(group_ids_field, "!=", None),
                            ),
                            [
                                ColumnDataSource(
                                    "group_id",
                                    transformed_column_value=sql.SQL(
                                        "unnest({group_ids_column})"
                                    ).format(
                                        group_ids_column=sql.Identifier(
                                            "meeting_m", group_ids_field
                                        )
                                    ),
                                )
                            ],
                        ),
                    ],
                ),
                return_fields=["group_id", "meeting_poll_setting_id"],
            )

    def migrate_polls(
        self,
        poll_type_to_visibility_map: dict[str, str],
        poll_onehundred_percent_bases_map: dict[str, str],
    ) -> None:
        self.update_from_values_map(
            TableRef("vote", True),
            ValuesSource(
                [
                    {"origin_value": "Y", "target_value": "yes"},
                    {"origin_value": "N", "target_value": "no"},
                    {"origin_value": "A", "target_value": "abstain"},
                ],
                ["origin_value"],
                {"origin_value": "value", "target_value": "value"},
            ),
        )

        poll_t = TableRef("poll", False)
        poll_m = TableRef("poll", True)
        self.update_from_values_map(
            poll_t,
            ValuesSource(
                [
                    {"type": poll_type, "visibility": poll_visibility}
                    for poll_type, poll_visibility in poll_type_to_visibility_map.items()
                ],
                ["type"],
            ),
            join_values_to_mig_table=True,
        )
        self.update_from_values_map(
            poll_m,
            ValuesSource(
                [
                    {"source_base": source_base, "target_base": target_base}
                    for source_base, target_base in poll_onehundred_percent_bases_map.items()
                ],
                ["source_base"],
                {
                    "source_base": "onehundred_percent_base",
                    "target_base": "onehundred_percent_base",
                },
            ),
        )
        self.update_matching_entries(
            poll_t,
            {"state": "finished", "published": True},
            FilterOperator("state", "=", "published"),
        )
        self.update_all_entries(
            poll_t,
            {"allow_invalid": False, "allow_vote_split": False},
        )

        self.execute_query("ALTER TABLE poll_m ADD COLUMN config_type varchar(32);")
        self.execute_query("""
            UPDATE poll_m p
            SET config_type =
                CASE
                    WHEN p.content_object_id LIKE 'motion/%'
                        THEN 'approval'
                    WHEN p.content_object_id LIKE 'topic/%'
                        THEN 'selection'
                    ELSE
                        CASE
                            WHEN EXISTS (
                                SELECT 1
                                FROM option_m o
                                WHERE o.poll_id = p.id
                                AND o.content_object_id LIKE 'poll_candidate_list/%'
                            )
                                THEN 'approval'
                            ELSE
                                CASE
                                    WHEN p.max_votes_per_option > 1
                                        THEN 'rating_score'
                                    ELSE
                                        CASE
                                            WHEN (p.global_yes = TRUE OR p.global_no = TRUE) AND p.global_option_id IS NOT NULL
                                                THEN 'selection'
                                            ELSE 'rating_approval'
                                        END
                                END
                        END
                END;
                """)

        self.execute_query("""
            ALTER TABLE vote_m
                ADD COLUMN poll_id integer,
                ADD COLUMN link_user_to_ballot boolean;
        """)
        vote_m = TableRef("vote", True)
        option_m = TableRef("option", True)
        self.update_from_other_table(
            UpdateFromTables(
                target_table=vote_m,
                copy_data=[
                    TableDataSource(
                        Join(option_m, [JoinOn("id", vote_m, "option_id")]),
                        [ColumnDataSource("poll_id", "poll_id")],
                    ),
                    TableDataSource(
                        Join(poll_m, [JoinOn("id", option_m, "poll_id")]),
                        [
                            ColumnDataSource(
                                "link_user_to_ballot",
                                transformed_column_value=sql.SQL(
                                    "(poll_m.type != 'analog' AND poll_m.is_pseudoanonymized <> TRUE)"
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        )

        self.execute_query("""
            INSERT INTO poll_entitled_user_t (
                poll_id,
                meeting_user_id,
                present
            )
            SELECT
                poll_m.id,
                meeting_user_t.id,
                COALESCE((e->>'present')::boolean, FALSE)
            FROM poll_m
            CROSS JOIN LATERAL jsonb_array_elements(poll_m.entitled_users_at_stop) AS e
            JOIN meeting_user_t
                ON meeting_user_t.meeting_id = poll_m.meeting_id
                AND meeting_user_t.user_id = (e->>'user_id')::integer
            RETURNING id;
            """)

        self.migrate_multiple_options_polls()
        self.migrate_single_option_polls()

    def migrate_single_option_polls(self) -> None:
        poll_m = TableRef("poll", True)
        option_m = TableRef("option", True)
        vote_m = TableRef("vote", True)

        migrated_polls = [
            entry["id"]
            for entry in self.insert_from_other_table(
                "poll_config_approval",
                copy_from_source_tables=InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(
                                poll_m,
                                [],
                                FilterOperator("config_type", "=", "approval"),
                            ),
                            value_definition=[
                                ColumnDataSource("id", "id"),
                                ColumnDataSource(
                                    "onehundred_percent_base", "onehundred_percent_base"
                                ),
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
                    ]
                ),
            )
        ]
        self._assign_configs_to_polls("poll_config_approval", migrated_polls)
        self._generate_poll_result(
            option_m,
            migrated_polls,
            self._get_aggregated_poll_result_part("option_m", ["yes", "no"]),
        )
        new_ballot_user_ids = [
            entry["id"]
            for entry in self.insert_from_other_table(
                "poll_ballot_user",
                InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            Join(
                                poll_m,
                                [],
                                And(
                                    FilterOperator("id", "in", migrated_polls),
                                    FilterOperator("type", "!=", "analog"),
                                ),
                            ),
                            [],
                        ),
                        TableDataSource(
                            source_table=Join(
                                vote_m,
                                [JoinOn("poll_id", poll_m, "id")],
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
            )
        ]
        self._create_poll_ballots(vote_m, migrated_polls, new_ballot_user_ids)

        # Create options only for assignment polls
        poll_candidate_m = TableRef("poll_candidate", True)
        poll_candidate_list_m = TableRef("poll_candidate_list", True)
        self.insert_from_other_table(
            "poll_option",
            InsertFromTables(
                copy_data=[
                    TableDataSource(
                        source_table=Join(
                            poll_m,
                            [],
                            And(
                                FilterOperator("config_type", "=", "approval"),
                                self._get_filter_by_content_object_collection(
                                    "assignment"
                                ),
                            ),
                        ),
                    ),
                    TableDataSource(
                        source_table=Join(
                            option_m,
                            [JoinOn("poll_id", poll_m, "id")],
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
                                transformed_column_value=self._build_fqid_from_id_column(
                                    "user",
                                    "user_id",
                                    poll_candidate_m.table_name,
                                ),
                            ),
                        ],
                    ),
                ]
            ),
        )

    def migrate_multiple_options_polls(
        self,
    ) -> None:
        poll_m = TableRef("poll", True)
        option_m = TableRef("option", True)

        topic_polls = self.migrate_topic_polls()
        assignment_selection_polls = self.migrate_assignment_selection_polls()
        assignment_rating_score_polls = self.migrate_assignment_rating_score_polls()
        assignment_rating_approval_polls = (
            self.migrate_assignment_rating_approval_polls()
        )

        all_polls = (
            topic_polls
            + assignment_selection_polls
            + assignment_rating_score_polls
            + assignment_rating_approval_polls
        )

        for poll_config_type, poll_ids in (
            ("selection", topic_polls + assignment_selection_polls),
            ("rating_score", assignment_rating_score_polls),
            ("rating_approval", assignment_rating_approval_polls),
        ):
            self._assign_configs_to_polls(f"poll_config_{poll_config_type}", poll_ids)
        for option_content_field, poll_ids in (
            ("text", topic_polls),
            (
                "content_object_id",
                assignment_selection_polls
                + assignment_rating_score_polls
                + assignment_rating_approval_polls,
            ),
        ):
            polls_filter = FilterOperator("poll_id", "in", poll_ids)
            self.insert_from_other_table(
                "poll_option",
                InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(
                                option_m,
                                [],
                                And(
                                    polls_filter,
                                    FilterOperator(
                                        "used_as_global_option_in_poll_id",
                                        "=",
                                        None,
                                    ),
                                ),
                            ),
                            value_definition=[
                                ColumnDataSource(field, field)
                                for field in [
                                    "id",
                                    "poll_id",
                                    "weight",
                                    option_content_field,
                                ]
                            ],
                        ),
                    ]
                ),
            )
        self.execute_query(
            sql.SQL("""
                CREATE TEMP TABLE poll_result_source_m AS
                SELECT
                    o.poll_id,
                    SUM(COALESCE(o.abstain, 0)) AS abstain,
                    SUM(COALESCE(o.yes, 0) + COALESCE(o.no, 0)) FILTER (
                        WHERE o.used_as_global_option_in_poll_id = o.poll_id
                    ) AS nota,
                    jsonb_object_agg(
                        CASE
                            WHEN p.content_object_id LIKE 'topic/%%'
                            THEN o.text
                            ELSE o.id::text
                        END,
                        CASE
                            WHEN p.pollmethod = 'N'
                            THEN o.no::text
                            ELSE o.yes::text
                        END
                    ) FILTER (
                        WHERE o.used_as_global_option_in_poll_id IS NULL
                    ) AS options_json
                FROM option_m o
                JOIN poll_m p ON p.id = o.poll_id
                WHERE o.poll_id = ANY(%s)
                GROUP BY o.poll_id;
            """),
            [topic_polls + assignment_selection_polls + assignment_rating_score_polls],
        )
        self.execute_query(
            sql.SQL("""
                INSERT INTO poll_result_source_m (
                    poll_id,
                    options_json
                )
                SELECT
                    o.poll_id,
                    jsonb_object_agg(
                        o.id::text,
                        jsonb_strip_nulls(
                            jsonb_build_object(
                                'yes', NULLIF(o.yes, 0)::text,
                                'no', NULLIF(o.no, 0)::text,
                                'abstain', NULLIF(o.abstain, 0)::text
                            )
                        )
                    ) AS options_json
                FROM option_m o
                WHERE o.poll_id = ANY(%s)
                GROUP BY o.poll_id;
            """),
            [assignment_rating_approval_polls],
        )
        poll_result_source_m = TableRef("poll_result_source", True)
        self._generate_poll_result(
            poll_result_source_m,
            all_polls,
            sql.SQL("options_json || {poll_json}").format(
                poll_json=self._get_aggregated_poll_result_part(
                    poll_result_source_m.table_name, ["nota"]
                )
            ),
        )
        self.execute_query(
            sql.SQL("""
                CREATE TEMP TABLE aggregated_votes_m AS
                SELECT
                    MIN(v.id) AS id,
                    MIN(v.poll_id) AS poll_id,
                    BOOL_AND(v.link_user_to_ballot) AS link_user_to_ballot,
                    CASE
                        WHEN BOOL_OR(p.config_type = 'rating_score')
                            THEN SUM(v.weight)
                        ELSE MIN(v.weight)
                    END AS weight,
                    MIN(mur.id) AS represented_meeting_user_id,
                    MIN(mua.id) AS acting_meeting_user_id,
                    CASE
                        WHEN BOOL_OR(p.config_type = 'rating_approval')
                            THEN jsonb_object_agg(
                                v.option_id::text,
                                v.value
                            )::text
                        WHEN BOOL_OR(o.used_as_global_option_in_poll_id = o.poll_id)
                            THEN 'nota'
                        WHEN BOOL_OR(p.config_type = 'rating_score')
                            THEN jsonb_object_agg(
                                o.id::text,
                                TRUNC(v.weight)::integer
                            )::text
                        ELSE array_to_string(array_agg(v.option_id), ',')
                    END AS value
                FROM vote_m v
                JOIN option_m o ON o.id = v.option_id
                JOIN poll_m p ON p.id = v.poll_id
                LEFT JOIN meeting_user mur
                    ON mur.meeting_id = p.meeting_id
                    AND mur.user_id = v.user_id
                LEFT JOIN meeting_user mua
                    ON mua.meeting_id = p.meeting_id
                    AND mua.user_id = v.delegated_user_id
                WHERE v.poll_id = ANY(%s) AND p.type != 'analog'
                GROUP BY v.poll_id, v.user_token;
            """),
            [all_polls],
        )
        new_ballot_user_ids = [
            entry["id"]
            for entry in self.insert_from_other_table(
                "poll_ballot_user",
                InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            Join(
                                poll_m,
                                [],
                                And(
                                    FilterOperator("id", "in", all_polls),
                                    FilterOperator("type", "!=", "analog"),
                                ),
                            ),
                            [],
                        ),
                        TableDataSource(
                            source_table=Join(
                                TableRef("aggregated_votes", True),
                                [JoinOn("poll_id", poll_m, "id")],
                            ),
                            value_definition=[
                                ColumnDataSource(field, field)
                                for field in [
                                    "id",
                                    "poll_id",
                                    "acting_meeting_user_id",
                                    "represented_meeting_user_id",
                                ]
                            ],
                        ),
                    ]
                ),
            )
        ]
        self._create_poll_ballots(
            TableRef("aggregated_votes", True), all_polls, new_ballot_user_ids
        )
        self.adjust_id_sequence("poll_option")

    def migrate_topic_polls(self) -> list[int]:
        return [
            entry["id"]
            for entry in self.insert_from_other_table(
                "poll_config_selection",
                copy_from_source_tables=InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(
                                TableRef("poll", True),
                                [],
                                self._get_filter_by_content_object_collection("topic"),
                            ),
                            value_definition=[
                                ColumnDataSource("id", "id"),
                                ColumnDataSource(
                                    "min_options_amount", "min_votes_amount"
                                ),
                                ColumnDataSource(
                                    "max_options_amount", "max_votes_amount"
                                ),
                                ColumnDataSource(
                                    "strike_out",
                                    transformed_column_value=sql.SQL(
                                        "(poll_m.pollmethod = 'N')"
                                    ),
                                ),
                                ColumnDataSource(
                                    "allow_nota",
                                    transformed_column_value=sql.SQL(
                                        "(poll_m.global_option_id IS NOT NULL)"
                                    ),
                                ),
                                ColumnDataSource(
                                    "onehundred_percent_base",
                                    transformed_column_value=sql.Literal("no_general"),
                                ),
                                ColumnDataSource(
                                    "display_chart",
                                    transformed_column_value=sql.Literal("pie"),
                                ),
                            ],
                        ),
                    ]
                ),
            )
        ]

    def migrate_assignment_rating_score_polls(self) -> list[int]:
        return [
            entry["id"]
            for entry in self.insert_from_other_table(
                "poll_config_rating_score",
                copy_from_source_tables=InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(
                                TableRef("poll", True),
                                [],
                                FilterOperator("config_type", "=", "rating_score"),
                            ),
                            value_definition=[
                                ColumnDataSource("id", "id"),
                                ColumnDataSource(
                                    "onehundred_percent_base", "onehundred_percent_base"
                                ),
                                ColumnDataSource(
                                    "max_votes_per_option", "max_votes_per_option"
                                ),
                                ColumnDataSource("max_vote_sum", "min_votes_amount"),
                                ColumnDataSource("min_vote_sum", "max_votes_amount"),
                            ],
                        ),
                    ]
                ),
            )
        ]

    def migrate_assignment_selection_polls(self) -> list[int]:
        return [
            entry["id"]
            for entry in self.insert_from_other_table(
                "poll_config_selection",
                copy_from_source_tables=InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(
                                TableRef("poll", True),
                                [],
                                And(
                                    self._get_filter_by_content_object_collection(
                                        "assignment"
                                    ),
                                    FilterOperator("config_type", "=", "selection"),
                                ),
                            ),
                            value_definition=[
                                ColumnDataSource("id", "id"),
                                ColumnDataSource(
                                    "min_options_amount", "min_votes_amount"
                                ),
                                ColumnDataSource(
                                    "max_options_amount", "max_votes_amount"
                                ),
                                ColumnDataSource(
                                    "strike_out",
                                    transformed_column_value=sql.SQL(
                                        "(poll_m.pollmethod = 'N')"
                                    ),
                                ),
                                ColumnDataSource(
                                    "onehundred_percent_base", "onehundred_percent_base"
                                ),
                                ColumnDataSource(
                                    "allow_nota",
                                    transformed_column_value=sql.Literal(True),
                                ),
                            ],
                        ),
                    ]
                ),
            )
        ]

    def migrate_assignment_rating_approval_polls(self) -> list[int]:
        return [
            entry["id"]
            for entry in self.insert_from_other_table(
                "poll_config_rating_approval",
                copy_from_source_tables=InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(
                                TableRef("poll", True),
                                [],
                                FilterOperator("config_type", "=", "rating_approval"),
                            ),
                            value_definition=[
                                ColumnDataSource("id", "id"),
                                ColumnDataSource(
                                    "onehundred_percent_base", "onehundred_percent_base"
                                ),
                                ColumnDataSource(
                                    "min_options_amount", "min_votes_amount"
                                ),
                                ColumnDataSource(
                                    "max_options_amount", "max_votes_amount"
                                ),
                                ColumnDataSource(
                                    "allow_abstain",
                                    transformed_column_value=sql.SQL(
                                        "(poll_m.pollmethod = 'YNA')"
                                    ),
                                ),
                            ],
                        ),
                    ]
                ),
            )
        ]

    # -- Helpers specific for this migration --
    def _check_allowed_values(
        self,
        collection: str,
        column: str,
        allowed_values: list[Any],
        allow_null: bool,
        filter_operator: Filter | None = None,
        option_filter_query: str | None = None,
    ) -> str | None:
        arguments: SqlArguments = []

        filter_: Filter = Not(FilterOperator(column, "in", allowed_values))
        if allow_null:
            filter_ = And(filter_, FilterOperator(column, "!=", None))
        if filter_operator:
            filter_ = And(filter_operator, filter_)

        query = sql.SQL(
            "SELECT {table}.id FROM {table}{join_option} WHERE {poll_filter}{filter_query};"
        ).format(
            table=sql.Identifier(collection),
            join_option=sql.SQL(
                " LEFT JOIN option ON option.poll_id = poll.id"
                if option_filter_query
                else ""
            ),
            poll_filter=self._build_filter_query(
                filter_, arguments, collection, filter_condition_table_alias=collection
            ),
            filter_query=sql.SQL(
                option_filter_query.replace("    ", "").replace("\n", " ")
                if option_filter_query
                else ""
            ),
        )
        self.execute_query(query, [*arguments])
        if entries := self.cursor.fetchall():
            ids = [entry["id"] for entry in entries]
            found_invalid_values = [
                entry[column]
                for entry in self.cursor.execute(
                    sql.SQL(
                        "SELECT DISTINCT {column} FROM {table} WHERE id = ANY({ids});"
                    ).format(
                        column=sql.Identifier(column),
                        table=sql.Identifier(collection),
                        ids=sql.Placeholder(),
                    ),
                    [ids],
                ).fetchall()
            ]
            return (
                f"Invalid values in {collection}/{column} for ids: {ids}.\n"
                f"Value must be one of: {allowed_values}.\n"
                f"Found invalid values: {found_invalid_values}.\n"
            )
        return None

    def _assign_configs_to_polls(
        self, poll_config_collection: str, poll_ids: list[int]
    ) -> None:
        self.update_matching_entries(
            TableRef("poll", False),
            {
                "config_id": self._build_fqid_from_id_column(
                    poll_config_collection, "id"
                )
            },
            FilterOperator("id", "in", poll_ids),
        )

    @staticmethod
    def _get_aggregated_poll_result_part(
        source_table: str, extra_source_columns: list[str]
    ) -> sql.Composed:
        json_source = {
            **{
                column: sql.SQL("NULLIF({source_column}::text, '0')").format(
                    source_column=sql.Identifier(source_table, column)
                )
                for column in [*extra_source_columns, "abstain"]
            },
            "entitled_users": sql.Identifier("cte_entitled_users", "all"),
            "entitled_users_present": sql.Identifier("cte_entitled_users", "present"),
            "invalid": sql.SQL(
                "CASE "
                "WHEN poll_t.visibility = 'manually' "
                "THEN NULLIF(TRUNC(poll_m.votesinvalid)::integer, 0) "
                "ELSE NULL "
                "END"
            ),
            "total_ballots": sql.SQL("TRUNC(poll_m.votescast)::integer"),
        }
        return sql.SQL("jsonb_strip_nulls(jsonb_build_object({json_source}))").format(
            json_source=sql.SQL(",").join(
                sql.SQL(",").join([k, v]) for k, v in json_source.items()
            ),
        )

    def _generate_poll_result(
        self,
        source_table: TableRef,
        poll_ids: list[int],
        value: sql.Composed,
    ) -> None:
        poll_t = TableRef("poll", False)
        poll_m = TableRef("poll", True)
        self.update_from_other_table(
            copy_from_source_tables=UpdateFromTables(
                target_table=poll_t,
                copy_data=[
                    TableDataSource(Join(poll_m, [JoinOn("id", poll_t, "id")])),
                    TableDataSource(
                        Join(
                            TableRef("cte_entitled_users", is_view=True),
                            [JoinOn("poll_id", poll_m, "id")],
                        )
                    ),
                    TableDataSource(
                        Join(
                            source_table,
                            [JoinOn("poll_id", poll_m, "id")],
                        ),
                        value_definition=[
                            ColumnDataSource(
                                "result",
                                transformed_column_value=value,
                            )
                        ],
                    ),
                ],
            ),
            filter_target_table=And(
                FilterOperator("id", "in", poll_ids),
                FilterOperator("state", "=", "finished"),
            ),
            common_table_expression=sql.SQL("""
                WITH cte_entitled_users AS (
                    SELECT
                        poll_id,
                        COUNT(*) AS all,
                        COUNT(*) FILTER(WHERE present = TRUE) AS present
                    FROM poll_entitled_user_t
                    GROUP BY poll_id
                )
            """),
        )

    def _create_poll_ballots(
        self,
        source_table: TableRef,
        poll_ids: list[int],
        ballot_user_ids: list[int],
    ) -> None:
        public_ballot_ids = [
            ballot["poll_ballot_user_id"]
            for ballot in self.insert_from_other_table(
                "poll_ballot",
                InsertFromTables(
                    copy_data=[
                        TableDataSource(
                            source_table=Join(
                                source_table,
                                [],
                                And(
                                    FilterOperator("id", "in", ballot_user_ids),
                                    FilterOperator("link_user_to_ballot", "=", True),
                                ),
                            ),
                            value_definition=[
                                ColumnDataSource("weight", "weight"),
                                ColumnDataSource("poll_id", "poll_id"),
                                ColumnDataSource("value", "value"),
                                ColumnDataSource("poll_ballot_user_id", "id"),
                            ],
                        ),
                    ]
                ),
                return_fields=["poll_ballot_user_id"],
            )
        ]
        self.insert_from_other_table(
            "poll_ballot",
            InsertFromTables(
                copy_data=[
                    TableDataSource(
                        source_table=Join(
                            source_table,
                            [],
                            And(
                                FilterOperator("poll_id", "in", poll_ids),
                                Not(FilterOperator("id", "in", public_ballot_ids)),
                            ),
                        ),
                        value_definition=[
                            ColumnDataSource("weight", "weight"),
                            ColumnDataSource("poll_id", "poll_id"),
                            ColumnDataSource("value", "value"),
                        ],
                    ),
                ]
            ),
        )

    @staticmethod
    def _get_filter_by_content_object_collection(
        collection: str,
    ) -> Filter:
        return FilterOperator("content_object_id", "%=", f"{collection}/%")

    @staticmethod
    def _build_fqid_from_id_column(
        collection: str,
        id_column_name: str,
        id_table_table: str | None = None,
    ) -> sql.Composed:
        return sql.SQL("{collection} || '/' || ({id_column})::text").format(
            collection=sql.Literal(collection),
            id_column=(
                sql.Identifier(id_table_table, id_column_name)
                if id_table_table
                else sql.Identifier(id_column_name)
            ),
        )
