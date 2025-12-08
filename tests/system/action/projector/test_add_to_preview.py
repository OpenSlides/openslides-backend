from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class ProjectorAddToPreview(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "assignment/1": {
                    "meeting_id": 1,
                    "title": "test assignment",
                },
                "list_of_speakers/23": {
                    "content_object_id": "assignment/1",
                    "meeting_id": 1,
                },
                "projector/2": {"meeting_id": 1},
                "projector/3": {"meeting_id": 1},
                "projection/10": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                    "preview_projector_id": 1,
                    "weight": 10,
                },
                "projection/11": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                    "preview_projector_id": 2,
                    "weight": 20,
                },
                "projection/12": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                    "preview_projector_id": 2,
                    "weight": 30,
                },
            }
        )

    def test_add_to_preview(self) -> None:
        response = self.request(
            "projector.add_to_preview",
            {
                "ids": [1, 2],
                "content_object_id": "assignment/1",
                "stable": False,
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector/1", {"preview_projection_ids": [10, 13]})
        self.assert_model_exists(
            "projector/2", {"preview_projection_ids": [11, 12, 14]}
        )
        self.assert_model_exists(
            "projection/13",
            {
                "preview_projector_id": 1,
                "content_object_id": "assignment/1",
                "weight": 11,
            },
        )
        self.assert_model_exists(
            "projection/14",
            {
                "preview_projector_id": 2,
                "content_object_id": "assignment/1",
                "weight": 31,
            },
        )

    def test_add_to_preview_empty_projector(self) -> None:
        response = self.request(
            "projector.add_to_preview",
            {
                "ids": [3],
                "content_object_id": "assignment/1",
                "stable": False,
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector/3", {"preview_projection_ids": [13]})
        self.assert_model_exists(
            "projection/13",
            {
                "preview_projector_id": 3,
                "content_object_id": "assignment/1",
                "weight": 1,
            },
        )

    def test_add_to_preview_non_unique_ids(self) -> None:
        response = self.request(
            "projector.add_to_preview",
            {
                "ids": [1, 1],
                "content_object_id": "assignment/1",
                "stable": False,
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action projector.add_to_preview: data.ids must contain unique items",
            response.json["message"],
        )

    def test_add_to_preview_check_meeting_id(self) -> None:
        self.create_meeting(4)
        response = self.request(
            "projector.add_to_preview",
            {
                "ids": [4],
                "content_object_id": "assignment/1",
                "stable": False,
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The following models do not belong to meeting 1: ['projector/4']",
            response.json["message"],
        )

    def test_add_to_preview_user(self) -> None:
        user_id = self.create_user_for_meeting(1)
        response = self.request(
            "projector.add_to_preview",
            {
                "ids": [1],
                "content_object_id": f"user/{user_id}",
                "stable": False,
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The collection 'user' is not available for field 'content_object_id' in collection 'projection'.",
            response.json["message"],
        )

    def test_add_to_preview_meeting_user(self) -> None:
        self.create_user_for_meeting(1)
        response = self.request(
            "projector.add_to_preview",
            {
                "ids": [1],
                "content_object_id": "meeting_user/1",
                "stable": False,
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The collection 'meeting_user' is not available for field 'content_object_id' in collection 'projection'.",
            response.json["message"],
        )

    def test_add_to_preview_non_existent_content_object(self) -> None:
        response = self.request(
            "projector.add_to_preview",
            {
                "ids": [1],
                "content_object_id": "motion/42",
                "stable": False,
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The following models do not belong to meeting 1: ['motion/42']",
            response.json["message"],
        )

    def test_add_to_preview_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "projector.add_to_preview",
            {
                "ids": [1, 2],
                "content_object_id": "assignment/1",
                "stable": False,
                "meeting_id": 1,
            },
        )

    def test_add_to_preview_permission(self) -> None:
        self.base_permission_test(
            {},
            "projector.add_to_preview",
            {
                "ids": [1, 2],
                "content_object_id": "assignment/1",
                "stable": False,
                "meeting_id": 1,
            },
            Permissions.Projector.CAN_MANAGE,
        )

    def test_add_to_preview_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.add_to_preview",
            {
                "ids": [1, 2],
                "content_object_id": "assignment/1",
                "stable": False,
                "meeting_id": 1,
            },
        )

    def test_mediafile_as_content_object(self) -> None:
        self.create_mediafile()
        self.set_models(
            {
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
            "projector.add_to_preview",
            {"ids": [1], "content_object_id": "mediafile/1", "meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/13",
            {"content_object_id": "meeting_mediafile/2", "preview_projector_id": 1},
        )

    def test_mediafile_as_content_object_generate_meeting_mediafile(self) -> None:
        self.create_mediafile()
        response = self.request(
            "projector.add_to_preview",
            {"ids": [2], "content_object_id": "mediafile/1", "meeting_id": 1},
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
                "projection_ids": [13],
            },
        )
        self.assert_model_exists(
            "projection/13",
            {"content_object_id": "meeting_mediafile/1", "preview_projector_id": 2},
        )

    def test_meeting_mediafile_as_content_object(self) -> None:
        self.create_mediafile()
        self.set_models(
            {
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
            "projector.add_to_preview",
            {"ids": [1], "content_object_id": "meeting_mediafile/2", "meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/13",
            {"content_object_id": "meeting_mediafile/2", "preview_projector_id": 1},
        )

    def test_unpublished_mediafile_as_content_object(self) -> None:
        self.set_models({"mediafile/1": {"owner_id": ONE_ORGANIZATION_FQID}})
        response = self.request(
            "projector.add_to_preview",
            {"ids": [2], "content_object_id": "mediafile/1", "meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "No meeting_mediafile creation possible: Mediafile is not published.",
            response.json["message"],
        )
