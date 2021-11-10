from unittest.mock import MagicMock

from openslides_backend.services.datastore.interface import InstanceAdditionalBehaviour
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.patterns import Collection

from .base import BaseTestExtendedDatastoreAdapter


class TestFilterExtendedDatastoreAdapter(BaseTestExtendedDatastoreAdapter):
    db_method_name = "filter"

    def setUp(self) -> None:
        super().setUp()
        self.db_method_return_value = {
            1: {"f": 1},
            2: {"f": 1},
        }

    def test_only_db(self) -> None:
        self.set_additional_models({"test/1": {"a": 2, "weight": 1}})
        result = self.adapter.filter(
            Collection("test"),
            FilterOperator("a", "=", 2),
            ["f", "weight"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
        )
        assert result == {
            1: {"f": 1},
            2: {"f": 1},
        }
        self.db_method_mock.assert_called()
        self.add_filter_mock.assert_not_called()

    def test_only_db_empty(self) -> None:
        self.db_method_return_value = {}
        result = self.adapter.filter(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
        )
        assert result == {}
        self.db_method_mock.assert_called()
        self.add_filter_mock.assert_not_called()

    def test_only_additional(self) -> None:
        self.set_additional_models({"test/1": {"a": 2, "weight": 100}})
        result = self.adapter.filter(
            Collection("test"),
            FilterOperator("a", "=", 2),
            ["f", "weight"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
        )
        assert result == {1: {"weight": 100}}
        self.db_method_mock.assert_not_called()
        self.add_filter_mock.assert_called()

    def test_only_additional_empty(self) -> None:
        self.set_additional_models({"test/1": {"a": 2}})
        result = self.adapter.filter(
            Collection("test"),
            FilterOperator("a", "=", 3),
            ["f", "weight"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
        )
        assert result == {}
        self.db_method_mock.assert_not_called()
        self.add_filter_mock.assert_called()

    def test_only_additional_multiple_models(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"a": 2, "weight": 50},
                "test/2": {"a": 2, "weight": 51},
                "test/3": {"a": 2, "weight": 52},
                "test/4": {"a": 3, "weight": 42},
            }
        )
        result = self.adapter.filter(
            Collection("test"),
            FilterOperator("a", "=", 2),
            ["f", "weight"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
        )
        assert result == {
            1: {"weight": 50},
            2: {"weight": 51},
            3: {"weight": 52},
        }
        self.db_method_mock.assert_not_called()
        self.add_filter_mock.assert_called()

    def test_additional_before_db(self) -> None:
        self.set_additional_models(
            {
                "test/2": {"a": 2, "f": 3, "weight": 50},
                "test/3": {"a": 2, "weight": 42},
            }
        )
        result = self.adapter.filter(
            Collection("test"),
            FilterOperator("a", "=", 2),
            ["f", "weight"],
            db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
        )
        assert result == {
            1: {"f": 1},
            2: {"f": 3, "weight": 50},
            3: {"weight": 42},
        }
        self.db_method_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_db_before_additional(self) -> None:
        self.set_additional_models(
            {
                "test/2": {"a": 2, "f": 3, "weight": 50},
                "test/3": {"a": 2, "weight": 42},
            }
        )
        result = self.adapter.filter(
            Collection("test"),
            FilterOperator("a", "=", 2),
            ["f", "weight"],
            db_additional_relevance=InstanceAdditionalBehaviour.DBINST_BEFORE_ADDITIONAL,
        )
        assert result == {
            1: {"f": 1},
            2: {"f": 1, "weight": 50},
            3: {"weight": 42},
        }
        self.db_method_mock.assert_called()
        self.add_filter_mock.assert_called()
