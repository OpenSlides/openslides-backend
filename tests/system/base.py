from typing import Any, Dict
from unittest import TestCase

import requests
import simplejson as json
from werkzeug.wrappers import Response

from openslides_backend.services.auth.interface import AuthenticationService
from openslides_backend.services.datastore.interface import (
    DatastoreService,
    DeletedModelsBehaviour,
)
from openslides_backend.shared.exceptions import DatastoreException
from openslides_backend.shared.interfaces.event import Event
from openslides_backend.shared.interfaces.write_request_element import (
    WriteRequestElement,
)
from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from tests.util import Client, get_fqid, get_id_from_fqid

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"


class BaseSystemTestCase(TestCase):
    app: WSGIApplication
    auth: AuthenticationService
    datastore: DatastoreService
    client: Client
    media: Any  # Any is needed because it is mocked and has magic methods
    EXAMPLE_DATA = "https://raw.githubusercontent.com/OpenSlides/OpenSlides/openslides4-dev/docs/example-data.json"

    def setUp(self) -> None:
        self.app = self.get_application()
        self.services = self.app.services
        self.auth = self.services.authentication()
        self.media = self.services.media()
        self.datastore = self.services.datastore()
        self.datastore.truncate_db()

        self.create_model(
            "user/1",
            {
                "username": ADMIN_USERNAME,
                "password": self.auth.hash(ADMIN_PASSWORD),
                "is_active": True,
            },
        )
        self.client = self.create_client(ADMIN_USERNAME, ADMIN_PASSWORD)

    def load_example_data(self) -> None:
        """
        Useful for debug purposes when an action fails with the example data.
        Do NOT use in final tests since it takes a long time.
        """
        self.datastore.truncate_db()
        example_data = json.loads(requests.get(self.EXAMPLE_DATA).content)
        for collection, models in example_data.items():
            for model in models:
                self.create_model(f"{collection}/{model['id']}", model)

    def create_client(self, username: str, password: str) -> Client:
        return Client(self.app, username, password)

    def get_application(self) -> WSGIApplication:
        raise NotImplementedError()

    def assert_status_code(self, response: Response, code: int) -> None:
        if response.status_code != code and response.data:
            print(response.data)
        self.assertEqual(response.status_code, code)

    def create_model(
        self, fqid: str, data: Dict[str, Any], deleted: bool = False
    ) -> None:
        data["id"] = get_id_from_fqid(fqid)
        request = WriteRequestElement(
            events=[Event(type="create", fqid=get_fqid(fqid), fields=data)],
            information={},
            user_id=0,
        )
        if deleted:
            request.events.append(Event(type="delete", fqid=get_fqid(fqid)))
        self.datastore.write(request)

    def update_model(self, fqid: str, data: Dict[str, Any]) -> None:
        request = WriteRequestElement(
            events=[Event(type="update", fqid=get_fqid(fqid), fields=data)],
            information={},
            user_id=0,
        )
        self.datastore.write(request)

    def get_model(self, fqid: str) -> Dict[str, Any]:
        model = self.datastore.get(
            get_fqid(fqid), get_deleted_models=DeletedModelsBehaviour.ALL_MODELS
        )
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
        with self.assertRaises(DatastoreException):
            self.get_model(fqid)

    def assert_model_deleted(self, fqid: str) -> None:
        model = self.get_model(fqid)
        self.assertTrue(model.get("meta_deleted"))
