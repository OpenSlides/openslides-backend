from typing import Any, Dict, List

import pytest

from openslides_backend.shared.exceptions import DatastoreException
from openslides_backend.shared.patterns import (
    FullQualifiedId,
    fqid_collection,
    fqid_id,
    to_fqid,
)

from .base import BaseTestExtendedDatastoreAdapter


class TestGetExtendedDatastoreAdapter(BaseTestExtendedDatastoreAdapter):
    db_method_name = "get"

    def setUp(self) -> None:
        super().setUp()
        self.db_method_mock.side_effect = self._get_mock

    def _get_mock(
        self, fqid: FullQualifiedId, mapped_fields: List[str], *args: Any, **kwargs: Any
    ) -> Dict[str, Any]:
        if fqid_id(fqid) in self.mock_datastore_content.get(fqid_collection(fqid), {}):
            model = self.mock_datastore_content[fqid_collection(fqid)][fqid_id(fqid)]
            if mapped_fields:
                return {field: model[field] for field in mapped_fields}
            else:
                return model
        else:
            raise DatastoreException("mock_db: model does not exist")

    def test_get_use_changed_models(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"f": 2},
            }
        )
        result = self.adapter.get(
            to_fqid(self.collection, 1),
            ["f"],
        )
        assert result == {"f": 2}
        self.db_method_mock.assert_not_called()
        self.add_get_many_mock.assert_called()

    def test_get_use_changed_models_empty(self) -> None:
        result = self.adapter.get(
            to_fqid(self.collection, 1),
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
            to_fqid(self.collection, 1),
            ["f", "weight"],
        )
        assert result == {"f": 1, "weight": 42}
        self.db_method_mock.assert_called()
        self.add_get_many_mock.assert_called()

    def test_get_use_changed_models_exception(self) -> None:
        self.mock_datastore_content = {}
        with pytest.raises(DatastoreException):
            self.adapter.get(
                to_fqid(self.collection, 1),
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
            to_fqid(self.collection, 1),
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
                to_fqid(self.collection, 1),
                ["f"],
                use_changed_models=False,
            )
        self.db_method_mock.assert_called()
        self.add_get_many_mock.assert_not_called()

    def test_get_empty_mapped_fields_and_changed_models(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"id": 1, "changed": 3},
            }
        )
        result = self.adapter.get(to_fqid(self.collection, 1), [])
        assert result == {"id": 1, "f": 1, "unused": 2, "changed": 3}
        self.db_method_mock.assert_called()
        self.add_get_many_mock.assert_called()
