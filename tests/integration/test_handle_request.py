from collections.abc import Iterable
from unittest.mock import MagicMock

import pytest

from openslides_backend.action.action import Action
from openslides_backend.action.action_handler import ActionHandler
from openslides_backend.action.util.register import register_action
from openslides_backend.action.util.typing import ActionData, ActionResults, Payload
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.shared.typing import Schema


class BaseTestAction(Action):
    def perform(
        self,
        action_data: ActionData,
        user_id: int,
        internal: bool = False,
        is_sub_call: bool = False,
    ) -> tuple[WriteRequest | None, ActionResults]:
        return (None, self.mock_perform())

    def mock_perform(self) -> ActionResults:
        return []


@register_action("success_action")
class SuccessAction(BaseTestAction):
    model = MagicMock()
    schema: Schema = {}


@register_action("action_with_result")
class ActionWithResult(BaseTestAction):
    model = MagicMock()
    schema: Schema = {}

    def mock_perform(self) -> ActionResults:
        return [{"id": 1}, {"id": 42}]


@register_action("error_action")
class ErrorAction(BaseTestAction):
    model = MagicMock()
    schema: Schema = {}

    def mock_perform(self) -> ActionResults:
        self.index = -1
        raise ActionException("")


@register_action("error_action_with_index")
class ErrorActionWithIndex(BaseTestAction):
    model = MagicMock()
    schema: Schema = {}

    def mock_perform(self) -> ActionResults:
        self.index = 2
        raise ActionException("")


@pytest.fixture()
def action_handler() -> Iterable[ActionHandler]:
    services = MagicMock()
    datastore_mock = MagicMock()
    datastore_mock.write = MagicMock()
    services.datastore = MagicMock(return_value=datastore_mock)

    yield ActionHandler(MagicMock(), services, MagicMock())


def test_success_actions(action_handler: ActionHandler) -> None:
    payload: Payload = [
        {"action": "success_action", "data": [{}, {}]},
        {"action": "success_action", "data": [{}, {}]},
    ]
    response = action_handler.handle_request(payload, 0)
    assert response["success"] is True
    assert response["results"] == [[], []]


def test_success_actions_atomic(action_handler: ActionHandler) -> None:
    payload: Payload = [
        {"action": "success_action", "data": [{}, {}]},
        {"action": "success_action", "data": [{}, {}]},
    ]
    response = action_handler.handle_request(payload, 0, False)
    assert response["success"] is True
    assert response["results"] == [[], []]


def test_success_actions_with_result(action_handler: ActionHandler) -> None:
    payload: Payload = [
        {"action": "success_action", "data": [{}, {}]},
        {"action": "action_with_result", "data": [{}, {}]},
    ]
    response = action_handler.handle_request(payload, 0)
    assert response["success"] is True
    assert response["results"] == [[], [{"id": 1}, {"id": 42}]]


def test_success_actions_with_result_atomic(action_handler: ActionHandler) -> None:
    payload: Payload = [
        {"action": "success_action", "data": [{}, {}]},
        {"action": "action_with_result", "data": [{}, {}]},
    ]
    response = action_handler.handle_request(payload, 0, False)
    assert response["success"] is True
    assert response["results"] == [[], [{"id": 1}, {"id": 42}]]


def test_with_error(action_handler: ActionHandler) -> None:
    payload: Payload = [
        {"action": "success_action", "data": [{}, {}]},
        {"action": "error_action", "data": [{}, {}]},
    ]
    with pytest.raises(ActionException) as e:
        action_handler.handle_request(payload, 0)
    assert e.value.action_error_index == 1
    assert getattr(e.value, "action_data_error_index", None) is None


def test_with_error_atomic(action_handler: ActionHandler) -> None:
    payload: Payload = [
        {"action": "success_action", "data": [{}, {}]},
        {"action": "error_action", "data": [{}, {}]},
    ]
    response = action_handler.handle_request(payload, 0, False)
    assert response["success"] is True
    assert response["results"] == [[], {"success": False, "message": ""}]


def test_with_error_with_index(action_handler: ActionHandler) -> None:
    payload: Payload = [
        {"action": "success_action", "data": [{}, {}]},
        {"action": "error_action_with_index", "data": [{}, {}]},
    ]
    with pytest.raises(ActionException) as e:
        action_handler.handle_request(payload, 0)
    assert e.value.action_error_index == 1
    assert e.value.action_data_error_index == 2


def test_with_error_with_index_atomic(action_handler: ActionHandler) -> None:
    payload: Payload = [
        {"action": "success_action", "data": [{}, {}]},
        {"action": "error_action_with_index", "data": [{}, {}]},
    ]
    response = action_handler.handle_request(payload, 0, False)
    assert response["success"] is True
    assert response["results"] == [
        [],
        {"success": False, "message": "", "action_data_error_index": 2},
    ]
