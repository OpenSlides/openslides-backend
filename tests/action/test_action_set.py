import inspect
from unittest import TestCase

import simplejson as json

from openslides_backend.action.action import register_action_set
from openslides_backend.action.action_set import ActionSet
from openslides_backend.action.generics import CreateAction, DeleteAction, UpdateAction
from openslides_backend.models.base import Model
from openslides_backend.shared.patterns import Collection

from ..utils import Client, ResponseWrapper, create_test_application, get_fqfield


def dummy_schema(schema: str) -> None:
    pass


class DummyModelVcioluoffl(Model):
    collection = Collection("dummy_model_vcioluoffl")


@register_action_set("dummy_model_vcioluoffl")
class DummyActionSet_phooth3I(ActionSet):
    model = DummyModelVcioluoffl()
    create_schema = dummy_schema
    update_schema = dummy_schema
    delete_schema = dummy_schema


class ActionSetTester(TestCase):
    def test_dummy_action_set_routes(self) -> None:
        for route, action in DummyActionSet_phooth3I.get_actions():
            self.assertIn(
                action.__name__,
                (
                    "DummyModelVcioluofflCreate",
                    "DummyModelVcioluofflUpdate",
                    "DummyModelVcioluofflDelete",
                ),
            )
            self.assertIn(
                route, ("create", "update", "delete"),
            )

    def test_dummy_action_set_types(self) -> None:
        for name, action in DummyActionSet_phooth3I.get_actions():
            generic_base = inspect.getmro(action)[1]
            self.assertIn(generic_base, (CreateAction, UpdateAction, DeleteAction))

    def test_wsgi_create(self) -> None:
        self.datastore_content = {
            get_fqfield("organisation/1/name"): "test_organisation_name",
        }
        self.user_id = 2879730333
        expected_write_data = json.dumps(
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": "dummy_model_vcioluoffl/42",
                        "fields": {"dummy_field_Ugh8joom0a": "OhquooPhu8"},
                    },
                ],
                "information": {"dummy_model_vcioluoffl/42": ["Object created"]},
                "user_id": self.user_id,
                "locked_fields": {},
            }
        )
        application = create_test_application(
            user_id=self.user_id,
            view_name="ActionView",
            superuser=self.user_id,
            datastore_content=self.datastore_content,
            expected_write_data=expected_write_data,
        )
        client = Client(application, ResponseWrapper)
        response = client.post(
            "/",
            json=[
                {
                    "action": "dummy_model_vcioluoffl.create",
                    "data": [{"dummy_field_Ugh8joom0a": "OhquooPhu8"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_update(self) -> None:
        self.datastore_content = {
            get_fqfield("organisation/1/name"): "test_organisation_name",
        }
        self.user_id = 2879730333
        expected_write_data = json.dumps(
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": "dummy_model_vcioluoffl/42",
                        "fields": {"dummy_field_Ugh8joom0a": "IeLahru6oa"},
                    },
                ],
                "information": {"dummy_model_vcioluoffl/42": ["Object updated"]},
                "user_id": self.user_id,
                "locked_fields": {},
            }
        )
        application = create_test_application(
            user_id=self.user_id,
            view_name="ActionView",
            superuser=self.user_id,
            datastore_content=self.datastore_content,
            expected_write_data=expected_write_data,
        )
        client = Client(application, ResponseWrapper)
        response = client.post(
            "/",
            json=[
                {
                    "action": "dummy_model_vcioluoffl.update",
                    "data": [{"id": 42, "dummy_field_Ugh8joom0a": "IeLahru6oa"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_delete(self) -> None:
        self.datastore_content = {
            get_fqfield("organisation/1/name"): "test_organisation_name",
        }
        self.user_id = 2879730333
        expected_write_data = json.dumps(
            {
                "events": [{"type": "delete", "fqid": "dummy_model_vcioluoffl/42"}],
                "information": {"dummy_model_vcioluoffl/42": ["Object deleted"]},
                "user_id": self.user_id,
                # "locked_fields": {"dummy_model_vcioluoffl/42": 1},
                "locked_fields": {},
            }
        )
        application = create_test_application(
            user_id=self.user_id,
            view_name="ActionView",
            superuser=self.user_id,
            datastore_content=self.datastore_content,
            expected_write_data=expected_write_data,
        )
        client = Client(application, ResponseWrapper)
        response = client.post(
            "/",
            json=[{"action": "dummy_model_vcioluoffl.delete", "data": [{"id": 42}]}],
        )
        self.assertEqual(response.status_code, 200)
