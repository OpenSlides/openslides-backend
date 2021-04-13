from collections import defaultdict
from typing import Any, Dict, List, Optional, Union, cast

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

DEFAULT_PASSWORD = "password"


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

    def create_meeting(self, base: int = 1) -> None:
        """
        Creates meeting with id 1 and groups with ids 1, 2, 3 by default.
        With base you can setup other meetings, but be cautious because of group-ids
        The groups have no permissions and no users by default.
        """
        self.set_models(
            {
                f"meeting/{base}": {
                    "group_ids": [base, base + 1, base + 2],
                    "default_group_id": base,
                    "admin_group_id": base + 1,
                },
                f"group/{base}": {
                    "meeting_id": base,
                    "default_group_for_meeting_id": base,
                },
                f"group/{base+1}": {
                    "meeting_id": base,
                    "admin_group_for_meeting_id": base,
                },
                f"group/{base+2}": {
                    "meeting_id": base,
                },
            }
        )

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
        partitioned_groups = self._fetch_groups(group_ids)
        id = self.datastore.reserve_id(Collection("user"))
        self.set_models(
            {
                f"user/{id}": {
                    "username": username,
                    "organisation_management_level": organisation_management_level,
                    "is_active": True,
                    "default_password": DEFAULT_PASSWORD,
                    "password": self.auth.hash(DEFAULT_PASSWORD),
                    "group_$_ids": list(
                        str(meeting_id) for meeting_id in partitioned_groups.keys()
                    ),
                    **{
                        f"group_${meeting_id}_ids": [group["id"] for group in groups]
                        for meeting_id, groups in partitioned_groups.items()
                    },
                },
                **{
                    f"group/{group['id']}": {
                        "user_ids": list(set(group.get("user_ids", []) + [id]))
                    }
                    for groups in partitioned_groups.values()
                    for group in groups
                },
            }
        )
        return id

    def set_user_groups(self, user_id: int, group_ids: List[int]) -> None:
        partitioned_groups = self._fetch_groups(group_ids)
        user = self.get_model(f"user/{user_id}")
        self.set_models(
            {
                f"user/{user_id}": {
                    "group_$_ids": list(
                        str(meeting_id)
                        for meeting_id in set(
                            user.get("group_$_ids", [])
                            + list(partitioned_groups.keys())
                        )
                    ),
                    **{
                        f"group_${meeting_id}_ids": list(
                            set(
                                [group["id"] for group in groups]
                                + user.get(f"group_${meeting_id}_ids", []),
                            )
                        )
                        for meeting_id, groups in partitioned_groups.items()
                    },
                },
                **{
                    f"group/{group['id']}": {
                        "user_ids": list(set(group.get("user_ids", []) + [user_id]))
                    }
                    for groups in partitioned_groups.values()
                    for group in groups
                },
            }
        )

    def login(self, user_id: int) -> None:
        """
        Login the given user by fetching the default password from the datastore.
        """
        user = self.get_model(f"user/{user_id}")
        assert user.get("default_password")
        self.client.login(user["username"], user["default_password"])

    def _fetch_groups(self, group_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        """
        Helper method to partition the groups by their meeting id.
        """
        if not group_ids:
            return {}

        response = self.datastore.get_many(
            [
                GetManyRequest(
                    Collection("group"), group_ids, ["id", "meeting_id", "user_ids"]
                )
            ]
        )
        partitioned_groups: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for group in response.get(Collection("group"), {}).values():
            partitioned_groups[group["meeting_id"]].append(group)
        return partitioned_groups

    def base_permission_test(
        self,
        models: Dict[str, Any],
        action: str,
        action_data: Dict[str, Any],
        permission: Optional[Union[Permission, OrganisationManagementLevel]] = None,
    ) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        if permission:
            if type(permission) == OrganisationManagementLevel:
                self.set_management_level(
                    cast(OrganisationManagementLevel, permission), self.user_id
                )
            else:
                self.set_group_permissions(3, [cast(Permission, permission)])
        if models:
            self.set_models(models)
        response = self.request(action, action_data)
        if permission:
            self.assert_status_code(response, 200)
        else:
            self.assert_status_code(response, 403)
            assert "Missing permission:" in response.json["message"]
