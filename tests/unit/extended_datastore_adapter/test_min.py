from openslides_backend.shared.filters import FilterOperator

from .base import BaseTestExtendedDatastoreAdapter


class TestMinExtendedDatastoreAdapter(BaseTestExtendedDatastoreAdapter):
    db_method_name = "min"

    def setUp(self) -> None:
        super().setUp()
        self.db_method_return_value = 42
        self.filter_return_value = {}

    def test_only_db(self) -> None:
        self.set_additional_models({"test/1": {"a": 2, "weight": 1}})
        result = self.adapter.min(
            "test",
            FilterOperator("a", "=", 2),
            "weight",
            use_changed_models=False,
        )
        assert result == 42
        self.db_method_mock.assert_called()
        self.filter_mock.assert_not_called()
        # TODO See TODO in tests/unit/extended_datastore_adapter/base.py
        # If that's done reactivate line below and other such lines in this file?
        # self.add_filter_mock.assert_not_called()

    def test_use_changed_models(self) -> None:
        self.set_additional_models({"test/1": {"a": 2, "weight": 100}})
        result = self.adapter.min(
            "test",
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result == 100
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()

    def test_use_changed_models_none(self) -> None:
        self.set_additional_models({"test/1": {"a": 2}})
        result = self.adapter.min(
            "test",
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result is None
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()

    def test_use_changed_models_multiple_models(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"a": 2, "weight": 10},
                "test/2": {"a": 2, "weight": 20},
                "test/3": {"a": 2, "weight": 30},
                "test/4": {"a": 3, "weight": 1},
            }
        )
        result = self.adapter.min(
            "test",
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result == 10
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()

    def test_use_changed_models_numeric_not_comparable(self) -> None:
        """Only test/1 and test/3 with numeric values in a-field are accepted,
        because filter value 2 is numeric
        """
        self.set_additional_models(
            {
                "test/1": {"a": 2, "weight": 10},
                "test/2": {"a": "nop", "weight": 1},
                "test/3": {"a": 12, "weight": 3},
                "test/4": {"a": "15", "weight": 8},
                "test/5": {"a": "3", "weight": 10},
            }
        )
        result = self.adapter.min(
            "test",
            FilterOperator("a", ">=", 2),
            "weight",
        )
        assert result == 3
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()

    def test_use_changed_models_string_not_comparable(self) -> None:
        """Only test/2, test/4 and test/5 with string values in a-field are accepted,
        because filter value "2" is a string. The comparison is per string,
        therefore test/4 is not accepted ("15" is < "2").
        "nop" is greater than "2" and it's weight will be taken as result.
        """
        self.set_additional_models(
            {
                "test/1": {"a": 2, "weight": 10},
                "test/2": {"a": "nop", "weight": 1},
                "test/3": {"a": 12, "weight": 3},
                "test/4": {"a": "15", "weight": 8},
                "test/5": {"a": "3", "weight": 10},
            }
        )
        result = self.adapter.min(
            "test",
            FilterOperator("a", ">=", "2"),
            "weight",
        )
        assert result == 1
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()

    def test_use_changed_models_additional_none(self) -> None:
        self.filter_return_value = {
            2: {"a": 2, "weight": 100},
        }
        self.set_additional_models({"test/1": {"a": 2}})
        result = self.adapter.min(
            "test",
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result == 100
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()

    def test_use_changed_models_both_none(self) -> None:
        self.filter_return_value = {
            2: {"a": 2},
        }
        self.set_additional_models({"test/1": {"a": 2}})
        result = self.adapter.min(
            "test",
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result is None
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()

    def test_use_changed_models_additional_lower(self) -> None:
        self.filter_return_value = {
            2: {"a": 2, "weight": 100},
        }
        self.set_additional_models({"test/1": {"a": 2, "weight": 50}})
        result = self.adapter.min(
            "test",
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result == 50
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()

    def test_use_changed_models_db_lower(self) -> None:
        self.filter_return_value = {
            2: {"a": 2, "weight": 50},
        }
        self.set_additional_models({"test/1": {"a": 2, "weight": 100}})
        result = self.adapter.min(
            "test",
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result == 50
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()
