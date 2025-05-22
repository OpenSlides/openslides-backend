# TODO consider to delete all tests of this directory
from collections import defaultdict
from typing import Any
from unittest import TestCase
from unittest.mock import patch

# from openslides_backend.datastore.shared.postgresql_backend import filter_models
from openslides_backend.services.database.commands import GetManyRequest
from openslides_backend.shared.patterns import Collection
from openslides_backend.shared.typing import DeletedModel


class BaseTestExtendedDatastoreAdapter(TestCase):
    db_method_name: str | None = None
    db_method_return_value: Any
    filter_return_value: Any

    mock_datastore_content: dict[Collection, dict[int, dict[str, Any]]]

    collection = "test"

    def setUp(self) -> None:
        self.get_many_mock = self.patch_method("get_many")
        self.get_many_mock.side_effect = self._get_many_mock

        self.filter_mock = self.patch_method("filter")
        self.filter_mock.side_effect = lambda *args, **kwargs: self.filter_return_value

        if self.db_method_name:
            self.db_method_mock = self.patch_method(self.db_method_name)
            self.db_method_mock.side_effect = (
                lambda *args, **kwargs: self.db_method_return_value
            )

        # TODO this needs to be created on top of the call stack from where it is needed.
        # self.adapter = ExtendedDatabase(MagicMock(), MagicMock())

        # TODO: Make this work again?
        # patcher = patch(
        #     "openslides_backend.services.datastore.extended_adapter.filter_models",
        #     side_effect=filter_models,
        # )
        # self.add_filter_mock = patcher.start()
        # self.addCleanup(patcher.stop)

        self.add_get_many_mock = self.add_mock_to_method(
            "_get_many_from_changed_models"
        )

        self.mock_datastore_content = {
            self.collection: {
                1: {"f": 1, "unused": 2},
                2: {"f": 1, "unused": 2},
            }
        }

    def _get_many_mock(
        self, get_many_requests: list[GetManyRequest], *args: Any, **kwargs: Any
    ) -> dict[Collection, dict[int, dict[str, Any]]]:
        results: dict[Collection, dict[int, dict[str, Any]]] = defaultdict(
            lambda: defaultdict(dict)
        )
        for request in get_many_requests:
            for id in request.ids:
                if id in self.mock_datastore_content.get(request.collection, {}):
                    model = self.mock_datastore_content[request.collection][id]
                    for field in request.mapped_fields:
                        if field in model:
                            results[request.collection][id][field] = model[field]
        return results

    def set_additional_models(self, models: dict[str, dict[str, Any]]) -> None:
        for fqid, model in models.items():
            self.adapter.apply_changed_model(
                fqid, model, isinstance(model, DeletedModel)
            )

    def add_mock_to_method(self, method_name: str) -> Any:
        """
        Inserts a proxy mock for the given method on the adapter to keep track of calls.
        """
        orig_method = getattr(self.adapter, method_name)
        patcher = patch.object(self.adapter, method_name)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        mock.side_effect = orig_method
        return mock

    def patch_method(self, method_name: str) -> Any:
        """
        Patches a method on the original adapter (superclass of the extended one) to control the
        return value.
        """
        patcher = patch(
            f"openslides_backend.services.datastore.cache_adapter.CacheDatastoreAdapter.{method_name}",
        )
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock
