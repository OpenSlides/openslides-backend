from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MeetingSettingsSystemTest(BaseActionTestCase):
    def test_group_ids(self) -> None:
        self.create_model(get_fqid("meeting/1"), {"motion_poll_default_group_ids": [1]})
        self.create_model(get_fqid("group/1"), {"used_as_motion_poll_default_id": 1})
        self.create_model(
            get_fqid("group/2"), {"name": "2", "used_as_motion_poll_default_id": None}
        )
        self.create_model(get_fqid("group/3"), {"used_as_motion_poll_default_id": None})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.update",
                    "data": [{"id": 1, "motion_poll_default_group_ids": [2, 3]}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        meeting = self.datastore.get(get_fqid("meeting/1"))
        self.assertEqual(meeting["motion_poll_default_group_ids"], [2, 3])
        group1 = self.datastore.get(get_fqid("group/1"))
        self.assertEqual(group1.get("used_as_motion_poll_default_id"), None)
        group2 = self.datastore.get(get_fqid("group/2"))
        self.assertEqual(group2["used_as_motion_poll_default_id"], 1)
        group3 = self.datastore.get(get_fqid("group/3"))
        self.assertEqual(group3["used_as_motion_poll_default_id"], 1)
