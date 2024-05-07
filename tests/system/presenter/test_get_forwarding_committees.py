from .base import BasePresenterTestCase

TEST_USER_PW = "test"


class TestGetForwardingCommittees(BasePresenterTestCase):
    def test_correct_single(self) -> None:
        self.set_models(
            {
                "meeting/5": {
                    "committee_id": 1,
                },
                "committee/1": {
                    "name": "committee_1",
                    "receive_forwardings_from_committee_ids": [2],
                },
                "committee/2": {
                    "name": "com2",
                },
            }
        )
        status_code, data = self.request("get_forwarding_committees", {"meeting_id": 5})
        assert status_code == 200
        assert data == ["com2"]

    def test_correct_multiple(self) -> None:
        self.set_models(
            {
                "meeting/5": {
                    "committee_id": 1,
                },
                "committee/1": {
                    "name": "committee_1",
                    "receive_forwardings_from_committee_ids": [2, 3, 4],
                },
                "committee/2": {
                    "name": "com2",
                },
                "committee/3": {
                    "name": "com3",
                },
                "committee/4": {
                    "name": "com4",
                },
            }
        )
        status_code, data = self.request("get_forwarding_committees", {"meeting_id": 5})
        assert status_code == 200
        assert data == ["com2", "com3", "com4"]

    def test_correct_empty(self) -> None:
        self.set_models(
            {
                "meeting/5": {
                    "committee_id": 1,
                },
                "committee/1": {
                    "name": "committee_1",
                },
            }
        )
        status_code, data = self.request("get_forwarding_committees", {"meeting_id": 5})
        assert status_code == 200
        assert data == []

    def test_missing_committee_id(self) -> None:
        status_code, data = self.request("get_forwarding_committees", {})
        assert status_code == 400
        assert "data must contain ['meeting_id'] properties" == data["message"]

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "user/3": {
                    "username": "test",
                    "is_active": True,
                    "default_password": TEST_USER_PW,
                    "password": self.auth.hash(TEST_USER_PW),
                    "meeting_user_ids": [3],
                },
                "meeting_user/3": {
                    "meeting_id": 3,
                    "user_id": 3,
                    "group_ids": [3],
                },
                "meeting/3": {"group_ids": [3]},
                "group/3": {"meeting_id": 3},
            }
        )
        self.client.login("test", TEST_USER_PW)
        status_code, data = self.request("get_forwarding_committees", {"meeting_id": 3})
        assert status_code == 403
        assert "Missing permission" in data["message"]
