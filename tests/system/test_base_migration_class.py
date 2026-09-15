from decimal import Decimal
from typing import Any

from psycopg import sql
from psycopg.types.json import Jsonb

from openslides_backend.migrations.base import BaseMigration
from openslides_backend.migrations.migrations.mig_0101_new_vote_service.diff_mixin import (
    DiffMixin,
)
from openslides_backend.shared.filters import And, Filter, FilterOperator, Or
from tests.system.action.base import BaseActionTestCase


# TODO: it's not a test framework for the migraions and this file's content should be replaced with proper tests:
#   * Should not extend BaseActionTestCase: for the performance reasons
#   * Should use direct db-requests instead of assert_model_exists, get_model or other methods
#     that use model_registry and need it to match the database structure
#   * Should be more generic and not rely on example_data
#   * Could be reasonable to split the tests into multiple files similarly to other generic tests
#   * Should be moved to tests/system/migrations/
# These tests were added solely to test the new methods on development stage and should not be used as is in the final version of dammi.
class BaseMigrationClassTest(DiffMixin, BaseMigration, BaseActionTestCase):
    def tearDown(self) -> None:
        super().tearDown()
        self.cleanup(self.connection.cursor())

    def test_update_simple(self) -> None:
        self.load_example_data()
        self.set_models(
            {
                "projection/5": {
                    "current_projector_id": None,
                    "preview_projector_id": None,
                    "history_projector_id": 1,
                    "content_object_id": "meeting/1",
                    "stable": False,
                    "type": None,
                    "weight": 1,
                    "options": Jsonb({}),
                    "meeting_id": 1,
                },
                "poll/1": {"is_pseudoanonymized": True, "type": "analog"},
                "poll/2": {"is_pseudoanonymized": False, "type": "pseudoanonymous"},
                "poll/3": {"is_pseudoanonymized": True, "type": "cryptographic"},
                "poll/4": {"type": "named"},
                "poll/5": {"is_pseudoanonymized": False, "type": "analog"},
            }
        )
        self.data_preparation(self.connection.cursor())

        new_value: Any
        lookup_filter: Filter
        test_filter: Filter

        # -- Update all --
        new_value = "this is migrated"
        test_filter = FilterOperator("title", "=", new_value)
        matching_ids = self.datastore.get_all("poll", [], False)

        assert len(self.datastore.filter("poll", test_filter, ["id"])) == 0
        self.update_all_entries(self.connection.cursor(), "poll", "title", new_value)
        assert len(self.datastore.filter("poll", test_filter, ["id"])) != 0
        assert (
            matching_ids.keys()
            == self.datastore.filter("poll", test_filter, ["id"]).keys()
        )

        # -- Update empty --
        new_value = Decimal(7.5)
        test_filter = FilterOperator("votesvalid", "=", new_value)
        matching_ids = self.datastore.filter(
            "poll", FilterOperator("votesvalid", "=", None), ["id"]
        )

        assert len(self.datastore.filter("poll", test_filter, ["id"])) == 0
        self.update_empty_cells(
            self.connection.cursor(), "poll", "votesvalid", new_value
        )
        assert len(self.datastore.filter("poll", test_filter, ["id"])) != 0
        assert (
            matching_ids.keys()
            == self.datastore.filter("poll", test_filter, ["id"]).keys()
        )

        # -- Update matching --
        new_value = "This one is has nothing to hide"
        lookup_filter = FilterOperator("is_pseudoanonymized", "=", False)
        test_filter = FilterOperator("description", "=", new_value)
        matching_ids = self.datastore.filter("poll", lookup_filter, ["id"])

        assert len(self.datastore.filter("poll", test_filter, ["id"])) == 0
        self.update_matching_entries(
            self.connection.cursor(),
            "poll",
            "description",
            new_value,
            lookup_filter,
        )
        assert len(self.datastore.filter("poll", test_filter, ["id"])) != 0
        assert (
            matching_ids.keys()
            == self.datastore.filter("poll", test_filter, ["id"]).keys()
        )

        # -- Update matching: multi columns --
        target_field_names = ["user_id", "delegated_user_id"]
        new_values = [2, 3]
        lookup_filter = FilterOperator("option_id", "=", 1)
        test_filter = And(
            FilterOperator(target_field_names[0], "=", new_values[0]),
            FilterOperator(target_field_names[1], "=", new_values[1]),
        )
        matching_ids = self.datastore.filter("vote", lookup_filter, ["id"])

        assert len(self.datastore.filter("vote", test_filter, ["id"])) == 0
        self.update_matching_entries_multiple_columns(
            self.connection.cursor(),
            "vote",
            target_field_names,
            new_values,
            lookup_filter,
        )
        assert len(self.datastore.filter("vote", test_filter, ["id"])) != 0
        assert (
            matching_ids.keys()
            == self.datastore.filter("vote", test_filter, ["id"]).keys()
        )

        # -- Update matching: multi columns, no condition --
        target_field_names = ["max_votes_amount", "max_votes_per_option"]
        new_values = [8, 2]
        test_filter = And(
            FilterOperator(target_field_names[0], "=", new_values[0]),
            FilterOperator(target_field_names[1], "=", new_values[1]),
        )
        matching_ids = self.datastore.get_all("poll", [], False)

        assert len(self.datastore.filter("poll", test_filter, ["id"])) == 0
        self.update_matching_entries_multiple_columns(
            self.connection.cursor(),
            "poll",
            target_field_names,
            new_values,
        )
        assert len(self.datastore.filter("poll", test_filter, ["id"])) != 0
        assert (
            matching_ids.keys()
            == self.datastore.filter("poll", test_filter, ["id"]).keys()
        )

        # -- Update from map --
        self.connection.commit()
        self.connection.cursor().execute(
            "ALTER TABLE poll_m ADD COLUMN type_m varchar(256);"
        )
        self.connection.cursor().execute(
            "UPDATE poll_m SET type_m = type::varchar(256);"
        )

        self.update_from_lookup_map(
            self.connection.cursor(),
            "poll",
            "title",
            [
                (FilterOperator("type_m", "=", poll_type), True, poll_visibility)
                for poll_type, poll_visibility in {
                    "analog": "manually",
                    "named": "open",
                    "pseudoanonymous": "secret",
                    "cryptographic": "secret",
                }.items()
            ],
        )
        for poll_id, title in {
            1: "manually",
            2: "secret",
            3: "secret",
            4: "open",
            5: "manually",
        }.items():
            self.assert_model_exists(f"poll/{poll_id}", {"title": title})

        # -- Update from map multiple columns --
        filter_field_name = "name"
        target_field_names = ["recommendation_label", "state_button_label"]
        replace_map = {
            "submitted": ["yellow", "Accept"],
            "rejected": ["cyan", "Submit again"],
            "in progress": ["magenta", "Finilize"],
        }
        matching_models = {
            i: self.datastore.filter(
                "motion_state",
                FilterOperator(filter_field_name, "=", list(replace_map.keys())[i]),
                ["id"],
            ).keys()
            for i in range(3)
        }

        assert (
            len(
                self.datastore.filter(
                    "motion_state",
                    Or(
                        FilterOperator(
                            "recommendation_label",
                            "in",
                            ["yellow", "cyan", "magenta"],
                        ),
                        FilterOperator(
                            "state_button_label",
                            "in",
                            ["Accept", "Submit again", "Finilize"],
                        ),
                    ),
                    ["id"],
                )
            )
            == 0
        )

        self.update_from_lookup_map_multiple_columns(
            self.connection.cursor(),
            "motion_state",
            ["recommendation_label", "state_button_label"],
            [
                (FilterOperator("name", "=", name), False, new_values)
                for name, new_values in replace_map.items()
            ],
        )

        assert len(
            self.datastore.filter(
                "motion_state",
                Or(
                    FilterOperator(
                        "recommendation_label",
                        "in",
                        ["yellow", "cyan", "magenta"],
                    ),
                    FilterOperator(
                        "state_button_label",
                        "in",
                        ["Accept", "Submit again", "Finilize"],
                    ),
                ),
                ["id"],
            )
        ) == sum(len(ids) for ids in matching_models.values())
        for i, ids in matching_models.items():
            for id_ in ids:
                self.assert_model_exists(
                    f"motion_state/{id_}",
                    {
                        "recommendation_label": list(replace_map.values())[i][0],
                        "state_button_label": list(replace_map.values())[i][1],
                    },
                )

        # -- Update from mig table --
        self.connection.commit()
        self.connection.cursor().execute(
            "ALTER TABLE option_m ADD COLUMN temporary_column integer;"
        )
        self.connection.cursor().execute(
            "UPDATE option_m SET temporary_column = id + 7;"
        )
        self.update_from_mig_table_sql(
            self.connection.cursor(),
            "option",
            ["text"],
            [
                sql.SQL(
                    "'Result ' || ({source_table}.{source_column} * 2)::text"
                ).format(
                    source_table=sql.Identifier("option_m"),
                    source_column=sql.Identifier("temporary_column"),
                )
            ],
        )
        self.connection.commit()

        for i in range(1, 14):
            self.assert_model_exists(f"option/{i}", {"text": f"Result {(i + 7) * 2}"})

    def setup_history_entries(self) -> None:
        base_entries_data = {
            1: None,
            2: ["a"],
            3: ["b"],
            4: ["c"],
            5: ["a", "b", "c", "d"],
        }
        self.set_models(
            {
                "history_position/148": {
                    "user_id": 1,
                    "original_user_id": 1,
                },
                **{
                    f"history_entry/{i}": {
                        "entries": entries,
                        "position_id": 148,
                    }
                    for i, entries in base_entries_data.items()
                },
                **{
                    f"history_entry/{i + 10}": {
                        "entries": entries,
                        "position_id": 148,
                    }
                    for i, entries in base_entries_data.items()
                },
            }
        )

    def test_update_array_add(self) -> None:
        """Should update all entries"""
        self.setup_history_entries()
        self.update_array(
            self.connection.cursor(),
            "history_entry",
            "entries",
            add=["b"],
            dictinct=False,
        )
        for i, entries in {
            1: ["b"],
            2: ["a", "b"],
            3: ["b", "b"],
            4: ["c", "b"],
            5: ["a", "b", "c", "d", "b"],
        }.items():
            self.assert_model_exists(f"history_entry/{i}", {"entries": entries})
            self.assert_model_exists(f"history_entry/{i + 10}", {"entries": entries})

    def test_update_array_add_distinct(self) -> None:
        """Should update all entries. Resulting entries should not contain duplicates"""
        self.setup_history_entries()
        self.update_array(
            self.connection.cursor(),
            "history_entry",
            "entries",
            add=["b"],
        )
        for i, entries in {
            1: ["b"],
            2: ["a", "b"],
            3: ["b"],
            4: ["c", "b"],
            5: ["a", "b", "c", "d"],
        }.items():
            assert set(self.get_model(f"history_entry/{i}")["entries"]) == set(entries)
            assert set(self.get_model(f"history_entry/{i + 10}")["entries"]) == set(
                entries
            )

    def test_update_array_add_multi(self) -> None:
        """Should update all entries. Resulting entries should not contain duplicates"""
        self.setup_history_entries()
        self.update_array(
            self.connection.cursor(),
            "history_entry",
            "entries",
            add=["a", "b"],
        )
        for i, entries in {
            1: ["a", "b"],
            2: ["a", "b"],
            3: ["b", "a"],
            4: ["c", "a", "b"],
            5: ["a", "b", "c", "d"],
        }.items():
            assert set(self.get_model(f"history_entry/{i}")["entries"]) == set(entries)
            assert set(self.get_model(f"history_entry/{i + 10}")["entries"]) == set(
                entries
            )

    def test_update_array_remove(self) -> None:
        """Should update all entries"""
        self.setup_history_entries()
        self.update_array(
            self.connection.cursor(),
            "history_entry",
            "entries",
            remove=["b"],
        )
        for i, entries in {
            1: None,
            2: ["a"],
            3: [],
            4: ["c"],
            5: ["a", "c", "d"],
        }.items():
            self.assert_model_exists(f"history_entry/{i}", {"entries": entries})
            self.assert_model_exists(f"history_entry/{i + 10}", {"entries": entries})

    def test_update_array_remove_multi(self) -> None:
        """Should update all entries"""
        self.setup_history_entries()
        self.update_array(
            self.connection.cursor(),
            "history_entry",
            "entries",
            remove=["a", "b"],
        )
        for i, entries in {
            1: None,
            2: [],
            3: [],
            4: ["c"],
            5: ["c", "d"],
        }.items():
            self.assert_model_exists(f"history_entry/{i}", {"entries": entries})
            self.assert_model_exists(f"history_entry/{i + 10}", {"entries": entries})

    def test_update_array_replace(self) -> None:
        """Should update all entries"""
        self.setup_history_entries()
        self.update_array(
            self.connection.cursor(),
            "history_entry",
            "entries",
            replace={"b": "c"},
            dictinct=False,
        )
        for i, entries in {
            1: None,
            2: ["a"],
            3: ["c"],
            4: ["c"],
            5: ["a", "c", "c", "d"],
        }.items():
            self.assert_model_exists(f"history_entry/{i}", {"entries": entries})
            self.assert_model_exists(f"history_entry/{i + 10}", {"entries": entries})

    def test_update_array_replace_distinct(self) -> None:
        """Should update all entries. Resulting entries should not contain duplicates"""
        self.setup_history_entries()
        self.update_array(
            self.connection.cursor(),
            "history_entry",
            "entries",
            replace={"b": "c"},
        )
        for i, entries in {
            1: None,
            2: ["a"],
            3: ["c"],
            4: ["c"],
        }.items():
            self.assert_model_exists(f"history_entry/{i}", {"entries": entries})
            self.assert_model_exists(f"history_entry/{i + 10}", {"entries": entries})
        for i in [5, 15]:
            assert set(self.get_model(f"history_entry/{i}")["entries"]) == {
                "a",
                "c",
                "d",
            }

    def test_update_array_replace_multi(self) -> None:
        """Should update all entries. Resulting entries should not contain duplicates"""
        self.setup_history_entries()
        self.update_array(
            self.connection.cursor(),
            "history_entry",
            "entries",
            replace={"b": "c", "a": "e"},
        )
        for i, entries in {
            1: None,
            2: ["e"],
            3: ["c"],
            4: ["c"],
        }.items():
            self.assert_model_exists(f"history_entry/{i}", {"entries": entries})
            self.assert_model_exists(f"history_entry/{i + 10}", {"entries": entries})
        for i in [5, 15]:
            assert set(self.get_model(f"history_entry/{i}")["entries"]) == {
                "e",
                "c",
                "d",
            }

    def test_update_array_all_actions_filter(self) -> None:
        """Should update only entries that match the filter. Resulting entries should not contain duplicates"""
        self.setup_history_entries()
        self.update_array(
            self.connection.cursor(),
            "history_entry",
            "entries",
            add=["a"],
            remove=["b"],
            replace={"c": "d"},
            filter_or_condition=FilterOperator("id", "<", 10),
        )
        for i, changed_entries in {
            1: ["a"],
            2: ["a"],
            3: ["a"],
            4: ["d", "a"],
            5: ["a", "d", "a"],
        }.items():
            assert set(self.get_model(f"history_entry/{i}")["entries"]) == set(
                changed_entries
            )
        for i, unchanged_entries in {
            1: None,
            2: ["a"],
            3: ["b"],
            4: ["c"],
            5: ["a", "b", "c", "d"],
        }.items():
            self.assert_model_exists(
                f"history_entry/{i + 10}", {"entries": unchanged_entries}
            )

    def test_insert_from_other_table(self) -> None:
        self.load_example_data()
        self.data_preparation(self.connection.cursor())
        matching_polls = {
            (state, pollmethod): set(
                self.datastore.filter(
                    "poll",
                    And(
                        FilterOperator("state", "=", state),
                        FilterOperator("pollmethod", "=", pollmethod),
                        FilterOperator("type", "=", "analog"),
                    ),
                    ["id"],
                ).keys()
            )
            for state in ["created", "finished"]
            for pollmethod in ["Y", "YNA"]
        }
        values = [
            {
                "state": "finished",
                "pollmethod": "YNA",
                "text": "Poll is over, abstain was allowed",
            },
            {
                "state": "finished",
                "pollmethod": "Y",
                "text": "Poll is over, abstain was prohibited",
            },
            {
                "state": "created",
                "pollmethod": "YNA",
                "text": "New poll, abstain is allowed",
            },
            {
                "state": "created",
                "pollmethod": "Y",
                "text": "New poll, abstain is prohibited",
            },
        ]
        assert (
            len(
                self.datastore.filter(
                    "option",
                    Or(
                        FilterOperator("text", "=", values_dict["text"])
                        for values_dict in values
                    ),
                    ["id"],
                )
            )
            == 0
        )

        self.insert_from_other_table(
            self.connection.cursor(),
            target_collection="option",
            main_source_table="poll_m",
            copy_from_source_tables={
                "poll_m": {
                    "id": "poll_id",
                    "meeting_id": "meeting_id",
                }
            },
            generate_from_map=values,
            values_join_on=["state", "pollmethod"],
            filter_or_condition=FilterOperator("type", "=", "analog"),
        )
        for values_dict in values:
            assert matching_polls[
                (values_dict["state"], values_dict["pollmethod"])
            ] == {
                option["poll_id"]
                for option in self.datastore.filter(
                    "option",
                    FilterOperator("text", "=", values_dict["text"]),
                    ["poll_id"],
                ).values()
            }

    def test_insert_from_other_table_multi_source(self) -> None:
        self.load_example_data()
        mu8_user_id = self.create_user("mu8")
        self.create_meeting(72)
        self.set_models(
            {
                "meeting_user/8": {"user_id": mu8_user_id, "meeting_id": 1},
                "group/1": {"meeting_user_ids": [8]},
                "option/15": {"meeting_id": 72},
                "meeting_user/14": {"user_id": 1, "meeting_id": 72},
                "group/72": {"meeting_user_ids": [14]},
                "vote/1": {"user_id": mu8_user_id},
                "vote/10": {
                    "meeting_id": 72,
                    "user_id": 1,
                    "weight": Decimal(1),
                    "user_token": "htrfsbderag",
                    "option_id": 15,
                    "value": "Y",
                },
                "vote/11": {
                    "meeting_id": 72,
                    "user_id": 2,
                    "weight": Decimal(1),
                    "user_token": "gerggewggdf",
                    "option_id": 15,
                    "value": "Y",
                },
            }
        )

        self.connection.cursor().execute(
            "CREATE TABLE poll_ballot_user_t (id integer PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY NOT NULL, poll_id integer, acting_meeting_user_id integer);"
        )
        self.copied_tables.append('poll_ballot_user_t')
        new_ids = self.insert_from_other_table(
            self.connection.cursor(),
            target_collection="poll_ballot_user",
            main_source_table="vote_t",
            additional_souce_tables={
                "meeting_user_t": {
                    "user_id": ("vote_t", "user_id"),
                    "meeting_id": ("vote_t", "meeting_id"),
                },
                "option_t": {"id": ("vote_t", "option_id")},
            },
            copy_from_source_tables={
                "option_t": {"poll_id": "poll_id"},
                "meeting_user_t": {"id": "acting_meeting_user_id"},
            },
        )

        expected_models = [
            {"acting_meeting_user_id": 8, "poll_id": 1},  # vote/1
            {"acting_meeting_user_id": 1, "poll_id": 5},  # vote/9
            {"acting_meeting_user_id": 14, "poll_id": None},  # vote/10
        ]
        assert len(expected_models) == len(new_ids)
        for item in (
            self.connection.cursor()
            .execute("SELECT * from poll_ballot_user_t;")
            .fetchall()
        ):
            item.pop("id")
            assert item in expected_models
