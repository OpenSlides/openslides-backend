from .base import BasePresenterTestCase


class TestGetForwardingCommittees(BasePresenterTestCase):
    def test_correct_single(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "name": "committee_1",
                    "receive_forwardings_from_committee_ids": [2],
                },
                "committee/2": {
                    "name": "com2",
                },
            }
        )
        status_code, data = self.request(
            "get_forwarding_committees", {"committee_id": 1}
        )
        assert status_code == 200
        assert data == ["com2"]

    def test_correct_multiple(self) -> None:
        self.set_models(
            {
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
        status_code, data = self.request(
            "get_forwarding_committees", {"committee_id": 1}
        )
        assert status_code == 200
        assert data == ["com2", "com3", "com4"]

    def test_correct_empty(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "name": "committee_1",
                },
            }
        )
        status_code, data = self.request(
            "get_forwarding_committees", {"committee_id": 1}
        )
        assert status_code == 200
        assert data == []

    def test_missing_committee_id(self) -> None:
        status_code, data = self.request("get_forwarding_committees", {})
        assert status_code == 400
        assert "data must contain ['committee_id'] properties" == data["message"]
