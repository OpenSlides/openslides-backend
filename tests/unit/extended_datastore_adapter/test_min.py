# from unittest.mock import MagicMock

# from openslides_backend.services.datastore.interface import InstanceAdditionalBehaviour
# from openslides_backend.shared.filters import FilterOperator
# from openslides_backend.shared.patterns import Collection

# from .base import BaseTestExtendedDatastoreAdapter


# class TestMinExtendedDatastoreAdapter(BaseTestExtendedDatastoreAdapter):
#     db_method_name = "min"

#     def setUp(self) -> None:
#         super().setUp()
#         self.db_method_return_value = 42

#     def test_only_db(self) -> None:
#         self.set_additional_models({"test/1": {"a": 2, "weight": 1}})
#         result = self.adapter.min(
#             Collection("test"),
#             FilterOperator("a", "=", 2),
#             "weight",
#             db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
#         )
#         assert result == 42
#         self.db_method_mock.assert_called()
#         self.add_filter_mock.assert_not_called()

#     def test_only_db_none(self) -> None:
#         self.db_method_return_value = None
#         result = self.adapter.min(
#             MagicMock(),
#             MagicMock(),
#             MagicMock(),
#             db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
#         )
#         assert result is None
#         self.db_method_mock.assert_called()
#         self.add_filter_mock.assert_not_called()

#     def test_only_additional(self) -> None:
#         self.set_additional_models({"test/1": {"a": 2, "weight": 100}})
#         result = self.adapter.min(
#             Collection("test"),
#             FilterOperator("a", "=", 2),
#             "weight",
#             db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
#         )
#         assert result == 100
#         self.db_method_mock.assert_not_called()
#         self.add_filter_mock.assert_called()

#     def test_only_additional_none(self) -> None:
#         self.set_additional_models({"test/1": {"a": 2}})
#         result = self.adapter.min(
#             Collection("test"),
#             FilterOperator("a", "=", 2),
#             "weight",
#             db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
#         )
#         assert result is None
#         self.db_method_mock.assert_not_called()
#         self.add_filter_mock.assert_called()

#     def test_only_additional_multiple_models(self) -> None:
#         self.set_additional_models(
#             {
#                 "test/1": {"a": 2, "weight": 50},
#                 "test/2": {"a": 2, "weight": 51},
#                 "test/3": {"a": 2, "weight": 52},
#                 "test/4": {"a": 3, "weight": 42},
#             }
#         )
#         result = self.adapter.min(
#             Collection("test"),
#             FilterOperator("a", "=", 2),
#             "weight",
#             db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
#         )
#         assert result == 50
#         self.db_method_mock.assert_not_called()
#         self.add_filter_mock.assert_called()

#     def test_only_additional_not_comparable(self) -> None:
#         self.set_additional_models(
#             {
#                 "test/1": {"a": 2, "weight": 2},
#                 "test/2": {"a": "nop", "weight": 1},
#             }
#         )
#         result = self.adapter.min(
#             Collection("test"),
#             FilterOperator("a", ">=", 2),
#             "weight",
#             db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
#         )
#         assert result == 2
#         self.db_method_mock.assert_not_called()
#         self.add_filter_mock.assert_called()

#     def test_db_and_additional_db_none(self) -> None:
#         self.db_method_return_value = None
#         self.set_additional_models({"test/1": {"a": 2, "weight": 1}})
#         result = self.adapter.min(
#             Collection("test"),
#             FilterOperator("a", "=", 2),
#             "weight",
#             db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
#         )
#         assert result == 1
#         self.db_method_mock.assert_called()
#         self.add_filter_mock.assert_called()

#     def test_db_and_additional_additional_none(self) -> None:
#         self.set_additional_models({"test/1": {"a": 2}})
#         result = self.adapter.min(
#             Collection("test"),
#             FilterOperator("a", "=", 2),
#             "weight",
#             db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
#         )
#         assert result == 42
#         self.db_method_mock.assert_called()
#         self.add_filter_mock.assert_called()

#     def test_db_and_additional_both_none(self) -> None:
#         self.db_method_return_value = None
#         self.set_additional_models({"test/1": {"a": 2}})
#         result = self.adapter.min(
#             Collection("test"),
#             FilterOperator("a", "=", 2),
#             "weight",
#             db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
#         )
#         assert result is None
#         self.db_method_mock.assert_called()
#         self.add_filter_mock.assert_called()

#     def test_db_and_additional_additional_lower(self) -> None:
#         self.set_additional_models({"test/1": {"a": 2, "weight": 1}})
#         result = self.adapter.min(
#             Collection("test"),
#             FilterOperator("a", "=", 2),
#             "weight",
#             db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
#         )
#         assert result == 1
#         self.db_method_mock.assert_called()
#         self.add_filter_mock.assert_called()

#     def test_db_and_additional_db_lower(self) -> None:
#         self.set_additional_models({"test/1": {"a": 2, "weight": 100}})
#         result = self.adapter.min(
#             Collection("test"),
#             FilterOperator("a", "=", 2),
#             "weight",
#             db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
#         )
#         assert result == 42
#         self.db_method_mock.assert_called()
#         self.add_filter_mock.assert_called()
