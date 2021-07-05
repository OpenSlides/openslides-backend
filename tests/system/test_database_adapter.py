from typing import Any, Dict

import pytest

from openslides_backend.services.datastore.interface import InstanceAdditionalBehaviour
from openslides_backend.shared.exceptions import DatastoreException
from openslides_backend.shared.patterns import Collection, FullQualifiedId
from tests.system.action.base import BaseActionTestCase


class DatabaseAdapterSystemTest(BaseActionTestCase):
    def fetch_model(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        with self.datastore.get_database_context():
            return self.datastore.fetch_model(*args, **kwargs)

    def init_both(self) -> None:
        self.set_models(
            {"meeting/1": {"name": "meetingDB", "description": "descriptionDB"}}
        )
        self.datastore.additional_relation_models[
            FullQualifiedId(Collection("meeting"), 1)
        ] = {"id": 1, "name": "meetingAdd"}

    def init_only_db(self) -> None:
        self.set_models({"meeting/1": {"name": "meetingDB"}})

    def init_only_add(self) -> None:
        self.datastore.additional_relation_models[
            FullQualifiedId(Collection("meeting"), 1)
        ] = {"id": 1, "name": "meetingAdd"}

    def test_fetch_model_ADD_BEFORE_DB_both(self) -> None:
        self.init_both()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name", "id", "description", "not_there"],
        )
        self.assertEqual(result["name"], "meetingAdd")
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["description"], "descriptionDB")
        self.assertEqual(result.get("not_there", "None"), "None")

    def test_fetch_model_ADD_BEFORE_DB_onlyDB(self) -> None:
        self.init_only_db()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
        )
        self.assertEqual(result["name"], "meetingDB")

    def test_fetch_model_ADD_BEFORE_DB_onlyAdd(self) -> None:
        self.init_only_add()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
        )
        self.assertEqual(result["name"], "meetingAdd")

    def test_fetch_model_ADD_BEFORE_DB_nothing(self) -> None:
        with pytest.raises(DatastoreException) as e:
            self.fetch_model(
                fqid=FullQualifiedId(Collection("meeting"), 1),
                mapped_fields=["name"],
            )
        self.assertIn(
            "Model 'meeting/1' does not exist.",
            e.value.message,
        )

    def test_fetch_model_ADD_BEFORE_DB_nothing_no_exception(self) -> None:
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            exception=False,
        )
        self.assertEqual(result.get("name"), None)

    def test_fetch_model_DB_BEFORE_ADD_both(self) -> None:
        self.init_both()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.DBINST_BEFORE_ADDITIONAL,
        )
        self.assertEqual(result["name"], "meetingDB")

    def test_fetch_model_DB_BEFORE_ADD_onlyDB(self) -> None:
        self.init_only_db()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.DBINST_BEFORE_ADDITIONAL,
        )
        self.assertEqual(result["name"], "meetingDB")

    def test_fetch_model_DB_BEFORE_ADD_onlyAdd(self) -> None:
        self.init_only_add()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.DBINST_BEFORE_ADDITIONAL,
        )
        self.assertEqual(result["name"], "meetingAdd")

    def test_fetch_model_DB_BEFORE_ADD_nothing(self) -> None:
        with pytest.raises(DatastoreException) as e:
            self.fetch_model(
                fqid=FullQualifiedId(Collection("meeting"), 1),
                mapped_fields=["name"],
                db_additional_relevance=InstanceAdditionalBehaviour.DBINST_BEFORE_ADDITIONAL,
            )
        self.assertIn(
            "Model 'meeting/1' does not exist.",
            e.value.message,
        )

    def test_fetch_model_DB_BEFORE_ADD_nothing_no_exception(self) -> None:
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.DBINST_BEFORE_ADDITIONAL,
            exception=False,
        )
        self.assertEqual(result.get("name"), None)

    def test_fetch_model_ONLY_ADD_both(self) -> None:
        self.init_both()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
        )
        self.assertEqual(result["name"], "meetingAdd")

    def test_fetch_model_ONLY_ADD_onlyDB(self) -> None:
        self.init_only_db()
        with pytest.raises(DatastoreException) as e:
            self.fetch_model(
                fqid=FullQualifiedId(Collection("meeting"), 1),
                mapped_fields=["name"],
                db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
            )
        self.assertIn("meeting/1 not found at all.", e.value.message)

    def test_fetch_model_ONLY_ADD_onlyDB_no_exception(self) -> None:
        self.init_only_db()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
            exception=False,
        )
        self.assertEqual(result.get("name"), None)

    def test_fetch_model_ONLY_ADD_onlyAdd(self) -> None:
        self.init_only_add()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
        )
        self.assertEqual(result["name"], "meetingAdd")

    def test_fetch_model_ONLY_ADD_nothing(self) -> None:
        with pytest.raises(DatastoreException) as e:
            self.fetch_model(
                fqid=FullQualifiedId(Collection("meeting"), 1),
                mapped_fields=["name"],
                db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
            )
        self.assertIn("meeting/1 not found at all.", e.value.message)

    def test_fetch_model_ONLY_ADD_nothing_no_exception(self) -> None:
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
            exception=False,
        )
        self.assertEqual(result.get("name"), None)

    def test_fetch_model_ONLY_DB_both(self) -> None:
        self.init_both()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
        )
        self.assertEqual(result["name"], "meetingDB")

    def test_fetch_model_ONLY_DB_onlyDB(self) -> None:
        self.init_only_db()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
        )
        self.assertEqual(result.get("name"), "meetingDB")

    def test_fetch_model_ONLY_DB_onlyAdd(self) -> None:
        self.init_only_add()
        with pytest.raises(DatastoreException) as e:
            self.fetch_model(
                fqid=FullQualifiedId(Collection("meeting"), 1),
                mapped_fields=["name"],
                db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
            )
        self.assertIn(
            "Model 'meeting/1' does not exist.",
            e.value.message,
        )

    def test_fetch_model_ONLY_DB_onlyAdd_no_exception(self) -> None:
        self.init_only_add()
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
            exception=False,
        )
        self.assertEqual(result.get("name"), None)

    def test_fetch_model_ONLY_DB_nothing(self) -> None:
        with pytest.raises(DatastoreException) as e:
            self.fetch_model(
                fqid=FullQualifiedId(Collection("meeting"), 1),
                mapped_fields=["name"],
                db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
            )
        self.assertIn(
            "Model 'meeting/1' does not exist.",
            e.value.message,
        )

    def test_fetch_model_ONLY_DB_nothing_no_exception(self) -> None:
        result = self.fetch_model(
            fqid=FullQualifiedId(Collection("meeting"), 1),
            mapped_fields=["name"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
            exception=False,
        )
        self.assertEqual(result.get("name"), None)
