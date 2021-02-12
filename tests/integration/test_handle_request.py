from unittest.mock import MagicMock

from openslides_backend.action.action import Action
from openslides_backend.action.action_handler import ActionHandler
from openslides_backend.action.util.register import register_action


@register_action("success_action")
class SuccessAction(Action):
    model = MagicMock()
    schema = {}  # type: ignore


@register_action("action_with_action_result")
class ActionWithActionResult(Action):
    model = MagicMock()
    schema = {}  # type: ignore


@register_action("error_action")
class ErrorAction(Action):
    model = MagicMock()
    schema = {}  # type: ignore


@register_action("error_on_second_call_action")
class ErrorOnSecondCallAction(Action):
    model = MagicMock()
    schema = {}  # type: ignore


def get_test_handler() -> ActionHandler:
    services = MagicMock()
    datastore_mock = MagicMock()
    datastore_mock.write = MagicMock()
    services.datastore = MagicMock(return_value=datastore_mock)

    return ActionHandler(services, MagicMock())
