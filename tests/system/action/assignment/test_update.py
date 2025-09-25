from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AssignmentUpdateActionTest(BaseActionTestCase):
    PERMISSION_TEST_MODELS = {
        "assignment/111": {
            "sequential_number": 1,
            "title": "title_srtgb123",
            "meeting_id": 1,
        },
        "list_of_speakers/23": {
            "content_object_id": "assignment/111",
            "sequential_number": 11,
            "meeting_id": 1,
        },
    }

    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "assignment/111": {
                    "sequential_number": 1,
                    "title": "title_srtgb123",
                    "meeting_id": 1,
                },
                "list_of_speakers/23": {
                    "content_object_id": "assignment/111",
                    "sequential_number": 11,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "assignment.update", {"id": 111, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("assignment/111", {"title": "title_Xcdfgee"})

    def test_update_correct_full_fields(self) -> None:
        self.create_mediafile(1, 1)
        self.set_models(
            {
                "meeting/1": {
                    "assignment_poll_add_candidates_to_list_of_speakers": True
                },
                "assignment/111": {
                    "sequential_number": 1,
                    "title": "title_srtgb123",
                    "meeting_id": 1,
                },
                "list_of_speakers/23": {
                    "content_object_id": "assignment/111",
                    "sequential_number": 11,
                    "meeting_id": 1,
                },
                "meeting_mediafile/11": {
                    "is_public": True,
                    "mediafile_id": 1,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "assignment.update",
            {
                "id": 111,
                "title": "title_Xcdfgee",
                "description": "text_test1",
                "open_posts": 12,
                "phase": "search",
                "default_poll_description": "text_test2",
                "number_poll_candidates": True,
                "attachment_mediafile_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "assignment/111",
            {
                "title": "title_Xcdfgee",
                "attachment_meeting_mediafile_ids": [11],
                "description": "text_test1",
                "open_posts": 12,
                "phase": "search",
                "default_poll_description": "text_test2",
                "number_poll_candidates": True,
            },
        )

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "assignment/111": {
                    "title": "title_srtgb123",
                    "sequential_number": 1,
                    "meeting_id": 1,
                },
                "list_of_speakers/23": {
                    "content_object_id": "assignment/111",
                    "sequential_number": 11,
                    "meeting_id": 1,
                },
            },
        )
        response = self.request(
            "assignment.update", {"id": 112, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("assignment/111")
        assert model.get("title") == "title_srtgb123"

    def prepare_voting_phase_test(
        self, number_of_speakers: int, phase: str = "search"
    ) -> None:
        for i in range(number_of_speakers):
            self.create_user(f"user{i+1}", [3])
        ids = list(range(1, number_of_speakers + 1))
        self.set_models(
            {
                "meeting/1": {
                    "assignment_poll_add_candidates_to_list_of_speakers": True
                },
                "assignment/1": {
                    "title": "assignment_with_candidates",
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "phase": phase,
                },
                "list_of_speakers/1": {
                    "sequential_number": 1,
                    "content_object_id": "assignment/1",
                    "meeting_id": 1,
                },
                **{
                    f"assignment_candidate/{i}": {
                        "meeting_id": 1,
                        "assignment_id": 1,
                        "meeting_user_id": i,
                    }
                    for i in ids
                },
            }
        )

    def test_update_phase_to_voting(self) -> None:
        self.prepare_voting_phase_test(3)
        self.request("speaker.create", {"meeting_user_id": 1, "list_of_speakers_id": 1})
        response = self.request("assignment.update", {"id": 1, "phase": "voting"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("list_of_speakers/1", {"speaker_ids": [1, 2, 3]})
        for id_ in [1, 2, 3]:
            self.assert_model_exists(
                f"speaker/{id_}",
                {"list_of_speakers_id": 1, "meeting_user_id": id_, "meeting_id": 1},
            )

    def test_update_phase_to_voting_empty_los(self) -> None:
        self.prepare_voting_phase_test(3)
        response = self.request(
            "assignment.update",
            {"id": 1, "phase": "voting"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("list_of_speakers/1", {"speaker_ids": [1, 2, 3]})
        for id_ in [1, 2, 3]:
            self.assert_model_exists(
                f"speaker/{id_}",
                {"list_of_speakers_id": 1, "meeting_user_id": id_, "meeting_id": 1},
            )

    def test_update_phase_to_voting_no_candidates(self) -> None:
        self.prepare_voting_phase_test(0)
        response = self.request(
            "assignment.update",
            {"id": 1, "phase": "voting"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("speaker/1")

    def test_update_phase_from_voting_to_voting(self) -> None:
        self.prepare_voting_phase_test(3, "voting")
        response = self.request(
            "assignment.update",
            {"id": 1, "phase": "voting"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("speaker/1")

    def test_update_no_permission(self) -> None:
        self.base_permission_test(
            self.PERMISSION_TEST_MODELS,
            "assignment.update",
            {"id": 111, "title": "title_Xcdfgee"},
        )

    def test_update_permission(self) -> None:
        self.base_permission_test(
            self.PERMISSION_TEST_MODELS,
            "assignment.update",
            {"id": 111, "title": "title_Xcdfgee"},
            Permissions.Assignment.CAN_MANAGE,
        )

    def test_update_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.PERMISSION_TEST_MODELS,
            "assignment.update",
            {"id": 111, "title": "title_Xcdfgee"},
        )
