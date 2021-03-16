from collections import defaultdict
from typing import Any, Dict, List, Optional

from openslides_backend.action.util.typing import Payload
from openslides_backend.permissions.permissions import (
    OrganisationManagementLevel,
    Permission,
)
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from openslides_backend.shared.patterns import Collection
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_action_test_application
from tests.util import Response


class BaseActionTestCase(BaseSystemTestCase):
    def get_application(self) -> WSGIApplication:
        return create_action_test_application()

    def request(
        self, action: str, data: Dict[str, Any], anonymous: bool = False
    ) -> Response:
        return self.request_multi(action, [data], anonymous=anonymous)

    def request_multi(
        self, action: str, data: List[Dict[str, Any]], anonymous: bool = False
    ) -> Response:
        response = self.request_json(
            [
                {
                    "action": action,
                    "data": data,
                }
            ],
            anonymous=anonymous,
        )
        if response.status_code == 200:
            results = response.json.get("results", [])
            assert len(results) == 1
            assert len(results[0]) == len(data)
        return response

    def request_json(self, payload: Payload, anonymous: bool = False) -> Response:
        client = self.client if not anonymous else self.anon_client
        return client.post("/", json=payload)

    def create_meeting(self) -> None:
        self.set_models({"committee/1": {}})
        response = self.request(
            "meeting.create",
            {
                "committee_id": 1,
                "name": "test",
                "welcome_title": "title",
            },
        )
        self.assert_status_code(response, 200)

    def set_anonymous(self, enable: bool = True, meeting_id: int = 1) -> None:
        self.set_models({f"meeting/{meeting_id}": {"enable_anonymous": enable}})

    def set_management_level(
        self, level: Optional[OrganisationManagementLevel], user_id: int = 1
    ) -> None:
        self.update_model(f"user/{user_id}", {"organisation_management_level": level})

    def add_group_permissions(
        self, group_id: int, permissions: List[Permission]
    ) -> None:
        group = self.get_model(f"group/{group_id}")
        self.set_group_permissions(group_id, group.get("permissions", []) + permissions)

    def remove_group_permissions(
        self, group_id: int, permissions: List[Permission]
    ) -> None:
        group = self.get_model(f"group/{group_id}")
        new_perms = [p for p in group.get("permissions", []) if p not in permissions]
        self.set_group_permissions(group_id, new_perms)

    def set_group_permissions(
        self, group_id: int, permissions: List[Permission]
    ) -> None:
        self.update_model(f"group/{group_id}", {"permissions": permissions})

    def create_user(
        self,
        username: str,
        group_ids: List[int] = [],
        organisation_management_level: Optional[OrganisationManagementLevel] = None,
    ) -> int:
        """
        Create a user with the given username, groups and organisation management level.
        """
        partitioned_group_ids = self._fetch_groups(group_ids)
        response = self.request(
            "user.create",
            {
                "username": username,
                "group_$_ids": partitioned_group_ids,
                "organisation_management_level": organisation_management_level,
                "is_active": True,
            },
        )
        self.assert_status_code(response, 200)
        # save newly created id
        id = response.json["results"][0][0]["id"]
        # set password
        # TODO: remove this once the password is set automatically in user.create
        response = self.request(
            "user.set_password",
            {"id": id, "password": "password", "set_as_default": True},
        )
        self.assert_status_code(response, 200)
        return id

    def set_user_groups(self, user_id: int, group_ids: List[int]) -> None:
        partitioned_group_ids = self._fetch_groups(group_ids)
        response = self.request(
            "user.update",
            {
                "id": user_id,
                "group_$_ids": {
                    meeting_id: groups
                    for meeting_id, groups in partitioned_group_ids.items()
                },
            },
        )
        self.assert_status_code(response, 200)

    def login(self, user_id: int) -> None:
        """
        Login the given user by fetching the default password from the datastore.
        """
        user = self.get_model(f"user/{user_id}")
        assert user.get("default_password")
        self.client.login(user["username"], user["default_password"])

    def _fetch_groups(self, group_ids: List[int]) -> Dict[int, List[int]]:
        """
        Helper method to partition the groups by their meeting id.
        """
        if not group_ids:
            return {}

        response = self.datastore.get_many(
            [GetManyRequest(Collection("group"), group_ids, ["meeting_id"])]
        )
        partitioned_group_ids: Dict[int, List[int]] = defaultdict(list)
        for id, group in response.get(Collection("group"), {}).items():
            partitioned_group_ids[group["meeting_id"]].append(id)
        return partitioned_group_ids
