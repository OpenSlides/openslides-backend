from .base import BasePresenterTestCase

TEST_USER_PW = "test"


class TestGetForwardingCommittees(BasePresenterTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(5)

    def test_correct_single(self) -> None:
        self.set_models(
            {
                "committee/2": {
                    "name": "com2",
                    "forward_to_committee_ids": [64],
                }
            }
        )
        status_code, data = self.request("get_forwarding_committees", {"meeting_id": 5})
        assert status_code == 200
        assert data == ["com2"]

    def test_correct_multiple(self) -> None:
        self.set_models(
            {
                f"committee/{id_}": {
                    "name": f"com{id_}",
                    "forward_to_committee_ids": [64],
                }
                for id_ in range(2, 5)
            }
        )
        status_code, data = self.request("get_forwarding_committees", {"meeting_id": 5})
        assert status_code == 200
        assert data == ["com2", "com3", "com4"]

    def test_correct_empty(self) -> None:
        status_code, data = self.request("get_forwarding_committees", {"meeting_id": 5})
        assert status_code == 200
        assert data == []

    def test_missing_committee_id(self) -> None:
        status_code, data = self.request("get_forwarding_committees", {})
        assert status_code == 400
        assert "data must contain ['meeting_id'] properties" == data["message"]

    def test_no_permissions(self) -> None:
        self.set_user_groups(1, [5])
        self.set_organization_management_level(None)
        status_code, data = self.request("get_forwarding_committees", {"meeting_id": 5})
        assert status_code == 403
        assert "Missing permission" in data["message"]

    def test_with_locked_meeting(self) -> None:
        self.set_models({"meeting/5": {"locked_from_inside": True}})
        status_code, data = self.request("get_forwarding_committees", {"meeting_id": 5})
        assert status_code == 403
        assert "Missing permission: motion.can_manage_metadata" in data["message"]
