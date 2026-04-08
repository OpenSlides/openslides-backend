from typing import Any

from openslides_backend.http.application import OpenSlidesBackendWSGIApplication
from openslides_backend.http.views.presenter_view import PresenterView
from openslides_backend.services.database.interface import PartialModel
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_presenter_test_application, get_route_path

PRESENTER_URL = get_route_path(PresenterView.presenter_route)


class BasePresenterTestCase(BaseSystemTestCase):
    def get_application(self) -> OpenSlidesBackendWSGIApplication:
        return create_presenter_test_application()

    def request(
        self, presenter: str, data: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        """
        Requests a single presenter and returns the status code and the json decoded
        response. Automatically removes array around response data.
        """
        payload: dict[str, Any] = {"presenter": presenter}
        if data is not None:
            payload["data"] = data
        response = self.client.post(PRESENTER_URL, json=[payload])
        if isinstance(response.json, list) and len(response.json) == 1:
            return (response.status_code, response.json[0])
        return (response.status_code, response.json)

    def create_meeting_for_two_users(
        self, base: int, user1: int, user2: int, meeting_data: PartialModel = {}
    ) -> None:
        """
        Creates meeting with the given base id together with the required related models
        including 3 groups.
        By setting different base you can create multiple meetings,
        but be cautious because of group-ids.
        Uses usernumber to create meeting users with the concatenation of base and usernumber.
        """
        self.create_meeting(base, meeting_data=meeting_data)
        mu1 = int(f"{base}{user1}")
        mu2 = int(f"{base}{user2}")
        self.set_models(
            {
                f"meeting_user/{mu1}": {"user_id": user1, "meeting_id": base},
                f"meeting_user/{mu2}": {"user_id": user2, "meeting_id": base},
                f"group/{base}": {"meeting_user_ids": [mu1, mu2]},
            }
        )

    def move_users_to_groups(
        self, user_to_groups: dict[int, list[int]]
    ) -> dict[int, list[int]]:
        """
        Sets the users groups, returns the meeting_user_ids for each given user.
        """
        return {
            user_id: self.set_user_groups(user_id, group_ids)
            for user_id, group_ids in user_to_groups.items()
        }
