from collections import defaultdict
from copy import deepcopy
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from openslides_backend.action.action_handler import ActionHandler
from openslides_backend.action.action_worker import gunicorn_post_request
from openslides_backend.action.relations.relation_manager import RelationManager
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.actions_map import actions_map
from openslides_backend.action.util.crypto import get_random_string
from openslides_backend.action.util.typing import ActionResults, Payload
from openslides_backend.http.application import OpenSlidesBackendWSGIApplication
from openslides_backend.http.views.action_view import ActionView
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permission
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.services.datastore.with_database_context import (
    with_database_context,
)
from openslides_backend.shared.exceptions import AuthenticationException
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.patterns import FullQualifiedId
from openslides_backend.shared.typing import HistoryInformation
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.util import get_internal_auth_header
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_action_test_application, get_route_path
from tests.util import Response

from .mock_gunicorn_gthread_worker import MockGunicornThreadWorker

DEFAULT_PASSWORD = "password"
ACTION_URL = get_route_path(ActionView.action_route)
ACTION_URL_INTERNAL = get_route_path(ActionView.internal_action_route)
ACTION_URL_SEPARATELY = get_route_path(ActionView.action_route, "handle_separately")


class BaseActionTestCase(BaseSystemTestCase):
    def setUp(self) -> None:
        super().setUp()
        ActionHandler.MAX_RETRY = 1

    def reset_redis(self) -> None:
        # access auth database directly to reset it
        redis = self.auth.auth_handler.database.redis
        prefix = ":".join(
            (
                self.auth.auth_handler.database.AUTH_PREFIX,
                self.auth.auth_handler.TOKEN_DB_KEY,
            )
        )
        for key in redis.keys():
            if key.decode().startswith(prefix):
                redis.delete(key)

    def get_application(self) -> OpenSlidesBackendWSGIApplication:
        return create_action_test_application()

    def request(
        self,
        action: str,
        data: dict[str, Any],
        anonymous: bool = False,
        lang: str | None = None,
        internal: bool | None = None,
    ) -> Response:
        return self.request_multi(
            action,
            [data],
            anonymous=anonymous,
            lang=lang,
            internal=internal,
        )

    def request_multi(
        self,
        action: str,
        data: list[dict[str, Any]],
        anonymous: bool = False,
        lang: str | None = None,
        internal: bool | None = None,
    ) -> Response:
        ActionClass = actions_map.get(action)
        if internal is None:
            internal = bool(
                ActionClass and ActionClass.action_type != ActionType.PUBLIC
            )
        response = self.request_json(
            [
                {
                    "action": action,
                    "data": data,
                }
            ],
            anonymous=anonymous,
            lang=lang,
            internal=internal,
        )
        if response.status_code == 200:
            results = response.json.get("results", [])
            assert len(results) == 1
            assert results[0] is None or len(results[0]) == len(data)
        return response

    def request_json(
        self,
        payload: Payload,
        anonymous: bool = False,
        lang: str | None = None,
        internal: bool = False,
        atomic: bool = True,
    ) -> Response:
        client = self.client if not anonymous else self.anon_client
        headers = {}
        if lang:
            headers["Accept-Language"] = lang
        if internal and atomic:
            url = ACTION_URL_INTERNAL
            headers.update(get_internal_auth_header())
        elif atomic:
            url = ACTION_URL
        elif not internal:
            url = ACTION_URL_SEPARATELY
        else:
            raise NotImplementedError("Cannot send internal non-atomic requests.")
        response = client.post(url, json=payload, headers=headers)
        if response.status_code == 202:
            gunicorn_post_request(
                MockGunicornThreadWorker(),
                None,  # type: ignore
                None,  # type: ignore
                response,
            )
        return response

    def execute_action_internally(
        self, action_name: str, data: dict[str, Any], user_id: int = 0
    ) -> ActionResults | None:
        """
        Shorthand to execute an action internally where all permissions etc. are ignored.
        Useful when an action is just execute for the end result and not for testing it.
        """
        ActionClass = actions_map[action_name]
        action = ActionClass(
            self.services,
            self.datastore,
            RelationManager(self.datastore),
            MagicMock(),
            MagicMock(),
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

    def create_committee(
        self, committee_id: int = 1, parent_id: int | None = None
    ) -> None:
        committee_fqid = f"committee/{committee_id}"
        data: dict[str, dict[str, Any]] = {
            committee_fqid: {
                "organization_id": 1,
                "name": f"Commitee{committee_id}",
            }
        }
        if parent_id:
            parent_fqid = f"committee/{parent_id}"
            parent = self.datastore.get(
                parent_fqid,
                ["all_parent_ids", "all_child_ids", "child_ids"],
                lock_result=False,
            )
            data[parent_fqid] = {
                "child_ids": [*parent.get("child_ids", []), committee_id],
                "all_child_ids": [*parent.get("all_child_ids", []), committee_id],
            }
            data[committee_fqid]["parent_id"] = parent_id
            data[committee_fqid]["all_parent_ids"] = [
                *parent.get("all_parent_ids", []),
                parent_id,
            ]
            if grandparent_ids := parent.get("all_parent_ids", []):
                grandparents = self.datastore.get_many(
                    [GetManyRequest("committee", grandparent_ids, ["all_child_ids"])],
                    lock_result=False,
                ).get("committee", {})
                data.update(
                    {
                        f"committee/{id_}": {
                            "all_child_ids": [
                                *grandparents.get(id_, {}).get("all_child_ids", []),
                                committee_id,
                            ]
                        }
                        for id_ in grandparent_ids
                    }
                )
        self.set_models(data)

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
                    "language": "en",
                    "motion_state_ids": [base],
                    "motion_workflow_ids": [base],
                },
                f"group/{base}": {
                    "meeting_id": base,
                    "default_group_for_meeting_id": base,
                    "name": f"group{base}",
                },
                f"group/{base+1}": {
                    "meeting_id": base,
                    "admin_group_for_meeting_id": base,
                    "name": f"group{base+1}",
                },
                f"group/{base+2}": {
                    "meeting_id": base,
                    "name": f"group{base+2}",
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
                ONE_ORGANIZATION_FQID: {
                    "limit_of_meetings": 0,
                    "active_meeting_ids": [base],
                    "enable_electronic_voting": True,
                },
            }
        )

    def set_anonymous(
        self,
        enable: bool = True,
        meeting_id: int = 1,
        permissions: list[Permission] = [],
    ) -> int:
        """Also creates an anonymous group at the next-highest free group_id"""
        next_group_id = self.datastore.reserve_id("group")
        group_ids = self.get_model(f"meeting/{meeting_id}").get("group_ids", [])
        self.set_models(
            {
                f"meeting/{meeting_id}": {
                    "enable_anonymous": enable,
                    "group_ids": [*group_ids, next_group_id],
                    "anonymous_group_id": next_group_id,
                },
                f"group/{next_group_id}": {
                    "name": "Anonymous",
                    "meeting_id": meeting_id,
                    "anonymous_group_for_meeting_id": meeting_id,
                    "permissions": permissions,
                },
            }
        )
        return next_group_id

    def set_organization_management_level(
        self, level: OrganizationManagementLevel | None, user_id: int = 1
    ) -> None:
        self.update_model(f"user/{user_id}", {"organization_management_level": level})

    def set_committee_management_level(
        self, committee_ids: list[int], user_id: int = 1
    ) -> None:
        d1 = {
            "committee_ids": committee_ids,
            "committee_management_ids": committee_ids,
        }

        self.set_models({f"user/{user_id}": d1})

    def add_group_permissions(
        self, group_id: int, permissions: list[Permission]
    ) -> None:
        group = self.get_model(f"group/{group_id}")
        self.set_group_permissions(group_id, group.get("permissions", []) + permissions)

    def remove_group_permissions(
        self, group_id: int, permissions: list[Permission]
    ) -> None:
        group = self.get_model(f"group/{group_id}")
        new_perms = [p for p in group.get("permissions", []) if p not in permissions]
        self.set_group_permissions(group_id, new_perms)

    def set_group_permissions(
        self, group_id: int, permissions: list[Permission]
    ) -> None:
        self.update_model(f"group/{group_id}", {"permissions": permissions})

    def create_user(
        self,
        username: str,
        group_ids: list[int] = [],
        organization_management_level: OrganizationManagementLevel | None = None,
    ) -> int:
        """
        Create a user with the given username, groups and organization management level.
        """
        partitioned_groups = self._fetch_groups(group_ids)
        id = 1
        while f"user/{id}" in self.created_fqids:
            id += 1
        self.set_models(
            {
                f"user/{id}": self._get_user_data(
                    username, partitioned_groups, organization_management_level
                ),
            }
        )
        self.set_user_groups(id, group_ids)
        return id

    def _get_user_data(
        self,
        username: str,
        partitioned_groups: dict[int, list[dict[str, Any]]] = {},
        organization_management_level: OrganizationManagementLevel | None = None,
    ) -> dict[str, Any]:
        return {
            "username": username,
            "organization_management_level": organization_management_level,
            "is_active": True,
            "default_password": DEFAULT_PASSWORD,
            "password": self.auth.hash(DEFAULT_PASSWORD),
            "meeting_ids": list(partitioned_groups.keys()),
        }

    def create_user_for_meeting(self, meeting_id: int) -> int:
        meeting = self.get_model(f"meeting/{meeting_id}")
        if not meeting.get("default_group_id"):
            id = self.datastore.reserve_id("group")
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

    @with_database_context
    def set_user_groups(self, user_id: int, group_ids: list[int]) -> list[int]:
        """
        Sets the users groups, returns the meeting_user_ids
        """
        assert isinstance(group_ids, list)
        groups = self.datastore.get_many(
            [
                GetManyRequest(
                    "group",
                    group_ids,
                    ["id", "meeting_id", "meeting_user_ids"],
                )
            ],
            lock_result=False,
        )["group"]
        meeting_ids: list[int] = list({v["meeting_id"] for v in groups.values()})
        filtered_result = self.datastore.filter(
            "meeting_user",
            FilterOperator("user_id", "=", user_id),
            ["id", "user_id", "meeting_id", "group_ids"],
            lock_result=False,
        )
        meeting_users: dict[int, dict[str, Any]] = {
            data["meeting_id"]: dict(data)
            for data in filtered_result.values()
            if data["meeting_id"] in meeting_ids
        }
        last_meeting_user_id = max(
            [
                int(k[1])
                for key in self.created_fqids
                if (k := key.split("/"))[0] == "meeting_user"
            ]
            or [0]
        )
        meeting_users_new = {
            meeting_id: {
                "id": (last_meeting_user_id := last_meeting_user_id + 1),  # noqa: F841
                "user_id": user_id,
                "meeting_id": meeting_id,
                "group_ids": [],
            }
            for meeting_id in meeting_ids
            if meeting_id not in meeting_users
        }
        meeting_users.update(meeting_users_new)
        meetings = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    meeting_ids,
                    ["id", "meeting_user_ids", "user_ids"],
                )
            ],
            lock_result=False,
        )["meeting"]
        user = self.datastore.get(
            f"user/{user_id}",
            ["user_meeting_ids", "meeting_ids"],
            lock_result=False,
            use_changed_models=False,
        )

        def add_to_list(where: dict[str, Any], key: str, what: int) -> None:
            if key in where and where.get(key):
                if what not in where[key]:
                    where[key].append(what)
            else:
                where[key] = [what]

        for group in groups.values():
            meeting_id = group["meeting_id"]
            meeting_user_id = meeting_users[meeting_id]["id"]
            meetings[meeting_id]["id"] = meeting_id
            add_to_list(meeting_users[meeting_id], "group_ids", group["id"])
            add_to_list(group, "meeting_user_ids", meeting_user_id)
            add_to_list(meetings[meeting_id], "meeting_user_ids", meeting_user_id)
            add_to_list(meetings[meeting_id], "user_ids", user_id)
            add_to_list(user, "meeting_user_ids", meeting_user_id)
            add_to_list(user, "meeting_ids", meeting_id)
        self.set_models(
            {
                f"user/{user_id}": user,
                **{f"meeting_user/{mu['id']}": mu for mu in meeting_users.values()},
                **{f"group/{group['id']}": group for group in groups.values()},
                **{
                    f"meeting/{meeting['id']}": meeting for meeting in meetings.values()
                },
            }
        )
        return [mu["id"] for mu in meeting_users.values()]

    @with_database_context
    def _fetch_groups(self, group_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
        """
        Helper method to partition the groups by their meeting id.
        """
        if not group_ids:
            return {}

        response = self.datastore.get_many(
            [
                GetManyRequest(
                    "group",
                    group_ids,
                    ["id", "meeting_id", "user_ids"],
                )
            ],
            lock_result=False,
        )
        partitioned_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for group in response.get("group", {}).values():
            partitioned_groups[group["meeting_id"]].append(group)
        return partitioned_groups

    def base_permission_test(
        self,
        models: dict[str, dict[str, Any]],
        action: str,
        action_data: dict[str, Any],
        permission: (
            Permission | list[Permission] | OrganizationManagementLevel | None
        ) = None,
        fail: bool | None = None,
        lock_meeting: bool = False,
        lock_out_calling_user: bool = False,
    ) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        if models:
            self.set_models(models)
        if lock_meeting:
            self.set_models({"meeting/1": {"locked_from_inside": True}})
        meeting_user_id = self.set_user_groups(self.user_id, [3])[0]
        if lock_out_calling_user:
            self.set_models({f"meeting_user/{meeting_user_id}": {"locked_out": True}})
        if permission:
            if isinstance(permission, OrganizationManagementLevel):
                self.set_organization_management_level(permission, self.user_id)
            elif isinstance(permission, list):
                self.set_group_permissions(3, permission)
            else:
                self.set_group_permissions(3, [permission])
        response = self.request(action, action_data)
        if fail is None:
            fail = not permission
        if fail:
            self.assert_status_code(response, 403)
            self.assertIn(
                f"You are not allowed to perform action {action}",
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)

    def base_locked_out_superadmin_permission_test(
        self,
        models: dict[str, dict[str, Any]],
        action: str,
        action_data: dict[str, Any],
    ) -> None:
        self.base_permission_test(
            models,
            action,
            action_data,
            OrganizationManagementLevel.SUPERADMIN,
            True,
            True,
        )

    @with_database_context
    def assert_history_information(
        self, fqid: FullQualifiedId, information: list[str] | None
    ) -> None:
        """
        Asserts that the last history information for the given model is the given information.
        """
        informations = self.datastore.history_information([fqid]).get(fqid)
        last_information = (
            cast(HistoryInformation, informations[-1]["information"])
            if informations
            else {}
        )
        if information is None:
            assert not informations or fqid not in last_information, informations
        else:
            assert informations
            self.assertEqual(last_information[fqid], information)

    @with_database_context
    def assert_history_information_contains(
        self, fqid: FullQualifiedId, information: str
    ) -> None:
        """
        Asserts that the last history information for the given model is the given information.
        """
        informations = self.datastore.history_information([fqid]).get(fqid)
        last_information = (
            cast(HistoryInformation, informations[-1]["information"])
            if informations
            else {}
        )
        assert informations
        assert information in last_information[fqid]

    def assert_logged_in(self) -> None:
        self.auth.authenticate()  # assert that no exception is thrown

    def assert_logged_out(self) -> None:
        with pytest.raises(AuthenticationException):
            self.auth.authenticate()
        BaseSystemTestCase.auth_data = None
