from typing import Any

import requests
import simplejson as json

from tests.system.util import convert_to_test_response
from tests.util import Response

from .base_poll_test import BasePollTestCase


class BaseVoteTestCase(BasePollTestCase):
    def request(
        self,
        action: str,
        data: dict[str, Any],
        anonymous: bool = False,
        lang: str | None = None,
        internal: bool | None = None,
        start_poll_before_vote: bool = True,
        stop_poll_after_vote: bool = True,
    ) -> Response:
        """Overwrite request method to reroute voting requests to the vote service."""
        if action == "poll.vote":
            if start_poll_before_vote:
                self.execute_action_internally("poll.start", {"id": data["id"]})
            response = self.vote_service.vote(data)
            if stop_poll_after_vote:
                # TODO: fix execute_action_internally to avoid concurrent update error
                # self.execute_action_internally("poll.stop", {"id": data["id"]})
                self.request("poll.stop", {"id": data["id"]}, internal=True)
            return response
        else:
            return super().request(action, data, anonymous, lang, internal)

    def anonymous_vote(self, payload: dict[str, Any], id: int = 1) -> Response:
        # make request manually to prevent sending of cookie & header
        payload_json = json.dumps(payload, separators=(",", ":"))
        response = requests.post(
            url=self.vote_service.url.replace("internal", "system") + f"?id={id}",
            data=payload_json,
            headers={
                "Content-Type": "application/json",
            },
        )
        return convert_to_test_response(response)
