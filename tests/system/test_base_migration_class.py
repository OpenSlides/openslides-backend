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
