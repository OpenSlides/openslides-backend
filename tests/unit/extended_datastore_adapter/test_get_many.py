from unittest.mock import MagicMock

from openslides_backend.services.database.commands import GetManyRequest

from .base import BaseTestExtendedDatastoreAdapter


class TestGetManyExtendedDatastoreAdapter(BaseTestExtendedDatastoreAdapter):
    def test_only_db(self) -> None:
        self.set_additional_models({"test/1": {"f": 2}})
        result = self.adapter.get_many(
            [GetManyRequest(self.collection, [1, 2], ["f"])],
            use_changed_models=False,
        )
        assert result == {
            self.collection: {
                1: {"f": 1},
                2: {"f": 1},
            }
        }
        self.get_many_mock.assert_called()
        self.add_get_many_mock.assert_not_called()

    def test_only_db_empty(self) -> None:
        self.mock_datastore_content = {}
        result = self.adapter.get_many(
            MagicMock(),
            use_changed_models=False,
        )
        assert result == {}
        self.get_many_mock.assert_called()
        self.add_get_many_mock.assert_not_called()

    def test_use_changed_models(self) -> None:
        self.set_additional_models(
            {
                "test/2": {"f": 3, "weight": 42},
                "test/3": {"f": 2},
            }
        )
        result = self.adapter.get_many(
            [GetManyRequest(self.collection, [1, 2], ["f"])],
        )
        assert result == {
            self.collection: {
                1: {"f": 1},
                2: {"f": 3},
            }
        }
        self.get_many_mock.assert_called()
        gmr = self.get_many_mock.call_args[0][0]
        assert len(gmr) == 1
        assert gmr[0] == GetManyRequest(self.collection, [1], ["f"])
        self.add_get_many_mock.assert_called()

    def test_use_changed_models_missing_field(self) -> None:
        self.set_additional_models(
            {
                "test/1": {"weight": 42},
            }
        )
        result = self.adapter.get_many(
            [GetManyRequest(self.collection, [1], ["f", "weight"])],
        )
        assert result == {
            self.collection: {
                1: {"f": 1, "weight": 42},
            }
        }
        self.get_many_mock.assert_called()
        gmr = self.get_many_mock.call_args[0][0]
        assert len(gmr) == 1
        assert gmr[0] == GetManyRequest(self.collection, [1], ["f"])
        self.add_get_many_mock.assert_called()
