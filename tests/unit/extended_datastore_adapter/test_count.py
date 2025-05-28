from openslides_backend.shared.filters import FilterOperator

from .base import BaseTestExtendedDatastoreAdapter


class TestCountExtendedDatastoreAdapter(BaseTestExtendedDatastoreAdapter):
    """Also basically tests `exists` which just returns len() > 0"""

    db_method_name = "count"

    def setUp(self) -> None:
        super().setUp()
        self.db_method_return_value = 42
        self.filter_return_value = {}

    def test_only_db(self) -> None:
        self.set_additional_models({"test/1": {"a": 2}})
        result = self.adapter.count(
            "test",
            FilterOperator("a", "=", 2),
            use_changed_models=False,
        )
        assert result == 42
        self.db_method_mock.assert_called()
        self.filter_mock.assert_not_called()
        # TODO See TODO in tests/unit/extended_datastore_adapter/base.py
        # If that's done reactivate line below and other such lines in this file?
        # self.add_filter_mock.assert_not_called()
        # self.add_filter_mock.assert_not_called()

    def test_use_changed_models(self) -> None:
        self.set_additional_models(
            {
                "test/2": {"a": 2},
                "test/3": {"a": 2},
            }
        )
        result = self.adapter.count(
            "test",
            FilterOperator("a", "=", 2),
        )
        assert result == 2
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()

    def test_use_changed_models_with_db(self) -> None:
        self.filter_return_value = {
            self.collection: {
                1: {"a": 2},
            }
        }
        self.set_additional_models(
            {
                "test/2": {"a": 2},
                "test/3": {"a": 2},
            }
        )
        result = self.adapter.count(
            "test",
            FilterOperator("a", "=", 2),
        )
        assert result == 3
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()

    def test_use_changed_models_empty(self) -> None:
        result = self.adapter.count(
            "test",
            FilterOperator("a", "=", 2),
        )
        assert result == 0
        self.db_method_mock.assert_not_called()
        self.filter_mock.assert_called()
        # self.add_filter_mock.assert_called()
