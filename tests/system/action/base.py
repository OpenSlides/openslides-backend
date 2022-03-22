from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Optional, Union, cast
from unittest.mock import MagicMock

from openslides_backend.action.relations.relation_manager import RelationManager
from openslides_backend.action.util.actions_map import actions_map
from openslides_backend.action.util.crypto import get_random_string
from openslides_backend.action.util.typing import ActionResults, Payload
from openslides_backend.http.views.action_view import ActionView
from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permission
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.services.datastore.with_database_context import (
    with_database_context,
)
from openslides_backend.shared.exceptions import DatastoreException
from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from openslides_backend.shared.patterns import Collection
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_action_test_application, get_route_path
from tests.util import Response

DEFAULT_PASSWORD = "password"
ACTION_URL = get_route_path(ActionView.action_route)


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
            assert results[0] is None or len(results[0]) == len(data)
        return response

    def request_json(self, payload: Payload, anonymous: bool = False) -> Response:
        client = self.client if not anonymous else self.anon_client
        return client.post(ACTION_URL, json=payload)

    def execute_action_internally(
        self, action_name: str, data: Dict[str, Any], user_id: int = 0
    ) -> Optional[ActionResults]:
        """
        Shorthand to execute an action internally where all permissions etc. are ignored.
        Useful when an action is just execute for the end result and not for testing it.
        """
        ActionClass = actions_map[action_name]
        action = ActionClass(
            self.services, self.datastore, RelationManager(self.datastore), MagicMock()
        )
        action_data = deepcopy(data)
        with self.datastore.get_database_context():
            write_request, result = action.perform(
                [action_data], user_id, internal=True
            )
        if write_request:
            self.datastore.write(write_request)
        self.datastore.reset()
        return result

    def create_meeting(self, base: int = 1) -> None:
        """
        Creates meeting with id 1, committee 60 and groups with ids 1, 2, 3 by default.
        With base you can setup other meetings, but be cautious because of group-ids
        The groups have no permissions and no users by default.
        """
        committee_id = base + 59
        self.set_models(
            {
                f"meeting/{base}": {
                    "group_ids": [base, base + 1, base + 2],
                    "default_group_id": base,
                    "admin_group_id": base + 1,
                    "motions_default_workflow_id": base,
                    "committee_id": committee_id,
                    "is_active_in_organization_id": 1,
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
                f"motion_workflow/{base}": {
                    "meeting_id": base,
                    "default_workflow_meeting_id": base,
                    "state_ids": [base],
                    "first_state_id": base,
                },
                f"motion_state/{base}": {
                    "meeting_id": base,
                    "workflow_id": base,
                    "first_state_of_workflow_id": base,
                },
                f"committee/{committee_id}": {
                    "organization_id": 1,
                    "name": f"Commitee{committee_id}",
                    "meeting_ids": [base],
                },
                "organization/1": {
                    "limit_of_meetings": 0,
                    "active_meeting_ids": [base],
                    "enable_electronic_voting": True,
                },
            }
        )

    def set_anonymous(self, enable: bool = True, meeting_id: int = 1) -> None:
        self.set_models({f"meeting/{meeting_id}": {"enable_anonymous": enable}})

    def set_organization_management_level(
        self, level: Optional[OrganizationManagementLevel], user_id: int = 1
    ) -> None:
        self.update_model(f"user/{user_id}", {"organization_management_level": level})

    def set_committee_management_level(
        self, committee_ids: List[int], user_id: int = 1
    ) -> None:
        d1 = {
            "committee_ids": committee_ids,
            "committee_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
            "committee_$can_manage_management_level": committee_ids,
        }

        self.set_models({f"user/{user_id}": d1})

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
        organization_management_level: Optional[OrganizationManagementLevel] = None,
    ) -> int:
        """
        Create a user with the given username, groups and organization management level.
        """
        partitioned_groups = self._fetch_groups(group_ids)
        id = self.datastore.reserve_id(Collection("user"))
        self.set_models(
            {
                f"user/{id}": {
                    "username": username,
                    "organization_management_level": organization_management_level,
                    "is_active": True,
                    "default_password": DEFAULT_PASSWORD,
                    "password": self.auth.hash(DEFAULT_PASSWORD),
                    "group_$_ids": list(
                        str(meeting_id) for meeting_id in partitioned_groups.keys()
                    ),
                    "meeting_ids": list(partitioned_groups.keys()),
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

    def create_user_for_meeting(self, meeting_id: int) -> int:
        meeting = self.get_model(f"meeting/{meeting_id}")
        if not meeting.get("default_group_id"):
            id = self.datastore.reserve_id(Collection("group"))
            self.set_models(
                {
                    f"meeting/{meeting_id}": {
                        "group_ids": meeting.get("group_ids", []) + [id],
                        "default_group_id": id,
                    },
                    f"group/{id}": {
                        "meeting_id": meeting_id,
                        "default_group_for_meeting_id": meeting_id,
                    },
                }
            )
            meeting["default_group_id"] = id
        user_id = self.create_user("user_" + get_random_string(6))
        self.set_user_groups(user_id, [meeting["default_group_id"]])
        self.update_model(
            f"meeting/{meeting_id}",
            {"user_ids": list(set(meeting.get("user_ids", []) + [user_id]))},
        )
        return user_id

    def set_user_groups(self, user_id: int, group_ids: List[int]) -> None:
        assert isinstance(group_ids, list)
        partitioned_groups = self._fetch_groups(group_ids)
        try:
            user = self.get_model(f"user/{user_id}")
        except DatastoreException:
            user = {}
        new_group_ids = list(
            set(
                user.get("group_$_ids", [])
                + [str(meeting_id) for meeting_id in partitioned_groups.keys()]
            )
        )
        self.set_models(
            {
                f"user/{user_id}": {
                    "group_$_ids": new_group_ids,
                    "meeting_ids": [int(group_id) for group_id in new_group_ids],
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
        self.vote_service.set_authentication(self.client.headers, self.client.cookies)

    @with_database_context
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
            ],
            lock_result=False,
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
        permission: Optional[Union[Permission, OrganizationManagementLevel]] = None,
    ) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        if permission:
            if type(permission) == OrganizationManagementLevel:
                self.set_organization_management_level(
                    cast(OrganizationManagementLevel, permission), self.user_id
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
            self.assertIn(
                f"You are not allowed to perform action {action}",
                response.json["message"],
            )
