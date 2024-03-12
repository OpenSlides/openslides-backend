import inspect
from unittest import TestCase

from openslides_backend.action.action_set import ActionSet
from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.generics.delete import DeleteAction
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.util.register import register_action_set
from openslides_backend.models.base import Model

dummy_schema: dict = {}


class DummyModelVcioluoffl(Model):
    collection = "dummy_model_vcioluoffl"


@register_action_set("dummy_model_vcioluoffl")
class DummyActionSet_phooth3I(ActionSet):
    model = DummyModelVcioluoffl()
    create_schema = dummy_schema
    update_schema = dummy_schema
    delete_schema = dummy_schema


class ActionSetTester(TestCase):
    def test_dummy_action_set_routes(self) -> None:
        for route, action in DummyActionSet_phooth3I.get_actions().items():
            self.assertIn(
                action.__name__,
                (
                    "DummyModelVcioluofflCreate",
                    "DummyModelVcioluofflUpdate",
                    "DummyModelVcioluofflDelete",
                ),
            )
            self.assertIn(
                route,
                ("create", "update", "delete"),
            )

    def test_dummy_action_set_types(self) -> None:
        for name, action in DummyActionSet_phooth3I.get_actions().items():
            generic_base = inspect.getmro(action)[1]
            self.assertIn(generic_base, (CreateAction, UpdateAction, DeleteAction))
