from unittest.mock import MagicMock

from openslides_backend.datastore.shared.util import DeletedModelsBehaviour
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.typing import DeletedModel

from .base import BaseTestExtendedDatastoreAdapter


class TestFilterExtendedDatastoreAdapter(BaseTestExtendedDatastoreAdapter):
    def setUp(self) -> None:
        super().setUp()
        self.filter_return_value = {
            1: {"f": 1},
            2: {"f": 1},
        }

    def test_only_db(self) -> None:
        self.set_additional_models({"test/1": {"a": 2, "weight": 1}})
        result = self.adapter.filter(
            self.collection,
            FilterOperator("a", "=", 2),
            ["f", "weight"],
            use_changed_models=False,
        )
        assert result == {
            1: {"f": 1},
            2: {"f": 1},
        }
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_not_called()

    def test_only_db_empty(self) -> None:
        self.filter_return_value = {}
        result = self.adapter.filter(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            use_changed_models=False,
        )
        assert result == {}
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_not_called()

    def test_use_changed_models(self) -> None:
        self.set_additional_models(
            {
                "test/2": {"a": 2, "f": 3, "weight": 50},
                "test/3": {"a": 2, "weight": 42},
            }
        )
        result = self.adapter.filter(
            self.collection,
            FilterOperator("a", "=", 2),
            ["f", "weight"],
        )
        assert result == {
            1: {"f": 1},
            2: {"f": 3, "weight": 50},
            3: {"weight": 42},
        }
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_not_in_filter(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"f": 3},
            }
        )
        result = self.adapter.filter(
            self.collection,
            FilterOperator("a", "=", 2),
            ["f"],
        )
        assert result == {
            1: {"f": 3},
            2: {"f": 1},
        }
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_missing_fields(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"a": 3, "f": 2},
                "test/2": {"a": 3},
            }
        )
        self.filter_return_value = {}
        self.mock_datastore_content = {self.collection: {2: {"f": 17}}}
        result = self.adapter.filter(
            self.collection,
            FilterOperator("a", "=", 3),
            ["f"],
        )
        assert result == {
            1: {"f": 2},
            2: {"f": 17},
        }
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()
        self.get_many_mock.assert_called()

    def test_use_changed_models_deleted(self) -> None:
        self.set_additional_models(
            {
                "test/1": DeletedModel(),
            }
        )
        result = self.adapter.filter(
            self.collection,
            FilterOperator("a", "=", 2),
            ["f"],
        )
        assert result == {
            2: {"f": 1},
        }
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_deleted_all_models(self) -> None:
        self.set_additional_models(
            {
                "test/1": DeletedModel(),
            }
        )
        result = self.adapter.filter(
            self.collection,
            FilterOperator("a", "=", 2),
            ["f"],
            DeletedModelsBehaviour.ALL_MODELS,
        )
        assert result == {
            1: {"f": 1},
            2: {"f": 1},
        }
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_check_comparable(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"f": 2},
                "test/2": {"f": 3},
            }
        )
        result = self.adapter.filter(
            self.collection,
            FilterOperator("f", ">", 1),
            ["f"],
        )
        assert result == {
            1: {"f": 2},
            2: {"f": 3},
        }
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_not_comparable(self) -> None:
        self.filter_return_value = {}
        self.set_additional_models(
            {
                "test/1": {"f": "str"},
                "test/2": {"f": 3},
            }
        )
        result = self.adapter.filter(
            self.collection,
            FilterOperator("f", ">", 1),
            ["f"],
        )
        assert result == {
            2: {"f": 3},
        }
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()

    def test_use_changed_models_is_none(self) -> None:
        self.filter_return_value = {}
        self.set_additional_models(
            {
                "test/1": {"f": None},
                "test/2": {"f": 3},
            }
        )
        result = self.adapter.filter(
            self.collection,
            FilterOperator("f", "=", None),
            ["f"],
        )
        assert result == {
            1: {"f": None},
        }
        self.filter_mock.assert_called()
        self.add_filter_mock.assert_called()
