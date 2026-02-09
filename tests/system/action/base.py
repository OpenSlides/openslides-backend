from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock

import pytest

from openslides_backend.action.action_handler import ActionHandler
from openslides_backend.action.action_worker import gunicorn_post_request
from openslides_backend.action.relations.relation_manager import RelationManager
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.actions_map import actions_map
from openslides_backend.action.util.typing import ActionResults, Payload
from openslides_backend.http.application import OpenSlidesBackendWSGIApplication
from openslides_backend.http.views.action_view import ActionView
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permission
from openslides_backend.services.database.commands import GetManyRequest
from openslides_backend.shared.exceptions import AuthenticationException
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.patterns import (
    FullQualifiedId,
    fqid_from_collection_and_id,
)
from tests.system.action.util import get_internal_auth_header
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_action_test_application, get_route_path
from tests.util import Response

from .mock_gunicorn_gthread_worker import MockGunicornThreadWorker

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
        self.connection.commit()
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
        self,
        action_name: str,
        data: dict[str, Any] | list[dict[str, Any]],
        user_id: int = -1,
    ) -> ActionResults | None:
        """
        Shorthand to execute an action internally where all permissions etc. are ignored.
        Useful when an action is just executed for the end result and not for testing it.
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
        if isinstance(action_data, dict):
            action_data = [action_data]
        write_request, result = action.perform(action_data, user_id, internal=True)
        if write_request:
            action.validate_write_request(write_request)
            self.datastore.write(write_request)
        self.datastore.reset()
        self.connection.commit()
        return result

    def create_committee(
        self,
        committee_id: int = 1,
        parent_id: int | None = None,
        name: str | None = None,
    ) -> None:
        if not name:
            name = f"Committee{committee_id}"
        committee_fqid = f"committee/{committee_id}"
        data: dict[str, dict[str, Any]] = {
            committee_fqid: {
                "organization_id": 1,
                "name": name or f"com{committee_id}",
            }
        }
        if parent_id:
            parent_fqid = f"committee/{parent_id}"
            parent = self.datastore.get(
                parent_fqid,
                ["all_parent_ids", "all_child_ids"],
                lock_result=False,
                use_changed_models=False,
            )
            data[parent_fqid] = {
                "all_child_ids": [*parent.get("all_child_ids", []), committee_id],
            }
            data[committee_fqid]["parent_id"] = parent_id
            if grandparent_ids := parent.get("all_parent_ids", []):
                grandparents = self.datastore.get_many(
                    [GetManyRequest("committee", grandparent_ids, ["all_child_ids"])],
                    lock_result=False,
                    use_changed_models=False,
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

    def set_anonymous(
        self,
        enable: bool = True,
        meeting_id: int = 1,
        permissions: list[Permission] = [],
    ) -> int:
        """Also creates an anonymous group at the next-highest free group_id"""
        next_group_id = self.datastore.reserve_id("group")
        self.set_models(
            {
                f"meeting/{meeting_id}": {
                    "enable_anonymous": enable,
                    "anonymous_group_id": next_group_id,
                },
                f"group/{next_group_id}": {
                    "name": "Anonymous",
                    "meeting_id": meeting_id,
                    "permissions": permissions,
                },
            }
        )
        return next_group_id

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
        anonymous: bool = False,
        user_groups: list[int] = [3],
        custom_error_message: str = None,
    ) -> None:
        meeting_data = {"locked_from_inside": True} if lock_meeting else {}
        self.create_meeting(meeting_data=meeting_data)
        self.user_id = self.create_user("user")
        if user_groups:
            meeting_user_id = self.set_user_groups(self.user_id, user_groups)[0]
        if models:
            self.set_models(models)
        if lock_out_calling_user:
            self.set_models({f"meeting_user/{meeting_user_id}": {"locked_out": True}})
        if permission:
            if isinstance(permission, OrganizationManagementLevel):
                self.set_organization_management_level(permission, self.user_id)
            elif isinstance(permission, list):
                self.set_group_permissions(3, permission)
            else:
                self.set_group_permissions(3, [permission])
        self.login(self.user_id)
        response = self.request(action, action_data, anonymous)
        if fail is None:
            fail = not permission or custom_error_message
        if fail:
            self.assert_status_code(response, 403)
            error_message = (
                custom_error_message
                or f"You are not allowed to perform action {action}"
            )
            self.assertIn(error_message, response.json["message"])
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

    def get_last_history_information(self, fqid: FullQualifiedId) -> list[str] | None:
        entry_id = self.datastore.max(
            "history_entry",
            FilterOperator("original_model_id", "=", fqid),
            "id",
            lock_result=False,
        )
        if entry_id:
            history_entry = self.datastore.get(
                fqid_from_collection_and_id("history_entry", entry_id),
                ["entries"],
                lock_result=False,
            )
            return history_entry.get("entries")
        else:
            return None

    def assert_history_information(
        self, fqid: FullQualifiedId, information: list[str] | None
    ) -> None:
        """
        Asserts that the last history information for the given model is the given information.
        """
        last_information = self.get_last_history_information(fqid)
        if information is None:
            assert not last_information
        else:
            assert last_information
            self.assertEqual(last_information, information)

    def assert_history_information_contains(
        self, fqid: FullQualifiedId, information: str
    ) -> None:
        """
        Asserts that the last history information for the given model is the given information.
        """
        last_information = self.get_last_history_information(fqid)
        assert last_information
        assert information in last_information

    def assert_logged_in(self) -> None:
        self.auth.authenticate()  # assert that no exception is thrown

    def assert_logged_out(self) -> None:
        with pytest.raises(AuthenticationException):
            self.auth.authenticate()
        BaseSystemTestCase.auth_data = None
