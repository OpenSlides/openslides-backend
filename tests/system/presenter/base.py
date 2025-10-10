from collections import defaultdict
from typing import Any

from openslides_backend.http.application import OpenSlidesBackendWSGIApplication
from openslides_backend.http.views.presenter_view import PresenterView
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_presenter_test_application, get_route_path
from openslides_backend.action.util.typing import ActionResults, Payload

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
        self, user1: int, user2: int, base: int = 1
    ) -> None:
        """
        Creates meeting with id 1, committee 60 and groups with ids 1, 2, 3 by default.
        With base you can setup other meetings, but be cautious because of group-ids
        The groups have no permissions and no users by default.
        Uses usernumber to create meeting users with the concatenation of base and usernumber.
        """
        committee_id = base + 59
        self.set_models(
            {
                f"meeting/{base}": {
                    "default_group_id": base,
                    "admin_group_id": base + 1,
                    "committee_id": committee_id,
                    "is_active_in_organization_id": 1,
                    "motions_default_workflow_id": base,
                    "motions_default_amendment_workflow_id": base,
                    "reference_projector_id": base,
                },
                f"projector/{base}": {
                    "meeting_id": base,
                    # **{field: base for field in Meeting.reverse_default_projectors()},
                },
                f"group/{base}": {"meeting_id": base, "name": f"group{base}"},
                f"group/{base+1}": {"meeting_id": base, "name": f"group{base+1}"},
                f"group/{base+2}": {"meeting_id": base, "name": f"group{base+2}"},
                f"motion_workflow/{base}": {
                    "name": "flo",
                    "meeting_id": base,
                    "first_state_id": base,
                },
                f"motion_state/{base}": {
                    "name": "stasis",
                    "weight": 36,
                    "meeting_id": base,
                    "workflow_id": base,
                },
                f"committee/{committee_id}": {
                    # "organization_id": 1,
                    "name": f"Commitee{committee_id}",
                },
                "organization/1": {
                    "limit_of_meetings": 0,
                    "enable_electronic_voting": True,
                },
                f"meeting_user/{base}{user1}": {"user_id": user1, "meeting_id": base},
                f"meeting_user/{base}{user2}": {"user_id": user2, "meeting_id": base},
            }
        )

    def move_user_to_group(self, meeting_user_to_groups: dict[int, Any]) -> None:
        """
        Sets the users groups, returns the meeting_user_ids
        Be careful as it does not reset previously set groups if the related meeting
        users are not in meeting_user_to_groups.
        """
        groups_to_meeting_user = defaultdict(list)
        for meeting_user_id, group_id in meeting_user_to_groups.items():
            if group_id:
                self.update_model(
                    f"meeting_user/{meeting_user_id}", {"group_ids": [group_id]}
                )
                groups_to_meeting_user[group_id].append(meeting_user_id)
            else:
                self.update_model(
                    f"meeting_user/{meeting_user_id}", {"group_ids": None}
                )
        for group_id, meeting_user_ids in groups_to_meeting_user.items():
            self.update_model(
                f"group/{group_id}", {"meeting_user_ids": meeting_user_ids}
            )
