import json
from typing import Any, Dict, List, Type, cast
from unittest import TestCase

from datastore.shared.util import DeletedModelsBehaviour
from fastjsonschema import validate
from fastjsonschema.exceptions import JsonSchemaException

from openslides_backend.models.base import Model, model_registry
from openslides_backend.models.fields import BaseTemplateField
from openslides_backend.services.auth.interface import AuthenticationService
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.services.datastore.interface import Collection, DatastoreService
from openslides_backend.services.datastore.with_database_context import (
    with_database_context,
)
from openslides_backend.shared.exceptions import DatastoreException
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.interfaces.event import Event, EventType
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from openslides_backend.shared.util import EXAMPLE_DATA_FILE, get_initial_data_file
from tests.util import (
    Client,
    Response,
    get_collection_from_fqid,
    get_fqid,
    get_id_from_fqid,
)

from .util import TestVoteService

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"


class BaseSystemTestCase(TestCase):
    app: WSGIApplication
    auth: AuthenticationService
    datastore: DatastoreService
    vote_service: TestVoteService
    client: Client
    anon_client: Client
    media: Any  # Any is needed because it is mocked and has magic methods

    def setUp(self) -> None:
        self.app = self.get_application()
        self.services = self.app.services
        self.auth = self.services.authentication()
        self.media = self.services.media()
        self.vote_service = cast(TestVoteService, self.services.vote())
        self.datastore = self.services.datastore()
        self.datastore.truncate_db()

        self.create_model(
            "user/1",
            {
                "username": ADMIN_USERNAME,
                "password": self.auth.hash(ADMIN_PASSWORD),
                "default_password": ADMIN_PASSWORD,
                "is_active": True,
                "organization_management_level": "superadmin",
            },
        )
        self.client = self.create_client(ADMIN_USERNAME, ADMIN_PASSWORD)
        self.vote_service.set_authentication(self.client.headers, self.client.cookies)
        self.vote_service.clear_all()
        self.anon_client = self.create_client()

    def load_example_data(self) -> None:
        """
        Useful for debug purposes when an action fails with the example data.
        Do NOT use in final tests since it takes a long time.
        """
        example_data = get_initial_data_file(EXAMPLE_DATA_FILE)
        self._load_data(example_data)

    def load_json_data(self, filename: str) -> None:
        """
        Useful for debug purposes when an action fails with a specific dump.
        Do NOT use in final tests since it takes a long time.
        """
        with open(filename) as file:
            data = json.loads(file.read())
        self._load_data(data)

    def _load_data(self, raw_data: Dict[str, Dict[str, Any]]) -> None:
        data = {}
        for collection, models in raw_data.items():
            if collection == "_migration_index":
                continue
            for model_id, model in models.items():
                data[f"{collection}/{model_id}"] = {
                    f: v for f, v in model.items() if not f.startswith("meta_")
                }
        self.set_models(data)

    def create_client(self, username: str = None, password: str = None) -> Client:
        return Client(self.app, username, password)

    def get_application(self) -> WSGIApplication:
        raise NotImplementedError()

    def assert_status_code(self, response: Response, code: int) -> None:
        if (
            response.status_code != code
            and response.json
            and response.json.get("message")
        ):
            print(response.json)
        self.assertEqual(response.status_code, code)

    def get_create_request(
        self, fqid: str, data: Dict[str, Any] = {}, deleted: bool = False
    ) -> WriteRequest:
        data["id"] = get_id_from_fqid(fqid)
        self.validate_fields(fqid, data)
        request = WriteRequest(
            events=[Event(type=EventType.Create, fqid=get_fqid(fqid), fields=data)],
            information={},
            user_id=0,
            locked_fields={},
        )
        if deleted:
            request.events.append(Event(type=EventType.Delete, fqid=get_fqid(fqid)))
        return request

    def create_model(
        self, fqid: str, data: Dict[str, Any] = {}, deleted: bool = False
    ) -> None:
        request = self.get_create_request(fqid, data, deleted)
        self.datastore.write(request)

    def get_update_request(self, fqid: str, data: Dict[str, Any]) -> WriteRequest:
        self.validate_fields(fqid, data)
        request = WriteRequest(
            events=[Event(type=EventType.Update, fqid=get_fqid(fqid), fields=data)],
            information={},
            user_id=0,
            locked_fields={},
        )
        return request

    def update_model(self, fqid: str, data: Dict[str, Any]) -> None:
        request = self.get_update_request(fqid, data)
        self.datastore.write(request)

    @with_database_context
    def set_models(self, models: Dict[str, Dict[str, Any]]) -> None:
        """
        Can be used to set multiple models at once, independent of create or update.
        """
        response = self.datastore.get_many(
            [
                GetManyRequest(get_fqid(fqid).collection, [get_fqid(fqid).id], ["id"])
                for fqid in models.keys()
            ],
            lock_result=False,
        )
        requests: List[WriteRequest] = []
        for fqid_str, model in models.items():
            fqid = get_fqid(fqid_str)
            collection_map = response.get(fqid.collection)
            if collection_map and fqid.id in collection_map:
                requests.append(self.get_update_request(fqid_str, model))
            else:
                requests.append(self.get_create_request(fqid_str, model))
        self.datastore.write(requests)

    def validate_fields(self, fqid: str, fields: Dict[str, Any]) -> None:
        model = model_registry[get_collection_from_fqid(fqid)]()
        for field_name, value in fields.items():
            field = model.get_field(field_name)
            if isinstance(field, BaseTemplateField) and field.is_template_field(
                field_name
            ):
                schema = {
                    "type": ["array", "null"],
                    "items": {"type": "string"},
                }
            else:
                schema = field.get_schema()
            try:
                validate(schema, value)
            except JsonSchemaException as e:
                raise JsonSchemaException(
                    f"Invalid data for {fqid}/{field_name}: " + e.message
                )

    @with_database_context
    def get_model(self, fqid: str) -> Dict[str, Any]:
        model = self.datastore.get(
            get_fqid(fqid),
            get_deleted_models=DeletedModelsBehaviour.ALL_MODELS,
            lock_result=False,
        )
        self.assertTrue(model)
        self.assertEqual(model.get("id"), get_id_from_fqid(fqid))
        return model

    def assert_model_exists(
        self, fqid: str, fields: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        model = self.get_model(fqid)
        self.assertFalse(model.get("meta_deleted"))
        if fields is not None:
            for field_name, value in fields.items():
                self.assertEqual(
                    model.get(field_name),
                    value,
                    f"Models differ in field {field_name}!",
                )
        return model

    def assert_model_not_exists(self, fqid: str) -> None:
        with self.assertRaises(DatastoreException):
            self.get_model(fqid)

    def assert_model_deleted(
        self, fqid: str, fields: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        model = self.get_model(fqid)
        self.assertTrue(model.get("meta_deleted"), f"Model '{fqid}' was not deleted.")
        if fields is not None:
            for field_name, value in fields.items():
                self.assertEqual(model.get(field_name), value)
        return model

    def assert_defaults(self, model: Type[Model], instance: Dict[str, Any]) -> None:
        for field in model().get_fields():
            if hasattr(field, "default") and field.default is not None:
                self.assertEqual(
                    field.default,
                    instance.get(field.own_field_name),
                    f"Field {field.own_field_name}: Value {instance.get(field.own_field_name, 'None')} is not equal default value {field.default}.",
                )

    @with_database_context
    def assert_model_count(self, collection: str, meeting_id: int, count: int) -> None:
        db_count = self.datastore.count(
            Collection(collection),
            FilterOperator("meeting_id", "=", meeting_id),
            lock_result=False,
        )
        self.assertEqual(db_count, count)
