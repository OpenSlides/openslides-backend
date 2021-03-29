from tests.system.action.base import BaseActionTestCase


class ProjectorProject(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {},
                "meeting/2": {},
                "group/1": {"meeting_id": 1},
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
                "weight": 2,
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
                "weight": 2,
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
                "weight": 2,
            },
        )
        self.assert_model_exists(
            "projection/111",
            {"current_projector_id": 75, "history_projector_id": None, "stable": True},
        )

    def test_try_to_store_second_unstable_projection(self) -> None:
        """
        Didn't succeed to store a second unstable projection
        """
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
                "weight": 2,
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
            "projector/23", {"current_projection_ids": [105, 106, 112], "scroll": 80}
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
        self.assert_model_exists(
            "projection/106",
            {
                "content_object_id": "assignment/452",
                "current_projector_id": 23,
                "stable": True,
            },
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

    def test_user_as_content_object_okay(self) -> None:
        self.create_model(
            "user/2",
            {"username": "normal user", "group_$1_ids": [1], "group_$_ids": ["1"]},
        )
        response = self.request(
            "projector.project",
            {"ids": [75], "content_object_id": "user/2", "meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"projection_$1_ids": [112], "projection_$_ids": ["1"]}
        )
        self.assert_model_exists(
            "projector/75",
            {
                "current_projection_ids": [111, 112],
                "history_projection_ids": [110],
                "scroll": 0,
            },
        )
        self.assert_model_exists(
            "projection/112",
            {
                "content_object_id": "user/2",
                "current_projector_id": 75,
                "stable": False,
            },
        )

    def test_temporary_user_as_content_object_okay(self) -> None:
        """
        Although the temporaray user has to have a group, this test checks the temporary user without group set
        """
        self.create_model(
            "user/2",
            {"username": "temporary", "meeting_id": 1},
        )
        response = self.request(
            "projector.project",
            {"ids": [75], "content_object_id": "user/2", "meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"projection_$1_ids": [112], "projection_$_ids": ["1"]}
        )
        self.assert_model_exists(
            "projector/75",
            {
                "current_projection_ids": [111, 112],
                "history_projection_ids": [110],
                "scroll": 0,
            },
        )
        self.assert_model_exists(
            "projection/112",
            {
                "content_object_id": "user/2",
                "current_projector_id": 75,
                "stable": False,
            },
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
            "data must contain ['content_object_id', 'meeting_id', 'ids'] properties",
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
            "The following models do not belong to meeting 2: ['assignment/452', 'projector/23']",
            response.json["message"],
        )

    def test_project_wrong_meeting_by_content_user(self) -> None:
        self.create_model(
            "user/2",
            {"username": "normal user", "group_$1_ids": [1], "group_$_ids": ["1"]},
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
