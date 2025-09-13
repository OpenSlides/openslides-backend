from copy import deepcopy
from typing import Any
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
from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permission
from openslides_backend.services.database.commands import GetManyRequest
from openslides_backend.shared.exceptions import (
    AuthenticationException,
    BadCodingException,
)
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.patterns import FullQualifiedId
from openslides_backend.shared.typing import PartialModel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
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
        user_id: int = 0,
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
            self.datastore.write(write_request)
        self.datastore.reset()
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

    def create_motion(
        self,
        meeting_id: int,
        base: int = 1,
        state_id: int = 0,
        motion_data: PartialModel = {},
    ) -> None:
        """
        The meeting and motion_state must already exist.
        Creates a motion with id 1 by default.
        You can specify another id by setting base.
        If no state_id is passed, meeting must have `state_id` equal to `id`.
        """
        self.set_models(
            {
                f"motion/{base}": {
                    "title": f"motion{base}",
                    "sequential_number": base,
                    "state_id": state_id or meeting_id,
                    "meeting_id": meeting_id,
                    **motion_data,
                },
                f"list_of_speakers/{base}": {
                    "content_object_id": f"motion/{base}",
                    "sequential_number": base,
                    "meeting_id": meeting_id,
                },
            }
        )

    def create_meeting(self, base: int = 1, meeting_data: PartialModel = {}) -> None:
        """
        Creates meeting with id 1, committee 60 and groups with ids 1(Default), 2(Admin), 3 by default.
        With base you can setup other meetings, but be cautious because of group-ids
        The groups have no permissions and no users by default.
        """
        committee_id = base + 59
        self.set_models(
            {
                f"meeting/{base}": {
                    "default_group_id": base,
                    "admin_group_id": base + 1,
                    "motions_default_workflow_id": base,
                    "motions_default_amendment_workflow_id": base,
                    "reference_projector_id": base,
                    "committee_id": committee_id,
                    "is_active_in_organization_id": 1,
                    "language": "en",
                    **meeting_data,
                },
                f"projector/{base}": {
                    "sequential_number": base,
                    "meeting_id": base,
                    **{field: base for field in Meeting.reverse_default_projectors()},
                },
                f"group/{base}": {"meeting_id": base, "name": f"group{base}"},
                f"group/{base+1}": {"meeting_id": base, "name": f"group{base+1}"},
                f"group/{base+2}": {"meeting_id": base, "name": f"group{base+2}"},
                f"motion_workflow/{base}": {
                    "name": "flo",
                    "sequential_number": base,
                    "meeting_id": base,
                    "first_state_id": base,
                },
                f"motion_state/{base}": {
                    "name": "stasis",
                    "weight": 36,
                    "meeting_id": base,
                    "workflow_id": base,
                    "first_state_of_workflow_id": base,
                },
                f"committee/{committee_id}": {"name": f"Commitee{committee_id}"},
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
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

    def set_organization_management_level(
        self, level: OrganizationManagementLevel | None, user_id: int = 1
    ) -> None:
        self.update_model(f"user/{user_id}", {"organization_management_level": level})

    def set_committee_management_level(
        self, committee_ids: list[int], user_id: int = 1
    ) -> None:
        """
        Sets the user as the only committee manager of the given committees.
        Removes all other committee managements of this user.
        """
        user = self.datastore.get(f"user/{user_id}", ["committee_management_ids"])
        # TODO Use list add and remove fields instead of obtaining and recalculating the manager_ids here
        db_committees = self.datastore.get_many(
            [
                GetManyRequest(
                    "committee",
                    user.get("committee_management_ids", []) + committee_ids,
                    ["manager_ids"],
                )
            ]
        ).get("committee", dict())

        # remove removed ones
        for db_committee_id, db_committee in db_committees.items():
            if db_committee_id not in committee_ids and "manager_ids" in db_committee:
                db_committee["manager_ids"].remove(user_id)
        # add new relation
        for committee_id in committee_ids:
            if not (db_committee := db_committees.get(committee_id, {})):
                raise BadCodingException(
                    "Committee does not exist. This test should create the committee first before changing its managers."
                )
            if "manager_ids" not in db_committee:
                db_committee["manager_ids"] = []
            db_committee["manager_ids"].append(user_id)

        self.set_models(
            {
                f"committee/{committee_id}": {
                    "manager_ids": committee.get("manager_ids", [])
                }
                for committee_id, committee in db_committees.items()
            }
        )

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
        home_committee_id: int | None = None,
        meeting_user_ids: list[int] = [],
    ) -> int:
        """
        Create a user with the given username, groups and organization management level.
        Returns the users id and stores meeting user ids in meeting_user_ids.
        """
        id = 1
        while f"user/{id}" in self.created_fqids:
            id += 1
        self.set_models(
            {
                f"user/{id}": self._get_user_data(
                    username, organization_management_level
                )
                | {"home_committee_id": home_committee_id},
            }
        )
        meeting_user_ids.extend(self.set_user_groups(id, group_ids))
        return id

    def _get_user_data(
        self,
        username: str,
        organization_management_level: OrganizationManagementLevel | None = None,
    ) -> dict[str, Any]:
        return {
            "username": username,
            "organization_management_level": organization_management_level,
            "is_active": True,
            "default_password": DEFAULT_PASSWORD,
            "password": self.auth.hash(DEFAULT_PASSWORD),
        }

    def create_user_for_meeting(self, meeting_id: int) -> int:
        """adds created user to default group, returns user_id"""
        meeting = self.get_model(f"meeting/{meeting_id}")
        user_id = self.create_user("user_" + get_random_string(6))
        self.set_user_groups(user_id, [meeting["default_group_id"]])
        return user_id

    # @with_database_context
    def set_user_groups(self, user_id: int, group_ids: list[int]) -> list[int]:
        """
        Sets the groups in corresponding meeting_users and creates new ones if not existent.
        Returns the meeting_user_ids.
        """
        assert isinstance(group_ids, list)
        current_meeting_users = self.datastore.filter(
            "meeting_user",
            FilterOperator("user_id", "=", user_id),
            ["id", "user_id", "meeting_id", "group_ids"],
            lock_result=False,
        )
        request_group_ids = set(group_ids)
        for mu in current_meeting_users.values():
            if mu_group_ids := mu.get("group_ids"):
                request_group_ids.update(mu_group_ids)
        all_users_groups = self.datastore.get_many(
            [
                GetManyRequest(
                    "group",
                    list(request_group_ids),
                    ["id", "meeting_id", "meeting_user_ids"],
                )
            ],
            lock_result=False,
        )["group"]
        meeting_ids: list[int] = list(
            {v["meeting_id"] for v in all_users_groups.values() if v["id"] in group_ids}
        )
        meeting_users: dict[int, dict[str, Any]] = {
            data["meeting_id"]: data
            for data in current_meeting_users.values()
            if data["meeting_id"] in meeting_ids
        }
        # remove from all_users_groups in difference with requested group_ids
        groups_remove_from = set(all_users_groups) - set(group_ids)
        for group_id in groups_remove_from:
            if meeting_user_ids := all_users_groups[group_id].get("meeting_user_ids"):
                # remove intersection with user
                for meeting_user_id in meeting_user_ids:
                    if meeting_user_id in current_meeting_users:
                        meeting_user_ids.remove(meeting_user_id)
        last_meeting_user_id = max(
            [
                int(k[1])
                for key in self.created_fqids
                if (k := key.split("/"))[0] == "meeting_user"
            ]
            or [0]
        )
        if meeting_users_new := {
            meeting_id: {
                "id": (last_meeting_user_id := last_meeting_user_id + 1),  # noqa: F841
                "user_id": user_id,
                "meeting_id": meeting_id,
            }
            for meeting_id in meeting_ids
            if meeting_id not in meeting_users
        }:
            meeting_users.update(meeting_users_new)

        # fill relevant meeting_user relations
        for group_id in group_ids:
            group = all_users_groups[group_id]
            meeting_id = group["meeting_id"]
            meeting_user_id = meeting_users[meeting_id]["id"]
            if meeting_user_ids := group.get("meeting_user_ids"):
                if meeting_user_id not in meeting_user_ids:
                    meeting_user_ids.append(meeting_user_id)
            else:
                group["meeting_user_ids"] = [meeting_user_id]
        if meeting_users_new or all_users_groups:
            self.set_models(
                {
                    **{
                        f"meeting_user/{mu['id']}": mu
                        for mu in meeting_users_new.values()
                    },
                    **{
                        f"group/{group['id']}": group
                        for group in all_users_groups.values()
                    },
                }
            )
        return [mu["id"] for mu in meeting_users.values()]

    def create_mediafile(
        self,
        base: int = 1,
        owner_meeting_id: int = 0,
        is_directory: bool = False,
        parent_id: int = 0,
        file_type: str = "text",
    ) -> None:
        """
        If `owner_meeting_id` is specified, creates meeting-wide mediafile
        belonging to this meeting. Otherwise, creates published
        organization-wide mediafile.

        If parent_id is provided, parent must have `is_directory=True`
        and belong to the same `owner_id`.

        If file is not directory, it has mimetype and filename of the text file
        by default. Set `file_type` to `image` or `font` to change these values.
        """
        model_data: dict[str, str | int | bool | None] = {
            "title": f"folder_{base}" if is_directory else f"file_{base}",
            "is_directory": is_directory,
            "parent_id": parent_id or None,
            "owner_id": (
                f"meeting/{owner_meeting_id}"
                if owner_meeting_id
                else ONE_ORGANIZATION_FQID
            ),
            "published_to_meetings_in_organization_id": (
                ONE_ORGANIZATION_ID if not owner_meeting_id else None
            ),
        }

        if not is_directory:
            match file_type:
                case "text":
                    mimetype = "text/plain"
                    filename = f"text-{base}.txt"
                case "font":
                    mimetype = "font/woff"
                    filename = f"font-{base}.woff"
                case "image":
                    mimetype = "image/png"
                    filename = f"image-{base}.png"
            model_data.update({"mimetype": mimetype, "filename": filename})

        self.set_models({f"mediafile/{base}": model_data})

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
        meeting_data = {"locked_from_inside": True} if lock_meeting else {}
        self.create_meeting(meeting_data=meeting_data)
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        if models:
            self.set_models(models)
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

    # @with_database_context
    def assert_history_information(
        self, fqid: FullQualifiedId, information: list[str] | None
    ) -> None:
        """
        Asserts that the last history information for the given model is the given information.
        """
        # TODO write history model and its actions
        # informations = self.datastore.history_information([fqid]).get(fqid)
        # last_information = (
        #     cast(HistoryInformation, informations[-1]["information"])
        #     if informations
        #     else {}
        # )
        # if information is None:
        #     assert not informations or fqid not in last_information, informations
        # else:
        #     assert informations
        #     self.assertEqual(last_information[fqid], information)

    # @with_database_context
    def assert_history_information_contains(
        self, fqid: FullQualifiedId, information: str
    ) -> None:
        """
        Asserts that the last history information for the given model is the given information.
        """
        # TODO write history model and its actions
        # informations = self.datastore.history_information([fqid]).get(fqid)
        # last_information = (
        #     cast(HistoryInformation, informations[-1]["information"])
        #     if informations
        #     else {}
        # )
        # assert informations
        # assert information in last_information[fqid]

    def assert_logged_in(self) -> None:
        self.auth.authenticate()  # assert that no exception is thrown

    def assert_logged_out(self) -> None:
        with pytest.raises(AuthenticationException):
            self.auth.authenticate()
        BaseSystemTestCase.auth_data = None
