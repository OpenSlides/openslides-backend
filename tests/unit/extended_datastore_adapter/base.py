from typing import Any, Dict
from unittest import TestCase
from unittest.mock import MagicMock, patch

from openslides_backend.services.datastore.extended_adapter import (
    ExtendedDatastoreAdapter,
)
from tests.util import get_fqid


class BaseTestExtendedDatastoreAdapter(TestCase):
    db_method_return_value: Any
    db_method_name: str

    def setUp(self) -> None:
        db_method_patcher = patch(
            f"openslides_backend.services.datastore.adapter.DatastoreAdapter.{self.db_method_name}",
        )
        self.db_method_mock = db_method_patcher.start()
        self.addCleanup(db_method_patcher.stop)
        self.db_method_mock.side_effect = (
            lambda *args, **kwargs: self.db_method_return_value
        )

        self.adapter = ExtendedDatastoreAdapter(MagicMock(), MagicMock())
        orig_add_filter = self.adapter._filter_additional_models
        add_filter_patcher = patch.object(self.adapter, "_filter_additional_models")
        self.add_filter_mock = add_filter_patcher.start()
        self.addCleanup(add_filter_patcher.stop)
        self.add_filter_mock.side_effect = orig_add_filter

    def set_additional_models(self, models: Dict[str, Dict[str, Any]]) -> None:
        for fqid, model in models.items():
            self.adapter.update_additional_models(get_fqid(fqid), model)
