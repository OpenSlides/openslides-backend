from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class ProjectorProject(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "meeting/2": {"is_active_in_organization_id": 1, "committee_id": 60},
                "projector/23": {
                    "meeting_id": 1,
                    "current_projection_ids": [105, 106],
                    "scroll": 80,
                },
                "projector/65": {"meeting_id": 1},
                "projector/75": {"meeting_id": 1, "current_projection_ids": [110, 111]},
                "projection/105": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/452",
                    "current_projector_id": 23,
                    "stable": False,
                },
                "projection/106": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/452",
                    "current_projector_id": 23,
                    "stable": True,
                },
                "projection/110": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/453",
                    "current_projector_id": 75,
                    "stable": False,
                    "type": "test",
                },
                "projection/111": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/453",
                    "current_projector_id": 75,
                    "stable": True,
                },
                "assignment/452": {"meeting_id": 1},
                "assignment/453": {"meeting_id": 1},
                "assignment/567": {"meeting_id": 2},
            }
        )

    def test_project(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [23],
                "content_object_id": "assignment/453",
                "meeting_id": 1,
                "options": {},
                "stable": False,
                "type": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/105",
            {
                "content_object_id": "assignment/452",
                "history_projector_id": 23,
                "stable": False,
                "weight": 1,
            },
        )
        self.assert_model_exists(
            "projection/106",
            {
                "content_object_id": "assignment/452",
                "current_projector_id": 23,
                "stable": True,
            },
        )
        self.assert_model_exists(
            "projection/112",
            {
                "content_object_id": "assignment/453",
                "current_projector_id": 23,
                "stable": False,
                "options": {},
                "type": "test",
            },
        )
        self.assert_model_exists(
            "projection/110",
            {
                "content_object_id": "assignment/453",
                "history_projector_id": 75,
                "stable": False,
                "type": "test",
                "weight": 1,
            },
        )
        self.assert_model_exists(
            "projection/111",
            {
                "content_object_id": "assignment/453",
                "current_projector_id": 75,
                "stable": True,
            },
        )
        self.assert_model_exists(
            "projector/23",
            {
                "current_projection_ids": [106, 112],
                "history_projection_ids": [105],
                "scroll": 0,
            },
        )
        self.assert_model_exists(
            "projector/75",
            {"current_projection_ids": [111], "history_projection_ids": [110]},
        )

    def test_project_2(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [23, 65],
                "content_object_id": "assignment/453",
                "meeting_id": 1,
                "stable": True,
                "options": None,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/105",
            {
                "content_object_id": "assignment/452",
                "current_projector_id": 23,
                "stable": False,
                "options": None,
            },
        )
        self.assert_model_exists(
            "projection/106",
            {
                "content_object_id": "assignment/452",
                "current_projector_id": 23,
                "stable": True,
            },
        )
        self.assert_model_exists(
            "projection/112",
            {
                "content_object_id": "assignment/453",
                "current_projector_id": 23,
                "stable": True,
            },
        )
        self.assert_model_exists(
            "projection/113",
            {
                "content_object_id": "assignment/453",
                "current_projector_id": 65,
                "stable": True,
            },
        )
        self.assert_model_exists(
            "projector/23", {"current_projection_ids": [105, 106, 112], "scroll": 80}
        )
        self.assert_model_exists("projector/65", {"current_projection_ids": [113]})

    def test_project_3(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [],
                "content_object_id": "assignment/453",
                "meeting_id": 1,
                "stable": False,
                "type": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/75",
            {"current_projection_ids": [111], "history_projection_ids": [110]},
        )
        self.assert_model_exists(
            "projection/110",
            {
                "current_projector_id": None,
                "history_projector_id": 75,
                "stable": False,
                "weight": 1,
            },
        )
        self.assert_model_exists(
            "projection/111",
            {"current_projector_id": 75, "history_projector_id": None, "stable": True},
        )

    def test_try_to_project_anonymous(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [23],
                "content_object_id": "meeting_user/0",
                "meeting_id": 1,
                "stable": False,
            },
        )
        self.assert_status_code(response, 400)
        assert "data.content_object_id must match pattern" in response.json["message"]

    def test_try_to_store_second_unstable_projection_1(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [23],
                "content_object_id": "assignment/452",
                "meeting_id": 1,
                "stable": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/23",
            {
                "current_projection_ids": [106, 112],
                "history_projection_ids": [105],
                "scroll": 0,
            },
        )
        self.assert_model_exists(
            "projection/112",
            {
                "content_object_id": "assignment/452",
                "current_projector_id": 23,
                "stable": False,
            },
        )
        self.assert_model_exists(
            "projection/105",
            {
                "content_object_id": "assignment/452",
                "history_projector_id": 23,
                "stable": False,
                "weight": 1,
            },
        )
        self.assert_model_exists(
            "projection/106",
            {
                "content_object_id": "assignment/452",
                "current_projector_id": 23,
                "stable": True,
            },
        )

    def test_try_to_store_second_unstable_projection_2(self) -> None:
        response = self.request_multi(
            "projector.project",
            [
                {
                    "ids": [23],
                    "content_object_id": "assignment/452",
                    "meeting_id": 1,
                    "stable": False,
                },
                {
                    "ids": [23],
                    "content_object_id": "assignment/452",
                    "meeting_id": 1,
                    "stable": False,
                },
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain less than or equal to 1 items", response.json["message"]
        )

    def test_try_to_store_second_unstable_projection_3(self) -> None:
        response = self.request_json(
            [
                {
                    "action": "projector.project",
                    "data": [
                        {
                            "ids": [23],
                            "content_object_id": "assignment/452",
                            "meeting_id": 1,
                            "stable": False,
                        }
                    ],
                },
                {
                    "action": "projector.project",
                    "data": [
                        {
                            "ids": [23],
                            "content_object_id": "assignment/452",
                            "meeting_id": 1,
                            "stable": False,
                        }
                    ],
                },
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Action projector.project may not appear twice in one request.",
            response.json["message"],
        )

    def test_try_to_store_second_stable_projection(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [23],
                "content_object_id": "assignment/452",
                "meeting_id": 1,
                "stable": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/23", {"current_projection_ids": [105, 112], "scroll": 80}
        )
        self.assert_model_exists(
            "projection/112",
            {
                "content_object_id": "assignment/452",
                "current_projector_id": 23,
                "stable": True,
            },
        )
        self.assert_model_exists(
            "projection/105",
            {
                "content_object_id": "assignment/452",
                "current_projector_id": 23,
                "stable": False,
            },
        )
        self.assert_model_not_exists("projection/106")

    def test_try_to_store_second_stable_projection_keep_active(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [65],
                "meeting_id": 1,
                "content_object_id": "assignment/453",
                "stable": True,
                "keep_active_projections": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/65", {"meeting_id": 1, "current_projection_ids": [112]}
        )
        self.assert_model_exists(
            "projector/75",
            {"meeting_id": 1, "current_projection_ids": [110, 111]},
        )

    def test_try_to_store_second_stable_projection_no_keep_active(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [65],
                "meeting_id": 1,
                "content_object_id": "assignment/453",
                "stable": True,
                "keep_active_projections": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/65", {"meeting_id": 1, "current_projection_ids": [112]}
        )
        self.assert_model_exists(
            "projector/75",
            {"meeting_id": 1, "current_projection_ids": [110]},
        )

    def test_meeting_as_content_object_ok(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [],
                "content_object_id": "meeting/1",
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)

    def test_user_as_content_object(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "normal user",
                    "meeting_ids": [1],
                },
            }
        )
        self.set_user_groups(2, [1])
        response = self.request(
            "projector.project",
            {"ids": [75], "content_object_id": "user/2", "meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        assert (
            "The collection 'user' is not available for field 'content_object_id' in collection 'projection'."
            in response.json["message"]
        )

    def test_meeting_user_as_content_object(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "normal user",
                    "meeting_ids": [1],
                    "meeting_user_ids": [2],
                },
                "meeting_user/2": {
                    "meeting_id": 1,
                    "user_id": 2,
                    "group_ids": [1],
                },
            }
        )
        response = self.request(
            "projector.project",
            {"ids": [75], "content_object_id": "meeting_user/2", "meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        assert (
            "The collection 'meeting_user' is not available for field 'content_object_id' in collection 'projection'."
            in response.json["message"]
        )

    def test_mediafile_as_content_object(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [2],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "meeting_mediafile/2": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "access_group_ids": [1],
                    "inherited_access_group_ids": [1],
                    "is_public": False,
                },
            }
        )
        response = self.request(
            "projector.project",
            {"ids": [75], "content_object_id": "mediafile/1", "meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/112",
            {
                "content_object_id": "meeting_mediafile/2",
                "current_projector_id": 75,
            },
        )

    def test_mediafile_as_content_object_generate_meeting_mediafile(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            }
        )
        response = self.request(
            "projector.project",
            {"ids": [75], "content_object_id": "mediafile/1", "meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "meeting_id": 1,
                "mediafile_id": 1,
                "access_group_ids": [2],
                "inherited_access_group_ids": [2],
                "is_public": False,
                "projection_ids": [112],
            },
        )
        self.assert_model_exists(
            "projection/112",
            {
                "content_object_id": "meeting_mediafile/1",
                "current_projector_id": 75,
            },
        )

    def test_meeting_mediafile_as_content_object(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "meeting_mediafile_ids": [2],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "meeting_mediafile/2": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "access_group_ids": [1],
                    "inherited_access_group_ids": [1],
                    "is_public": False,
                },
            }
        )
        response = self.request(
            "projector.project",
            {"ids": [75], "content_object_id": "meeting_mediafile/2", "meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/112",
            {
                "content_object_id": "meeting_mediafile/2",
                "current_projector_id": 75,
            },
        )

    def test_unpublished_mediafile_as_content_object(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
            }
        )
        response = self.request(
            "projector.project",
            {"ids": [75], "content_object_id": "mediafile/1", "meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        assert (
            "No meeting_mediafile creation possible: Mediafile is not published."
            in response.json["message"]
        )

    def test_project_without_meeting_id(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [23],
                "content_object_id": "assignment/453",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id'] properties",
            response.json["message"],
        )

    def test_project_wrong_meeting_by_ids_and_object(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [23],
                "content_object_id": "assignment/452",
                "meeting_id": 2,
                "stable": True,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 2", response.json["message"]
        )
        self.assertIn("'assignment/452'", response.json["message"])
        self.assertIn("'projector/23'", response.json["message"])

    def test_project_wrong_meeting_by_content_user(self) -> None:
        self.create_model(
            "user/2",
            {"username": "normal user", "meeting_user_ids": [2]},
        )
        self.set_models(
            {"meeting_user/2": {"meeting_id": 1, "user_id": 2, "group_ids": [1]}}
        )
        response = self.request(
            "projector.project",
            {"ids": [], "content_object_id": "user/2", "meeting_id": 2, "stable": True},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 2: ['user/2']",
            response.json["message"],
        )

    def test_project_wrong_meeting_by_content_meeting(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [],
                "content_object_id": "meeting/1",
                "meeting_id": 2,
                "stable": True,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 2: ['meeting/1']",
            response.json["message"],
        )

    def test_project_not_unique_ids(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [23, 23],
                "content_object_id": "assignment/453",
                "meeting_id": 1,
                "options": None,
                "stable": False,
                "type": "test",
            },
        )
        self.assert_status_code(response, 400)
        assert "data.ids must contain unique items" in response.data.decode()

    def test_project_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.project",
            {
                "ids": [23],
                "content_object_id": "assignment/453",
                "meeting_id": 1,
                "options": {},
                "stable": False,
                "type": "test",
            },
        )

    def test_project_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.project",
            {
                "ids": [23],
                "content_object_id": "assignment/453",
                "meeting_id": 1,
                "options": {},
                "stable": False,
                "type": "test",
            },
            Permissions.Projector.CAN_MANAGE,
        )

    def test_project_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.project",
            {
                "ids": [23],
                "content_object_id": "assignment/453",
                "meeting_id": 1,
                "options": {},
                "stable": False,
                "type": "test",
            },
        )
