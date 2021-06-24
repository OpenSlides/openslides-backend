import time

from tests.system.action.base import BaseActionTestCase


class CommitteeImportMeeting(BaseActionTestCase):
    def test_no_meeting_collection(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "committee.import_meeting", {"id": 1, "meeting_json": {"meeting": []}}
        )
        self.assert_status_code(response, 400)
        assert (
            "Need exact one meeting in meeting collection." in response.json["message"]
        )

    def test_too_many_meeting_collections(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "committee.import_meeting",
            {"id": 1, "meeting_json": {"meeting": [{"id": 1}, {"id": 2}]}},
        )
        self.assert_status_code(response, 400)
        assert (
            "Need exact one meeting in meeting collection." in response.json["message"]
        )

    def test_include_organization(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "committee.import_meeting",
            {
                "id": 1,
                "meeting_json": {"meeting": [{"id": 1}], "organization": [{"id": 1}]},
            },
        )
        self.assert_status_code(response, 400)
        assert "organization must be empty." in response.json["message"]

    def test_not_empty_password(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "committee.import_meeting",
            {
                "id": 1,
                "meeting_json": {
                    "meeting": [{"id": 1}],
                    "user": [{"id": 1, "password": "test"}],
                },
            },
        )
        self.assert_status_code(response, 400)
        assert "User password must be an empty string." in response.json["message"]

    def test_replace_ids_and_write_to_datastore(self) -> None:
        start = round(time.time())
        self.set_models(
            {
                "committee/1": {"meeting_ids": []},
                "meeting/1": {},
                "motion/1": {},
            }
        )
        response = self.request(
            "committee.import_meeting",
            {
                "id": 1,
                "meeting_json": {
                    "meeting": [
                        {
                            "id": 1,
                            "name": "Test",
                            "description": "blablabla",
                            "default_group_id": 1,
                            "motions_default_amendment_workflow_id": 1,
                            "motions_default_statute_amendment_workflow_id": 1,
                            "motions_default_workflow_id": 1,
                            "projector_countdown_default_time": 60,
                            "projector_countdown_warning_time": 60,
                            "reference_projector_id": 1,
                        }
                    ],
                    "user": [
                        {
                            "id": 1,
                            "password": "",
                            "username": "test",
                            "group_$_ids": ["1"],
                            "group_$1_ids": [1],
                        }
                    ],
                    "group": [
                        {"id": 1, "meeting_id": 1, "name": "testgroup", "user_ids": [1]}
                    ],
                    "motion_workflow": [
                        {"id": 1, "meeting_id": 1, "name": "blup", "first_state_id": 1}
                    ],
                    "motion_state": [
                        {
                            "id": 1,
                            "css_class": "line",
                            "meeting_id": 1,
                            "workflow_id": 1,
                            "name": "test",
                        }
                    ],
                    "projector": [{"id": 1, "meeting_id": 1}],
                    "personal_note": [
                        {"id": 1, "meeting_id": 1, "content_object_id": "motion/1"}
                    ],
                    "motion": [
                        {
                            "id": 1,
                            "meeting_id": 1,
                            "list_of_speakers_id": 1,
                            "state_id": 1,
                            "title": "bla",
                        }
                    ],
                    "list_of_speakers": [
                        {"id": 1, "meeting_id": 1, "content_object_id": "motion/1"}
                    ],
                    "tag": [
                        {
                            "id": 1,
                            "meeting_id": 1,
                            "tagged_ids": ["motion/1"],
                            "name": "testag",
                        }
                    ],
                },
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "name": "Test",
                "description": "blablabla",
                "committee_id": 1,
                "enable_anonymous": False,
            },
        )
        meeting_2 = self.get_model("meeting/2")
        assert start <= meeting_2.get("imported_at", 0) <= start + 300
        self.assert_model_exists(
            "user/2", {"username": "test", "group_$2_ids": [1], "group_$_ids": ["2"]}
        )
        user_2 = self.get_model("user/2")
        assert user_2.get("password", "")
        self.assert_model_exists("projector/1", {"meeting_id": 2})
        self.assert_model_exists("group/1", {"user_ids": [2]})
        self.assert_model_exists("personal_note/1", {"content_object_id": "motion/2"})
        self.assert_model_exists(
            "tag/1", {"tagged_ids": ["motion/2"], "name": "testag"}
        )
        self.assert_model_exists("committee/1", {"meeting_ids": [2]})

    def test_check_usernames(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
                "user/1": {"username": "admin"},
            }
        )
        response = self.request(
            "committee.import_meeting",
            {
                "id": 1,
                "meeting_json": {
                    "meeting": [
                        {
                            "id": 1,
                            "name": "Test",
                            "description": "blablabla",
                            "default_group_id": 1,
                            "motions_default_amendment_workflow_id": 1,
                            "motions_default_statute_amendment_workflow_id": 1,
                            "motions_default_workflow_id": 1,
                            "projector_countdown_default_time": 60,
                            "projector_countdown_warning_time": 60,
                            "reference_projector_id": 1,
                        }
                    ],
                    "user": [
                        {
                            "id": 1,
                            "password": "",
                            "username": "admin",
                            "group_$_ids": ["1"],
                            "group_$1_ids": [1],
                        }
                    ],
                    "group": [
                        {"id": 1, "meeting_id": 1, "name": "testgroup", "user_ids": [1]}
                    ],
                    "motion_workflow": [
                        {"id": 1, "meeting_id": 1, "name": "blup", "first_state_id": 1}
                    ],
                    "motion_state": [
                        {
                            "id": 1,
                            "css_class": "line",
                            "meeting_id": 1,
                            "workflow_id": 1,
                            "name": "test",
                        }
                    ],
                    "projector": [{"id": 1, "meeting_id": 1}],
                },
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "admin1"})

    def test_check_usernames_2(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
                "user/1": {"username": "admin"},
            }
        )
        response = self.request(
            "committee.import_meeting",
            {
                "id": 1,
                "meeting_json": {
                    "meeting": [
                        {
                            "id": 1,
                            "name": "Test",
                            "description": "blablabla",
                            "default_group_id": 1,
                            "motions_default_amendment_workflow_id": 1,
                            "motions_default_statute_amendment_workflow_id": 1,
                            "motions_default_workflow_id": 1,
                            "projector_countdown_default_time": 60,
                            "projector_countdown_warning_time": 60,
                            "reference_projector_id": 1,
                        }
                    ],
                    "user": [
                        {
                            "id": 1,
                            "password": "",
                            "username": "admin",
                            "group_$_ids": ["1"],
                            "group_$1_ids": [1],
                        },
                        {
                            "id": 2,
                            "password": "",
                            "username": "admin1",
                        },
                    ],
                    "group": [
                        {"id": 1, "meeting_id": 1, "name": "testgroup", "user_ids": [1]}
                    ],
                    "motion_workflow": [
                        {"id": 1, "meeting_id": 1, "name": "blup", "first_state_id": 1}
                    ],
                    "motion_state": [
                        {
                            "id": 1,
                            "css_class": "line",
                            "meeting_id": 1,
                            "workflow_id": 1,
                            "name": "test",
                        }
                    ],
                    "projector": [{"id": 1, "meeting_id": 1}],
                },
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "admin1"})
        self.assert_model_exists("user/3", {"username": "admin2"})
