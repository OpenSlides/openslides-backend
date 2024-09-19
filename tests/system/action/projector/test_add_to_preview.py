from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class ProjectorAddToPreview(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "meeting/2": {"is_active_in_organization_id": 1},
                "assignment/1": {"meeting_id": 1},
                "projector/1": {"meeting_id": 1, "preview_projection_ids": [10]},
                "projector/2": {"meeting_id": 1, "preview_projection_ids": [11, 12]},
                "projector/3": {"meeting_id": 1},
                "projector/4": {"meeting_id": 2},
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
        projector_1 = self.get_model("projector/1")
        assert projector_1.get("preview_projection_ids") == [10, 13]
        projector_2 = self.get_model("projector/2")
        assert projector_2.get("preview_projection_ids") == [11, 12, 14]
        projection_13 = self.get_model("projection/13")
        assert projection_13.get("preview_projector_id") == 1
        assert projection_13.get("content_object_id") == "assignment/1"
        assert projection_13.get("weight") == 11
        projection_14 = self.get_model("projection/14")
        assert projection_14.get("preview_projector_id") == 2
        assert projection_14.get("content_object_id") == "assignment/1"
        assert projection_14.get("weight") == 31

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
        projector_1 = self.get_model("projector/3")
        assert projector_1.get("preview_projection_ids") == [13]
        projection_13 = self.get_model("projection/13")
        assert projection_13.get("preview_projector_id") == 3
        assert projection_13.get("content_object_id") == "assignment/1"
        assert projection_13.get("weight") == 1

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
        assert "data.ids must contain unique items" in response.json["message"]

    def test_add_to_preview_check_meeting_id(self) -> None:
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
        self.assertIn(
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
        assert (
            "The collection 'user' is not available for field 'content_object_id' in collection 'projection'."
            in response.json["message"]
        )

    def test_add_to_preview_meeting_user(self) -> None:
        user_id = self.create_user_for_meeting(1)
        self.set_models({"meeting_user/1": {"meeting_id": 1, "user_id": user_id}})
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
        assert (
            "The collection 'meeting_user' is not available for field 'content_object_id' in collection 'projection'."
            in response.json["message"]
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
        self.assertIn(
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
            "projector.add_to_preview",
            {"ids": [1], "content_object_id": "mediafile/1", "meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/13",
            {
                "content_object_id": "meeting_mediafile/2",
                "preview_projector_id": 1,
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
            {
                "content_object_id": "meeting_mediafile/1",
                "preview_projector_id": 2,
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
            "projector.add_to_preview",
            {"ids": [1], "content_object_id": "meeting_mediafile/2", "meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/13",
            {
                "content_object_id": "meeting_mediafile/2",
                "preview_projector_id": 1,
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
            "projector.add_to_preview",
            {"ids": [2], "content_object_id": "mediafile/1", "meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        assert (
            "No meeting_mediafile creation possible: Mediafile is not published."
            in response.json["message"]
        )
