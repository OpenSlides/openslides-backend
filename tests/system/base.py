from typing import Any, Dict
from unittest import TestCase

from werkzeug.wrappers import Response

from openslides_backend.services.datastore.interface import Datastore
from openslides_backend.shared.exceptions import DatabaseException
from openslides_backend.shared.interfaces import (
    Event,
    WriteRequestElement,
    WSGIApplication,
)
from tests.system.util import Client
from tests.util import get_fqid, get_id_from_fqid


class BaseSystemTestCase(TestCase):
    def setUp(self) -> None:
        app = self.get_application()
        self.client = Client(app)
        self.datastore: Datastore = app.services.datastore()  # type: ignore
        self.datastore.truncate_db()

    def get_application(self) -> WSGIApplication:
        raise NotImplementedError()

    def assert_status_code(self, response: Response, code: int) -> None:
        if response.status_code != code and response.data:
            print(response.data)
        self.assertEqual(response.status_code, code)

    def create_model(self, fqid: str, data: Dict[str, Any]) -> None:
        data["id"] = get_id_from_fqid(fqid)
        request = WriteRequestElement(
            events=[Event(type="create", fqid=get_fqid(fqid), fields=data)],
            information={},
            user_id=0,
        )
        self.datastore.write(request)

    def get_model(self, fqid: str) -> Dict[str, Any]:
        model = self.datastore.get(get_fqid(fqid), get_deleted_models=3)
        self.assertTrue(model)
        self.assertEqual(model.get("id"), get_id_from_fqid(fqid))
        return model

    def assert_model_exists(self, fqid: str, fields: Dict[str, Any] = None) -> None:
        model = self.get_model(fqid)
        self.assertFalse(model.get("meta_deleted"))
        if fields is not None:
            for field_name, value in fields.items():
                self.assertEqual(model.get(field_name), value)

    def assert_model_not_exists(self, fqid: str) -> None:
        with self.assertRaises(DatabaseException):
            self.get_model(fqid)

    def assert_model_deleted(self, fqid: str) -> None:
        model = self.get_model(fqid)
        self.assertTrue(model.get("meta_deleted"))
