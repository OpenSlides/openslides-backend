from typing import Any
from unittest.mock import patch

import pytest

from openslides_backend.action.action_handler import ActionHandler
from openslides_backend.action.util.typing import ActionsResponseResults, Payload
from openslides_backend.shared.interfaces.write_request import WriteRequest
from tests.system.action.base import BaseActionTestCase

# will be written to the datastore between loading the example data and executing the payload
ADDITIONAL_MODELS = {}
# change payload according to your needs
PAYLOAD: Payload = [
    {
        "action": "topic.create",
        "data": [
            {
                "meeting_id": 1,
                "title": "test",
            }
        ],
    },
]


class CreateEventsHelper(BaseActionTestCase):
    @pytest.mark.skip()
    def test_create_events(self) -> None:
        """
        Remove the skip decorator and adjust the payload and datastore content for your needs to
        create events from actions on the basis of the example data. Call pytest with the -s flag to
        see the output.
        """
        self.load_example_data()
        if ADDITIONAL_MODELS:
            self.set_models(ADDITIONAL_MODELS)

        # patch handler to output write requests
        orig_parse_actions = ActionHandler.parse_actions

        def mock_parse_actions(
            *args: Any, **kwargs: Any
        ) -> tuple[list[WriteRequest], ActionsResponseResults]:
            write_requests, results = orig_parse_actions(*args, **kwargs)
            for write_request in write_requests:
                print(write_request.events)
            return write_requests, results

        with patch.object(ActionHandler, "parse_actions", mock_parse_actions):
            print()
            for payload in PAYLOAD:
                print(payload["action"])
                response = self.request_json([payload])
                self.assert_status_code(response, 200)
                print()
