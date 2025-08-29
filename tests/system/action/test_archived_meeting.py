from tests.system.action.base import BaseActionTestCase


class InMeetingActions(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(meeting_data={"is_active_in_organization_id": None})
        self.create_motion(1)

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
            "Meeting OpenSlides/1 cannot be changed, because it is archived.",
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
            "Meeting OpenSlides/1 cannot be changed, because it is archived.",
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
            "Meeting OpenSlides/1 cannot be changed, because it is archived.",
            response.json["message"],
        )


class MeetingActions(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(meeting_data={"is_active_in_organization_id": None})
        self.create_motion(1)

    def test_create_meeting(self) -> None:
        response = self.request(
            "meeting.create",
            {
                "name": "test_meeting",
                "committee_id": 60,
                "language": "en",
                "admin_ids": [1],
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
            "Meeting OpenSlides/1 cannot be changed, because it is archived.",
            response.json["message"],
        )

    def test_delete_meeting(self) -> None:
        self.create_user_for_meeting(1)
        self.set_models(
            {
                "meeting_user/3": {
                    "user_id": 2,
                    "meeting_id": 1,
                },
                "meeting_user/4": {
                    "user_id": 1,
                    "meeting_id": 1,
                },
                "topic/23": {
                    "title": "to pic",
                    "sequential_number": 1,
                    "meeting_id": 1,
                },
                "list_of_speakers/11": {
                    "content_object_id": "topic/23",
                    "sequential_number": 11,
                    "meeting_id": 1,
                },
                "speaker/1": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 11,
                    "meeting_user_id": 4,
                },
                "speaker/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 11,
                    "meeting_user_id": 3,
                },
                "topic/42": {
                    "title": "to pic",
                    "sequential_number": 2,
                    "meeting_id": 1,
                },
                "list_of_speakers/12": {
                    "content_object_id": "topic/42",
                    "sequential_number": 11,
                    "meeting_id": 1,
                },
                "speaker/3": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 12,
                    "meeting_user_id": 3,
                },
            }
        )
        response = self.request("meeting.delete", {"id": 1})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting/1")
        self.assert_model_exists(
            "user/2",
            {
                "is_active": True,
            },
        )
        self.assert_model_not_exists("meeting_user/3")
        self.assert_model_not_exists("group/1")
        self.assert_model_not_exists("list_of_speakers/11")
        self.assert_model_not_exists("speaker/2")
        self.assert_model_not_exists("motion/1")


class OutMeetingActions(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(meeting_data={"is_active_in_organization_id": None})

    def test_change_user_group(self) -> None:
        self.create_user_for_meeting(1)
        response = self.request(
            "meeting_user.update",
            {
                "id": 1,
                "group_ids": [2],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Meeting OpenSlides/1 cannot be changed, because it is archived.",
            response.json["message"],
        )

    def test_delete_user(self) -> None:
        self.set_user_groups(1, [3])
        self.create_user_for_meeting(1)
        response = self.request(
            "user.delete",
            {
                "id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/2")
        self.assert_model_exists("group/1", {"meeting_user_ids": None})
        self.assert_model_exists("meeting/1", {"group_ids": [1, 2, 3], "user_ids": [1]})

    def test_delete_organization_tag(self) -> None:
        self.set_models(
            {
                "organization_tag/1": {
                    "name": "tag1",
                    "tagged_ids": ["meeting/1", "committee/60"],
                    "color": "#333333",
                },
                "organization_tag/2": {
                    "name": "tag2",
                    "tagged_ids": ["meeting/1", "committee/60"],
                    "color": "#333333",
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
        self.assert_model_not_exists("organization_tag/1")
        self.assert_model_exists("committee/60", {"organization_tag_ids": [2]})
        self.assert_model_exists("meeting/1", {"organization_tag_ids": [2]})
