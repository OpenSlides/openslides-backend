from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.patterns import Collection

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
            Collection("test"),
            FilterOperator("a", "=", 2),
            "weight",
            use_changed_models=False,
        )
        assert result == 42
        self.db_method_mock.assert_called()
        self.filter_mock.assert_not_called()
        self.add_filter_mock.assert_not_called()

    def test_use_changed_models(self) -> None:
        self.set_additional_models({"test/1": {"a": 2, "weight": 100}})
        result = self.adapter.min(
            Collection("test"),
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result == 100
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_none(self) -> None:
        self.set_additional_models({"test/1": {"a": 2}})
        result = self.adapter.min(
            Collection("test"),
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result is None
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

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
            Collection("test"),
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result == 10
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_not_comparable(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"a": 2, "weight": 2},
                "test/2": {"a": "nop", "weight": 1},
            }
        )
        result = self.adapter.min(
            Collection("test"),
            FilterOperator("a", ">=", 2),
            "weight",
        )
        assert result == 2
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_additional_none(self) -> None:
        self.filter_return_value = {
            2: {"a": 2, "weight": 100},
        }
        self.set_additional_models({"test/1": {"a": 2}})
        result = self.adapter.min(
            Collection("test"),
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result == 100
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_both_none(self) -> None:
        self.filter_return_value = {
            2: {"a": 2},
        }
        self.set_additional_models({"test/1": {"a": 2}})
        result = self.adapter.min(
            Collection("test"),
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result is None
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_additional_lower(self) -> None:
        self.filter_return_value = {
            2: {"a": 2, "weight": 100},
        }
        self.set_additional_models({"test/1": {"a": 2, "weight": 50}})
        result = self.adapter.min(
            Collection("test"),
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result == 50
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_db_lower(self) -> None:
        self.filter_return_value = {
            2: {"a": 2, "weight": 50},
        }
        self.set_additional_models({"test/1": {"a": 2, "weight": 100}})
        result = self.adapter.min(
            Collection("test"),
            FilterOperator("a", "=", 2),
            "weight",
        )
        assert result == 50
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()
