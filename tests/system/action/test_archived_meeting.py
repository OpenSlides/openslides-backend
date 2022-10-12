from tests.system.action.base import BaseActionTestCase


class InMeetingActions(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {"name": "test"},
                "motion/1": {
                    "title": "test_title",
                    "meeting_id": 1,
                },
            }
        )

    def test_create_motion(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "test_create",
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Meeting test/1 cannot be changed, because it is archived.",
            response.json["message"],
        )

    def test_update_motion(self) -> None:
        response = self.request(
            "motion.update",
            {
                "id": 1,
                "title": "new_title",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Meeting test/1 cannot be changed, because it is archived.",
            response.json["message"],
        )

    def test_delete_motion(self) -> None:
        response = self.request(
            "motion.delete",
            {
                "id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Meeting test/1 cannot be changed, because it is archived.",
            response.json["message"],
        )


class MeetingActions(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "committee/1": {
                    "name": "committee1",
                    "meeting_ids": [1],
                    "organization_id": 1,
                },
                "meeting/1": {"name": "test", "committee_id": 1, "motion_ids": [1]},
                "motion/1": {
                    "title": "test_title",
                    "meeting_id": 1,
                },
            }
        )

    def test_create_meeting(self) -> None:
        response = self.request(
            "meeting.create",
            {
                "name": "test_meeting",
                "committee_id": 1,
                "language": "en",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "name": "test_meeting"}
        )

    def test_update_meeting(self) -> None:
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "name": "test meeting new",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Meeting test/1 cannot be changed, because it is archived.",
            response.json["message"],
        )

    def test_delete_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_ids": [11, 12],
                    "speaker_ids": [1, 2, 3],
                    "group_ids": [1],
                },
                "group/1": {"user_ids": [2], "meeting_id": 1},
                "user/2": {
                    "username": "user2",
                    "is_active": True,
                    "structure_level_$": ["1", "2"],
                    "structure_level_$1": "Member M1",
                    "structure_level_$2": "Member M2",
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "speaker_$_ids": ["1"],
                    "speaker_$1_ids": [2, 3],
                },
                "list_of_speakers/11": {"meeting_id": 1, "speaker_ids": [1, 2]},
                "speaker/1": {"meeting_id": 1, "list_of_speakers_id": 11, "user_id": 1},
                "speaker/2": {"meeting_id": 1, "list_of_speakers_id": 11, "user_id": 2},
                "list_of_speakers/12": {"meeting_id": 1, "speaker_ids": [3]},
                "speaker/3": {"meeting_id": 1, "list_of_speakers_id": 12, "user_id": 2},
            }
        )
        response = self.request("meeting.delete", {"id": 1})

        self.assert_status_code(response, 200)
        self.assert_model_deleted(
            "meeting/1",
            {
                "is_active_in_organization_id": None,
                "committee_id": 1,
                "group_ids": [1],
                "list_of_speakers_ids": [11, 12],
                "motion_ids": [1],
                "speaker_ids": [1, 2, 3],
            },
        )
        self.assert_model_exists(
            "user/2",
            {
                "group_$1_ids": [],
                "group_$_ids": [],
                "is_active": True,
                "speaker_$1_ids": [],
                "speaker_$_ids": [],
                "structure_level_$": ["1", "2"],
                "structure_level_$1": "Member M1",
                "structure_level_$2": "Member M2",
            },
        )
        self.assert_model_deleted("group/1", {"user_ids": [2], "meeting_id": 1})
        self.assert_model_deleted(
            "list_of_speakers/11",
            {"speaker_ids": [1, 2], "meeting_id": 1},
        )
        self.assert_model_deleted(
            "speaker/2",
            {
                "user_id": 2,
                "list_of_speakers_id": 11,
                "meeting_id": 1,
            },
        )
        self.assert_model_deleted(
            "motion/1",
            {
                "meeting_id": 1,
            },
        )


class OutMeetingActions(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "committee/1": {
                    "name": "committee1",
                    "meeting_ids": [1],
                    "organization_id": 1,
                },
                "meeting/1": {"name": "test", "committee_id": 1},
            }
        )

    def test_change_user_group(self) -> None:
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2]},
                "group/1": {"user_ids": [2], "meeting_id": 1},
                "group/2": {"meeting_id": 1},
                "user/2": {
                    "username": "user2",
                    "is_active": True,
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 2,
                "group_$_ids": {1: [2]},
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Meetings 1 cannot be changed, because they are archived.",
            response.json["message"],
        )

    def test_delete_user(self) -> None:
        self.set_models(
            {
                "meeting/1": {"group_ids": [1], "user_ids": [1, 2]},
                "group/1": {"user_ids": [2], "meeting_id": 1},
                "user/2": {
                    "username": "user2",
                    "is_active": True,
                    "structure_level_$": ["1"],
                    "structure_level_$1": "Member M1",
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                },
            }
        )

        response = self.request(
            "user.delete",
            {
                "id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted(
            "user/2", {"group_$1_ids": [1], "structure_level_$1": "Member M1"}
        )
        self.assert_model_exists("group/1", {"user_ids": []})
        self.assert_model_exists("meeting/1", {"group_ids": [1], "user_ids": [1]})

    def test_delete_organization_tag(self) -> None:
        self.set_models(
            {
                "committee/1": {"organization_tag_ids": [1, 2]},
                "meeting/1": {"organization_tag_ids": [1, 2]},
                "organization_tag/1": {
                    "name": "tag1",
                    "tagged_ids": ["meeting/1", "committee/1"],
                },
                "organization_tag/2": {
                    "name": "tag2",
                    "tagged_ids": ["meeting/1", "committee/1"],
                },
            }
        )
        response = self.request(
            "organization_tag.delete",
            {
                "id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted(
            "organization_tag/1", {"tagged_ids": ["meeting/1", "committee/1"]}
        )
        self.assert_model_exists("committee/1", {"organization_tag_ids": [2]})
        self.assert_model_exists("meeting/1", {"organization_tag_ids": [2]})
