from typing import Any, Dict, List

import pytest

from openslides_backend.shared.exceptions import DatastoreException
from openslides_backend.shared.patterns import FullQualifiedId

from .base import BaseTestExtendedDatastoreAdapter


class TestGetExtendedDatastoreAdapter(BaseTestExtendedDatastoreAdapter):
    db_method_name = "get"

    def setUp(self) -> None:
        super().setUp()
        self.db_method_mock.side_effect = self._get_mock

    def _get_mock(
        self, fqid: FullQualifiedId, mapped_fields: List[str], *args: Any, **kwargs: Any
    ) -> Dict[str, Any]:
        if fqid.id in self.mock_datastore_content.get(fqid.collection, {}):
            model = self.mock_datastore_content[fqid.collection][fqid.id]
            return {field: model[field] for field in mapped_fields}
        else:
            raise DatastoreException("mock_db: model does not exist")

    def test_get_use_changed_models(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"f": 2},
            }
        )
        result = self.adapter.get(
            FullQualifiedId(self.collection, 1),
            ["f"],
        )
        assert result == {"f": 2}
        self.db_method_mock.assert_not_called()
        self.add_get_many_mock.assert_called()

    def test_get_use_changed_models_empty(self) -> None:
        result = self.adapter.get(
            FullQualifiedId(self.collection, 1),
            ["f"],
        )
        assert result == {"f": 1}
        self.db_method_mock.assert_called()
        self.add_get_many_mock.assert_called()

    def test_get_use_changed_models_missing_fields(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"weight": 42},
            }
        )
        result = self.adapter.get(
            FullQualifiedId(self.collection, 1),
            ["f", "weight"],
        )
        assert result == {"f": 1, "weight": 42}
        self.db_method_mock.assert_not_called()
        self.get_many_mock.assert_called()
        self.add_get_many_mock.assert_called()

    def test_get_use_changed_models_exception(self) -> None:
        self.mock_datastore_content = {}
        with pytest.raises(DatastoreException):
            self.adapter.get(
                FullQualifiedId(self.collection, 1),
                ["f"],
            )
        self.db_method_mock.assert_called()
        self.add_get_many_mock.assert_called()

    def test_get_only_db(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"f": 2},
            }
        )
        result = self.adapter.get(
            FullQualifiedId(self.collection, 1),
            ["f"],
            use_changed_models=False,
        )
        assert result == {"f": 1}
        self.db_method_mock.assert_called()
        self.add_get_many_mock.assert_not_called()

    def test_get_only_db_exception(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"f": 2},
            }
        )
        self.mock_datastore_content = {}
        with pytest.raises(DatastoreException):
            self.adapter.get(
                FullQualifiedId(self.collection, 1),
                ["f"],
                use_changed_models=False,
            )
        self.db_method_mock.assert_called()
        self.add_get_many_mock.assert_not_called()
