from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class MediafileMoveActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"meeting_mediafile_ids": [7, 8]},
            "mediafile/7": {
                "owner_id": "meeting/1",
                "is_directory": True,
                "meeting_mediafile_ids": [7],
            },
            "mediafile/8": {
                "owner_id": "meeting/1",
                "is_directory": True,
                "meeting_mediafile_ids": [8],
            },
            "meeting_mediafile/7": {"mediafile_id": 7, "meeting_id": 1},
            "meeting_mediafile/8": {"mediafile_id": 8, "meeting_id": 1},
        }
        self.orga_permission_test_models: dict[str, dict[str, Any]] = {
            "mediafile/7": {"owner_id": ONE_ORGANIZATION_FQID, "is_directory": True},
            "mediafile/8": {"owner_id": ONE_ORGANIZATION_FQID, "is_directory": True},
        }

    def test_move_parent_none(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "meeting_mediafile_ids": [2227, 2228, 2229, 2230],
                },
                "mediafile/7": {
                    "title": "title_7",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [8, 9],
                    "meeting_mediafile_ids": [2227],
                },
                "meeting_mediafile/2227": {
                    "meeting_id": 222,
                    "mediafile_id": 7,
                },
                "mediafile/8": {
                    "title": "title_8",
                    "owner_id": "meeting/222",
                    "parent_id": 7,
                    "child_ids": [],
                    "meeting_mediafile_ids": [2228],
                },
                "meeting_mediafile/2228": {
                    "meeting_id": 222,
                    "mediafile_id": 8,
                },
                "mediafile/9": {
                    "title": "title_9",
                    "owner_id": "meeting/222",
                    "parent_id": 7,
                    "child_ids": [10],
                    "meeting_mediafile_ids": [2229],
                },
                "meeting_mediafile/2229": {
                    "meeting_id": 222,
                    "mediafile_id": 9,
                },
                "mediafile/10": {
                    "title": "title_10",
                    "owner_id": "meeting/222",
                    "parent_id": 9,
                    "child_ids": [],
                    "meeting_mediafile_ids": [2230],
                },
                "meeting_mediafile/2230": {
                    "meeting_id": 222,
                    "mediafile_id": 10,
                },
            }
        )
        response = self.request(
            "mediafile.move",
            {"owner_id": "meeting/222", "ids": [8, 9], "parent_id": None},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/7",
            {"child_ids": [], "parent_id": None, "meeting_mediafile_ids": [2227]},
        )
        self.assert_model_exists(
            "mediafile/8",
            {
                "child_ids": [],
                "parent_id": None,
                "meeting_mediafile_ids": [2228],
            },
        )
        self.assert_model_exists("meeting_mediafile/2228", {"is_public": True})
        self.assert_model_exists(
            "mediafile/9",
            {
                "child_ids": [10],
                "parent_id": None,
                "meeting_mediafile_ids": [2229],
            },
        )
        self.assert_model_exists("meeting_mediafile/2229", {"is_public": True})
        self.assert_model_exists(
            "mediafile/10",
            {
                "child_ids": [],
                "parent_id": 9,
                "meeting_mediafile_ids": [2230],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/2230",
            {"is_public": True, "inherited_access_group_ids": []},
        )

    def test_move_parent_set(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "mediafile/7": {
                    "title": "title_7",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                    "is_directory": True,
                    "meeting_mediafile_ids": [2227],
                },
                "meeting_mediafile/2227": {
                    "meeting_id": 222,
                    "mediafile_id": 7,
                    "is_public": True,
                    "inherited_access_group_ids": [],
                },
                "mediafile/8": {
                    "title": "title_8",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                    "meeting_mediafile_ids": [2228],
                },
                "meeting_mediafile/2228": {
                    "meeting_id": 222,
                    "mediafile_id": 8,
                },
                "mediafile/9": {
                    "title": "title_9",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                    "meeting_mediafile_ids": [2229],
                },
                "meeting_mediafile/2229": {
                    "meeting_id": 222,
                    "mediafile_id": 9,
                },
            }
        )
        response = self.request(
            "mediafile.move", {"owner_id": "meeting/222", "ids": [8, 9], "parent_id": 7}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/7",
            {"child_ids": [8, 9], "parent_id": None, "meeting_mediafile_ids": [2227]},
        )
        for id_ in [8, 9]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "child_ids": [],
                    "parent_id": 7,
                    "meeting_mediafile_ids": [2220 + id_],
                },
            )
            self.assert_model_exists(
                f"meeting_mediafile/222{id_}",
                {"inherited_access_group_ids": [], "is_public": True},
            )

    def test_move_non_directory_parent_set(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "mediafile/7": {
                    "title": "title_7",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                    "is_directory": False,
                    "meeting_mediafile_ids": [2227],
                },
                "meeting_mediafile/2227": {
                    "meeting_id": 222,
                    "mediafile_id": 7,
                },
                "mediafile/8": {
                    "title": "title_8",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                    "meeting_mediafile_ids": [2228],
                },
                "meeting_mediafile/2228": {
                    "meeting_id": 222,
                    "mediafile_id": 8,
                },
                "mediafile/9": {
                    "title": "title_9",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                    "meeting_mediafile_ids": [2229],
                },
                "meeting_mediafile/2229": {
                    "meeting_id": 222,
                    "mediafile_id": 9,
                },
            }
        )
        response = self.request(
            "mediafile.move", {"owner_id": "meeting/222", "ids": [8, 9], "parent_id": 7}
        )
        self.assert_status_code(response, 400)
        self.assertIn("Parent is not a directory.", response.json["message"])

    def test_move_multiple_action_data_items(self) -> None:
        """This test ensures that multi-requests are impossible"""
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "meeting_mediafile_ids": [2227, 2228],
                },
                "mediafile/7": {
                    "owner_id": "meeting/222",
                    "is_directory": True,
                    "meeting_mediafile_ids": [2227],
                },
                "meeting_mediafile/2227": {
                    "meeting_id": 222,
                    "mediafile_id": 7,
                },
                "mediafile/8": {
                    "owner_id": "meeting/222",
                    "is_directory": True,
                    "meeting_mediafile_ids": [2228],
                },
                "meeting_mediafile/2228": {
                    "meeting_id": 222,
                    "mediafile_id": 8,
                },
            }
        )
        response = self.request_multi(
            "mediafile.move",
            [
                {"owner_id": "meeting/222", "ids": [8], "parent_id": 7},
                {"owner_id": "meeting/222", "ids": [7], "parent_id": 8},
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain less than or equal to 1 items", response.json["message"]
        )
        mediafile_7 = self.get_model("mediafile/7")
        assert mediafile_7.get("parent_id") is None
        mediafile_8 = self.get_model("mediafile/8")
        assert mediafile_8.get("parent_id") is None

    def test_move_owner_mismatch(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "mediafile/7": {"owner_id": "meeting/222", "is_directory": True},
                "mediafile/8": {"owner_id": "meeting/222", "is_directory": True},
            }
        )
        response = self.request_multi(
            "mediafile.move",
            [
                {"owner_id": ONE_ORGANIZATION_FQID, "ids": [8], "parent_id": 7},
            ],
        )
        self.assert_status_code(response, 400)
        assert "Owner and parent don't match." in response.json["message"]

    def test_move_circle(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "meeting_mediafile_ids": [7, 8],
                },
                "mediafile/7": {
                    "owner_id": "meeting/222",
                    "is_directory": True,
                    "child_ids": [8],
                    "meeting_mediafile_ids": [7],
                },
                "mediafile/8": {
                    "owner_id": "meeting/222",
                    "is_directory": True,
                    "parent_id": 7,
                    "meeting_mediafile_ids": [8],
                },
                "meeting_mediafile/7": {"meeting_id": 222, "mediafile_id": 7},
                "meeting_mediafile/8": {"meeting_id": 222, "mediafile_id": 8},
            }
        )
        response = self.request(
            "mediafile.move", {"owner_id": "meeting/222", "ids": [7], "parent_id": 8}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Moving item 7 to one of its children is not possible.",
            response.json["message"],
        )

    def test_move_bigger_circle(self) -> None:
        self.set_models(
            {
                "mediafile/7": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "child_ids": [8],
                },
                "mediafile/8": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "parent_id": 7,
                    "child_ids": [9],
                },
                "mediafile/9": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "parent_id": 8,
                    "child_ids": [10],
                },
                "mediafile/10": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "parent_id": 9,
                },
            }
        )
        response = self.request(
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [7], "parent_id": 10},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Moving item 7 to one of its children is not possible.",
            response.json["message"],
        )

    def test_move_explicitly_published_file_error(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                },
                "mediafile/2": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            }
        )
        response = self.request(
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [2], "parent_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Item 2 is published and may therefore not be moved away from the root directory. Please unpublish it first.",
            response.json["message"],
        )

    def test_move_explicitly_published_file_error_2(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "mediafile/2": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            }
        )
        response = self.request(
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [2], "parent_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Item 2 is published and may therefore not be moved away from the root directory. Please unpublish it first.",
            response.json["message"],
        )

    def test_move_to_explicitly_published_directory(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                },
                "mediafile/2": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            }
        )
        response = self.request(
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [1], "parent_id": 2},
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting_mediafile/1")

    def test_move_unpublished_to_published_parent_meeting_data(self) -> None:
        self.create_meeting(1)
        self.create_meeting(4)
        self.create_meeting(7)
        self.set_models(
            {
                "meeting/1": {"meeting_mediafile_ids": [1]},
                "group/3": {"meeting_mediafile_inherited_access_group_ids": [1]},
                "meeting/4": {"meeting_mediafile_ids": [4]},
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "meeting_mediafile_ids": [1, 4],
                },
                "meeting_mediafile/1": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "inherited_access_group_ids": [3],
                    "is_public": False,
                },
                "meeting_mediafile/4": {
                    "meeting_id": 4,
                    "mediafile_id": 1,
                },
                "mediafile/2": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "child_ids": [3],
                },
                "mediafile/3": {
                    "parent_id": 2,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                },
            }
        )
        response = self.request(
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [2], "parent_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/2",
            {
                "parent_id": 1,
                "meeting_mediafile_ids": [5, 7],
                "child_ids": [3],
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/5",
            {
                "mediafile_id": 2,
                "meeting_id": 1,
                "inherited_access_group_ids": [3],
                "is_public": False,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/7",
            {
                "mediafile_id": 2,
                "meeting_id": 4,
                "inherited_access_group_ids": [],
                "is_public": True,
            },
        )
        self.assert_model_exists(
            "mediafile/3",
            {
                "parent_id": 2,
                "meeting_mediafile_ids": [6, 8],
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/6",
            {
                "mediafile_id": 3,
                "meeting_id": 1,
                "inherited_access_group_ids": [3],
                "is_public": False,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/8",
            {
                "mediafile_id": 3,
                "meeting_id": 4,
                "inherited_access_group_ids": [],
                "is_public": True,
            },
        )
        self.assert_model_not_exists("meeting_mediafile/9")

    def test_move_published_to_published_parent_meeting_data(self) -> None:
        self.create_meeting(1)
        self.create_meeting(4)
        self.create_meeting(7)
        self.set_models(
            {
                "meeting/1": {"meeting_mediafile_ids": [1]},
                "group/3": {"meeting_mediafile_inherited_access_group_ids": [1]},
                "meeting/4": {"meeting_mediafile_ids": [4]},
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "meeting_mediafile_ids": [1, 4],
                },
                "meeting_mediafile/1": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "inherited_access_group_ids": [1, 3],
                    "is_public": False,
                },
                "meeting_mediafile/4": {
                    "meeting_id": 4,
                    "mediafile_id": 1,
                },
                "mediafile/2": {
                    "parent_id": 4,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "child_ids": [3],
                    "meeting_mediafile_ids": [2, 8],
                },
                "meeting_mediafile/2": {
                    "meeting_id": 1,
                    "mediafile_id": 2,
                    "access_group_ids": [2, 3],
                    "inherited_access_group_ids": [2],
                    "is_public": False,
                },
                "meeting_mediafile/8": {
                    "meeting_id": 7,
                    "mediafile_id": 2,
                    "access_group_ids": [],
                    "inherited_access_group_ids": [],
                    "is_public": True,
                },
                "mediafile/3": {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "parent_id": 2,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "meeting_mediafile_ids": [3, 6, 9],
                },
                "meeting_mediafile/3": {
                    "meeting_id": 1,
                    "mediafile_id": 3,
                    "access_group_ids": [1, 2],
                    "inherited_access_group_ids": [2],
                    "is_public": False,
                },
                "meeting_mediafile/6": {
                    "meeting_id": 4,
                    "mediafile_id": 3,
                    "access_group_ids": [6],
                    "inherited_access_group_ids": [6],
                    "is_public": False,
                },
                "meeting_mediafile/9": {
                    "meeting_id": 7,
                    "mediafile_id": 3,
                    "access_group_ids": [9],
                    "inherited_access_group_ids": [9],
                    "is_public": False,
                },
                "mediafile/4": {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "child_ids": [2],
                },
            }
        )
        response = self.request(
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [2], "parent_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/2",
            {
                "parent_id": 1,
                "child_ids": [3],
                "meeting_mediafile_ids": [2, 8, 10],
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "meeting_id": 1,
                "mediafile_id": 2,
                "access_group_ids": [2, 3],
                "inherited_access_group_ids": [3],
                "is_public": False,
            },
        )

        # Should calculate admin group for inherited_access_group_ids
        # if the parent doesn't have a meeting_mediafile
        self.assert_model_exists(
            "meeting_mediafile/8",
            {
                "meeting_id": 7,
                "mediafile_id": 2,
                "access_group_ids": [],
                "inherited_access_group_ids": [8],
                "is_public": False,
            },
        )

        self.assert_model_exists(
            "meeting_mediafile/10",
            {
                "meeting_id": 4,
                "mediafile_id": 2,
                "inherited_access_group_ids": [],
                "is_public": True,
            },
        )

        self.assert_model_exists(
            "mediafile/3",
            {
                "parent_id": 2,
                "meeting_mediafile_ids": [3, 6, 9],
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/3",
            {
                "mediafile_id": 3,
                "meeting_id": 1,
                "access_group_ids": [1, 2],
                "inherited_access_group_ids": [],
                "is_public": False,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/6",
            {
                "mediafile_id": 3,
                "meeting_id": 4,
                "access_group_ids": [6],
                "inherited_access_group_ids": [6],
                "is_public": False,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/9",
            {
                "mediafile_id": 3,
                "meeting_id": 7,
                "access_group_ids": [9],
                "inherited_access_group_ids": [],
                "is_public": False,
            },
        )
        self.assert_model_not_exists("meeting_mediafile/11")
        self.assert_model_exists("mediafile/4", {"parent_id": None, "child_ids": []})

    def test_move_published_to_unpublished_parent_meeting_data(self) -> None:
        self.create_meeting(1)
        self.create_meeting(4)
        self.create_meeting(7)
        self.set_models(
            {
                "meeting/1": {"meeting_mediafile_ids": [1]},
                "group/3": {"meeting_mediafile_inherited_access_group_ids": [1]},
                "meeting/4": {"meeting_mediafile_ids": [4]},
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                },
                "mediafile/2": {
                    "parent_id": 4,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "child_ids": [3],
                    "meeting_mediafile_ids": [2, 8],
                },
                "meeting_mediafile/2": {
                    "meeting_id": 1,
                    "mediafile_id": 2,
                    "access_group_ids": [2, 3],
                    "inherited_access_group_ids": [2],
                    "is_public": False,
                },
                "meeting_mediafile/8": {
                    "meeting_id": 7,
                    "mediafile_id": 2,
                    "access_group_ids": [],
                    "inherited_access_group_ids": [],
                    "is_public": True,
                },
                "mediafile/3": {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "parent_id": 2,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "meeting_mediafile_ids": [3, 6, 9],
                },
                "meeting_mediafile/3": {
                    "meeting_id": 1,
                    "mediafile_id": 3,
                    "access_group_ids": [1, 2],
                    "inherited_access_group_ids": [2],
                    "is_public": False,
                },
                "meeting_mediafile/6": {
                    "meeting_id": 4,
                    "mediafile_id": 3,
                    "access_group_ids": [6],
                    "inherited_access_group_ids": [6],
                    "is_public": False,
                },
                "meeting_mediafile/9": {
                    "meeting_id": 7,
                    "mediafile_id": 3,
                    "access_group_ids": [9],
                    "inherited_access_group_ids": [9],
                    "is_public": False,
                },
                "mediafile/4": {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "child_ids": [2],
                },
            }
        )
        response = self.request(
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [2], "parent_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/2",
            {
                "parent_id": 1,
                "child_ids": [3],
                "meeting_mediafile_ids": [],
                "published_to_meetings_in_organization_id": None,
            },
        )
        for id_ in [2, 3, 6, 8, 9]:
            self.assert_model_deleted(f"meeting_mediafile/{id_}")

        self.assert_model_exists(
            "mediafile/3",
            {
                "parent_id": 2,
                "meeting_mediafile_ids": [],
                "published_to_meetings_in_organization_id": None,
            },
        )
        self.assert_model_not_exists("meeting_mediafile/10")

    def test_move_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.move",
            {"owner_id": "meeting/1", "ids": [8], "parent_id": 7},
        )

    def test_move_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.move",
            {"owner_id": "meeting/1", "ids": [8], "parent_id": 7},
            Permissions.Mediafile.CAN_MANAGE,
        )

    def test_move_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "mediafile.move",
            {"owner_id": "meeting/1", "ids": [8], "parent_id": 7},
        )

    def test_move_no_permissions_orga(self) -> None:
        self.base_permission_test(
            self.orga_permission_test_models,
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [8], "parent_id": 7},
        )

    def test_move_permissions_orga(self) -> None:
        self.base_permission_test(
            self.orga_permission_test_models,
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [8], "parent_id": 7},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
