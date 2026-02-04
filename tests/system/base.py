import threading
from collections.abc import Callable
from copy import deepcopy
from typing import Any, cast
from unittest import TestCase, TestResult
from unittest.mock import MagicMock, _patch

import simplejson as json
from fastjsonschema.exceptions import JsonSchemaException
from psycopg import sql

from openslides_backend.action.util.crypto import get_random_string
from openslides_backend.http.application import OpenSlidesBackendWSGIApplication
from openslides_backend.models.base import (
    Model,
    json_dict_to_non_json_data_types,
    model_registry,
)
from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permission
from openslides_backend.services.auth.interface import AuthenticationService
from openslides_backend.services.database.commands import GetManyRequest
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.env import Environment
from openslides_backend.shared.exceptions import (
    ActionException,
    BadCodingException,
    ModelDoesNotExist,
)
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.interfaces.event import Event, EventType, ListFields
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.shared.patterns import (
    FullQualifiedId,
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
    is_reserved_field,
)
from openslides_backend.shared.typing import PartialModel
from openslides_backend.shared.util import (
    EXAMPLE_DATA_FILE,
    ONE_ORGANIZATION_FQID,
    ONE_ORGANIZATION_ID,
    get_initial_data_file,
)
from tests.util import AuthData, Client, Response

from .util import TestVoteService

DEFAULT_PASSWORD = "password"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"


class BaseSystemTestCase(TestCase):
    app: OpenSlidesBackendWSGIApplication
    auth: AuthenticationService
    vote_service: TestVoteService
    media: Any  # Any is needed because it is mocked and has magic methods
    client: Client
    anon_client: Client

    # Save auth data as class variable
    auth_data: AuthData | None = None

    auth_mockers: dict[str, _patch]
    # Save all created fqids
    created_fqids: set[str]

    # create organization, superadmin and login
    init_with_login: bool = True

    def setUp(self) -> None:
        # register_services()
        self.app = self.get_application()
        self.logger = cast(MagicMock, self.app.logger)
        self.services = self.app.services
        self.env = cast(Environment, self.app.env)
        self.auth = self.services.authentication()
        self.media = self.services.media()
        self.vote_service = cast(TestVoteService, self.services.vote())
        self.set_thread_watch_timeout(-1)

        self.created_fqids = set()
        if self.init_with_login:
            self.set_models(
                {
                    ONE_ORGANIZATION_FQID: {
                        "name": "OpenSlides Organization",
                        "default_language": "en",
                        "user_ids": [1],
                        "theme_id": 1,
                    },
                    "theme/1": {
                        "name": "OpenSlides Organization",
                    },
                    "user/1": {
                        "username": ADMIN_USERNAME,
                        "password": self.auth.hash(ADMIN_PASSWORD),
                        "default_password": ADMIN_PASSWORD,
                        "is_active": True,
                        "organization_management_level": "superadmin",
                        "organization_id": ONE_ORGANIZATION_ID,
                    },
                }
            )
        self.client = self.create_client(self.update_vote_service_auth_data)
        self.client.auth = self.auth  # type: ignore
        if self.init_with_login:
            if self.auth_data:
                # Reuse old login data to avoid a new login request
                self.client.update_auth_data(self.auth_data)
            else:
                # Login and save copy of auth data for all following tests
                self.client.login(ADMIN_USERNAME, ADMIN_PASSWORD, 1)
                BaseSystemTestCase.auth_data = deepcopy(self.client.auth_data)
        self.anon_client = self.create_client()
        self.anon_client.auth = self.auth  # type: ignore

    def set_thread_watch_timeout(self, timeout: float) -> None:
        """
        Set the timeout for the thread watch.
        timeout > 0: Waits `timeout` seconds before continuing the action in the action worker.
        timeout = 0: Continues the action in the action worker immediately.
        timeout = -1: Waits indefinetly for the action to finish, does not start an action worker
        timeout = -2: Deacticates threading alltogether. The action is executed in the main thread.
        """
        self.env.vars["OPENSLIDES_BACKEND_THREAD_WATCH_TIMEOUT"] = str(timeout)

    def run(self, result: TestResult | None = None) -> TestResult | None:
        """
        Overrides the TestCases run method.
        Provides an ExtendedDatabase in self.datastore with an open psycopg connection.
        Also stores its connection in self.connection.
        """
        with get_new_os_conn() as conn:
            self.datastore = ExtendedDatabase(conn, MagicMock(), MagicMock())
            self.connection = conn
            return super().run(result)

    def tearDown(self) -> None:
        if thread := self.__class__.get_thread_by_name("action_worker"):
            thread.join()

        # TODO: Does something equivalent to this old code
        #  need to be done here?
        # injector.get(ShutdownService).shutdown()

        super().tearDown()

    @staticmethod
    def get_thread_by_name(name: str) -> threading.Thread | None:
        for thread in threading.enumerate():
            if thread.name == name:
                return thread
        return None

    def load_example_data(self) -> None:
        """
        Useful for debug purposes when an action fails with the example data.
        Do NOT use in final tests since it takes a long time.
        """
        example_data = get_initial_data_file(EXAMPLE_DATA_FILE)
        json_dict_to_non_json_data_types(example_data)
        self._load_data(example_data)

    def load_json_data(self, filename: str) -> None:
        """
        Useful for debug purposes when an action fails with a specific dump.
        Do NOT use in final tests since it takes a long time.
        """
        with open(filename) as file:
            data = json.loads(file.read())
        self._load_data(data)

    def _load_data(self, raw_data: dict[str, dict[str, Any]]) -> None:
        data = {}
        for collection, models in raw_data.items():
            if collection == "_migration_index":
                continue
            for model_id, model in models.items():
                data[f"{collection}/{model_id}"] = {
                    f: v for f, v in model.items() if not f.startswith("meta_")
                }
        self.set_models(data)

    def create_client(
        self, on_auth_data_changed: Callable[[AuthData], None] | None = None
    ) -> Client:
        return Client(self.app, on_auth_data_changed)

    def login(self, user_id: int) -> None:
        """
        Login the given user by fetching the default password from the datastore.
        """
        user = self.get_model(f"user/{user_id}")
        assert user.get("default_password")
        self.client.login(user["username"], user["default_password"], user_id)

    def update_vote_service_auth_data(self, auth_data: AuthData) -> None:
        self.vote_service.set_authentication(
            auth_data["access_token"], auth_data["refresh_id"]
        )

    def get_application(self) -> OpenSlidesBackendWSGIApplication:
        raise NotImplementedError()

    def assert_status_code(self, response: Response, code: int) -> None:
        if (
            response.status_code != code
            and response.json
            and response.json.get("message")
        ):
            print(response.json)
        self.assertEqual(response.status_code, code)

    def create_model(
        self, fqid: str, data: dict[str, Any] = {}, deleted: bool = False
    ) -> None:
        create_events = self.get_create_events(fqid, data, deleted)
        self.perform_write_request(create_events)
        self.adjust_id_sequences()

    def update_model(
        self, fqid: str, fields: dict[str, Any], list_fields: ListFields = {}
    ) -> None:
        update_events = self.get_update_events(fqid, fields)
        if list_fields:
            update_events.extend(
                self.get_update_list_events(
                    fqid, list_fields.get("add", {}), list_fields.get("remove", {})
                )
            )
        self.perform_write_request(update_events)

    def get_create_events(
        self, fqid: str, data: dict[str, Any] = {}, deleted: bool = False
    ) -> list[Event]:
        self.created_fqids.add(fqid)
        data["id"] = id_from_fqid(fqid)
        self.validate_fields(fqid, data)
        events = [Event(type=EventType.Create, fqid=fqid, fields=data)]
        if deleted:
            events.append(Event(type=EventType.Delete, fqid=fqid))
        return events

    def get_update_events(self, fqid: str, data: dict[str, Any]) -> list[Event]:
        self.validate_fields(fqid, data)
        if data:
            return [Event(type=EventType.Update, fqid=fqid, fields=data)]
        else:
            return []

    def get_update_list_events(
        self, fqid: str, add: dict[str, Any] = {}, remove: dict[str, Any] = {}
    ) -> list[Event]:
        self.validate_fields(fqid, add)
        self.validate_fields(fqid, remove)
        if not (add or remove):
            return []
        return [
            Event(
                type=EventType.Update,
                fqid=fqid,
                list_fields={"add": add, "remove": remove},
            )
        ]

    def perform_write_request(self, events: list[Event]) -> None:
        write_request = WriteRequest(events, user_id=0)
        if self.check_auth_mockers_started():
            for event in write_request.events:
                self.auth.create_update_user_session(event)  # type: ignore
        self.datastore.write(write_request)
        self.connection.commit()

    def set_models(self, models: dict[FullQualifiedId, dict[str, Any]]) -> None:
        """
        Can be used to set multiple models at once, independent of create or update.
        Uses self.created_fqids to determine which models are already created. If you want to update
        a model which was not set in the test but created via an action, you may have to add the
        fqid to this set.
        """
        events: list[Event] = []
        for fqid, model in models.items():
            if fqid in self.created_fqids:
                events.extend(self.get_update_events(fqid, model))
            else:
                events.extend(self.get_create_events(fqid, model))
        self.perform_write_request(events)
        self.adjust_id_sequences()

    def adjust_id_sequences(self) -> None:
        for collection in {collection_from_fqid(fqid) for fqid in self.created_fqids}:
            maximum = self.datastore.max(collection, None, "id")
            with self.connection.cursor() as curs:
                curs.execute(
                    sql.SQL(
                        """SELECT setval('{collection}_t_id_seq', {maximum})"""
                    ).format(
                        collection=sql.SQL(collection),
                        maximum=sql.Literal(maximum),
                    )
                )
            self.connection.commit()

    def check_auth_mockers_started(self) -> bool:
        if (
            hasattr(self, "auth_mockers")
            and not self.auth_mockers["auth_http_adapter_patch"]._active_patches  # type: ignore
        ):
            return False
        return True

    def validate_fields(self, fqid: str, fields: dict[str, Any]) -> None:
        model = model_registry[collection_from_fqid(fqid)]()
        for field_name, value in fields.items():
            try:
                model.get_field(field_name).validate_with_schema(
                    fqid, field_name, value
                )
            except ActionException as e:
                raise JsonSchemaException(e.message)

    def get_model(self, fqid: str, raise_exception: bool = True) -> dict[str, Any]:
        model = self.datastore.get(
            fqid,
            mapped_fields=[],
            lock_result=False,
            use_changed_models=False,
            raise_exception=raise_exception,
        )
        if raise_exception:
            self.assertTrue(model)
            self.assertEqual(model.get("id"), id_from_fqid(fqid))
        return model

    def assert_model_exists(
        self, fqid: str, fields: dict[str, Any] = dict()
    ) -> dict[str, Any]:
        return self._assert_fields(fqid, fields)

    def assert_model_not_exists(self, fqid: str) -> None:
        with self.assertRaises(ModelDoesNotExist):
            self.get_model(fqid)

    def _assert_fields(
        self, fqid: FullQualifiedId, fields: dict[str, Any]
    ) -> dict[str, Any]:
        model = self.get_model(fqid)
        assert model
        model_cls = model_registry[collection_from_fqid(fqid)]()
        for field_name, value in fields.items():
            if not is_reserved_field(field_name) and value is not None:
                # assert that the field actually exists to detect errors in the tests
                model_cls.get_field(field_name)
            self.assertEqual(
                model.get(field_name),
                value,
                f"{fqid}: Models differ in field {field_name}!",
            )
        return model

    def assert_defaults(self, model: type[Model], instance: dict[str, Any]) -> None:
        for field in model().get_fields():
            if getattr(field, "default", None) is not None:
                self.assertEqual(
                    field.default,
                    instance.get(field.own_field_name),
                    f"Field {field.own_field_name}: Value {instance.get(field.own_field_name, 'None')} is not equal default value {field.default}.",
                )

    def assert_model_count(self, collection: str, meeting_id: int, count: int) -> None:
        self.connection.commit()
        db_count = self.datastore.count(
            collection,
            FilterOperator("meeting_id", "=", meeting_id),
            lock_result=False,
        )
        self.assertEqual(db_count, count)

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
                    "meeting_id": base,
                    **{field: base for field in Meeting.reverse_default_projectors()},
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
                f"committee/{committee_id}": {"name": f"Committee{committee_id}"},
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
            }
        )

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
                    "state_id": state_id or meeting_id,
                    "meeting_id": meeting_id,
                    **motion_data,
                },
                f"list_of_speakers/{base}": {
                    "content_object_id": f"motion/{base}",
                    "meeting_id": meeting_id,
                },
            }
        )

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

    def create_topic(
        self, base: int, meeting_id: int, topic_data: PartialModel = {}
    ) -> None:
        self.set_models(
            {
                f"topic/{base}": {
                    "title": "test",
                    "meeting_id": meeting_id,
                    **topic_data,
                },
                f"agenda_item/{base}": {
                    "meeting_id": meeting_id,
                    "content_object_id": f"topic/{base}",
                },
                f"list_of_speakers/{base}": {
                    "content_object_id": f"topic/{base}",
                    "meeting_id": meeting_id,
                },
            }
        )

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

    def create_user(
        self,
        username: str,
        group_ids: list[int] = [],
        organization_management_level: OrganizationManagementLevel | None = None,
        home_committee_id: int | None = None,
        committee_management_ids: list[int] = [],
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
        if committee_management_ids:
            self.set_committee_management_level(committee_management_ids, id)
        meeting_user_ids.extend(self.set_user_groups(id, group_ids))
        return id

    def create_user_for_meeting(self, meeting_id: int) -> int:
        """adds created user to default group, returns user_id"""
        meeting = self.get_model(f"meeting/{meeting_id}")
        user_id = self.create_user("user_" + get_random_string(6))
        self.set_user_groups(user_id, [meeting["default_group_id"]])
        return user_id

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
            if user_id not in db_committee["manager_ids"]:
                db_committee["manager_ids"].append(user_id)

        self.set_models(
            {
                f"committee/{committee_id}": {
                    "manager_ids": committee.get("manager_ids", [])
                }
                for committee_id, committee in db_committees.items()
            }
        )

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

    def set_group_permissions(
        self, group_id: int, permissions: list[Permission]
    ) -> None:
        self.update_model(f"group/{group_id}", {"permissions": permissions})

    def add_group_permissions(
        self, group_id: int, permissions: list[Permission]
    ) -> None:
        self.update_model(
            fqid_from_collection_and_id("group", group_id),
            {},
            {"add": {"permissions": [str(p) for p in permissions]}},
        )

    def remove_group_permissions(
        self, group_id: int, permissions: list[Permission]
    ) -> None:
        self.update_model(
            fqid_from_collection_and_id("group", group_id),
            {},
            {"remove": {"permissions": [str(p) for p in permissions]}},
        )
