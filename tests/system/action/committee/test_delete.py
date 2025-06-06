from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class CommitteeDeleteActionTest(BaseActionTestCase):
    COMMITTEE_ID = 1
    COMMITTEE_FQID = "committee/1"

    def create_data(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"committee_ids": [self.COMMITTEE_ID]},
                "user/20": {"committee_ids": [self.COMMITTEE_ID]},
                "user/21": {
                    "committee_ids": [self.COMMITTEE_ID],
                    "committee_management_ids": [self.COMMITTEE_ID],
                },
                self.COMMITTEE_FQID: {
                    "organization_id": 1,
                    "user_ids": [20, 21],
                    "manager_ids": [21],
                },
            }
        )

    def test_delete_correct(self) -> None:
        self.create_data()
        self.set_models(
            {
                self.COMMITTEE_FQID: {
                    "organization_tag_ids": [12],
                    "forward_to_committee_ids": [2],
                    "receive_forwardings_from_committee_ids": [3],
                    "organization_id": 1,
                },
                "committee/2": {
                    "receive_forwardings_from_committee_ids": [1],
                    "organization_id": 1,
                },
                "committee/3": {"forward_to_committee_ids": [1], "organization_id": 1},
                "meeting/1": {"user_ids": [20]},
                "user/20": {"meeting_ids": [1]},
                ONE_ORGANIZATION_FQID: {"committee_ids": [1, 2, 3]},
                "organization_tag/12": {
                    "tagged_ids": ["committee/1"],
                    "organization_id": 1,
                },
            }
        )
        response = self.request("committee.delete", {"id": self.COMMITTEE_ID})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists(self.COMMITTEE_FQID)
        self.assert_model_exists("user/20", {"committee_ids": []})
        self.assert_model_exists(
            "user/21",
            {"committee_ids": [], "committee_management_ids": []},
        )
        organization1 = self.get_model(ONE_ORGANIZATION_FQID)
        self.assertCountEqual(organization1["committee_ids"], [2, 3])
        self.assert_model_exists("organization_tag/12", {"tagged_ids": []})
        self.assert_model_exists(
            "committee/2", {"receive_forwardings_from_committee_ids": []}
        )
        self.assert_model_exists("committee/3", {"forward_to_committee_ids": []})

    def test_delete_wrong_id(self) -> None:
        self.create_data()
        response = self.request("committee.delete", {"id": 2})
        self.assert_status_code(response, 400)
        self.assertIn("Model 'committee/2' does not exist.", response.json["message"])
        self.assert_model_exists(self.COMMITTEE_FQID)

    def test_delete_protected_by_meeting(self) -> None:
        self.create_data()
        self.create_model(
            "meeting/22", {"name": "name_meeting_22", "committee_id": self.COMMITTEE_ID}
        )
        self.update_model(self.COMMITTEE_FQID, {"meeting_ids": [22]})

        response = self.request("committee.delete", {"id": self.COMMITTEE_ID})

        self.assert_status_code(response, 400)
        assert (
            "This committee has still a meeting 22. Please remove all meetings before deletion."
            in response.json["message"]
        )
        self.assert_model_exists(self.COMMITTEE_FQID, {"meeting_ids": [22]})

    def test_delete_no_permission(self) -> None:
        self.create_data()
        self.set_models(
            {"user/1": {"organization_management_level": "can_manage_users"}}
        )

        response = self.request("committee.delete", {"id": self.COMMITTEE_ID})
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action committee.delete. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee 1"
            in response.json["message"]
        )

    def test_delete_permission(self) -> None:
        self.create_data()
        self.set_models(
            {"user/1": {"organization_management_level": "can_manage_organization"}}
        )

        response = self.request("committee.delete", {"id": self.COMMITTEE_ID})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists(self.COMMITTEE_FQID)

    def test_delete_with_committee_permission_without_parent(self) -> None:
        self.create_committee(4)
        self.set_committee_management_level([4])
        self.set_organization_management_level(None)
        response = self.request("committee.delete", {"id": 4})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("committee/4")

    def test_delete_with_committee_permission(self) -> None:
        self.create_committee(2)
        self.create_committee(3, parent_id=2)
        self.create_committee(4, parent_id=3)
        self.set_committee_management_level([4])
        self.set_organization_management_level(None)
        response = self.request("committee.delete", {"id": 4})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("committee/4")

    def test_delete_with_parent_committee_permission(self) -> None:
        self.create_committee(3)
        self.create_committee(4, parent_id=3)
        self.set_committee_management_level([3])
        self.set_organization_management_level(None)

        response = self.request("committee.delete", {"id": 4})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("committee/4")

    def test_delete_with_grandparent_committee_permission(self) -> None:
        self.create_committee(2)
        self.create_committee(3, parent_id=2)
        self.create_committee(4, parent_id=3)
        self.set_committee_management_level([2])
        self.set_organization_management_level(None)

        response = self.request("committee.delete", {"id": 4})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("committee/4")

    def test_delete_parent_committee(self) -> None:
        self.create_committee(2)
        self.create_committee(3, parent_id=2)
        self.create_committee(4, parent_id=3)
        response = self.request("committee.delete", {"id": 2})
        self.assert_status_code(response, 400)
        assert (
            "Can't delete committee 2 since it has subcommittees"
            in response.json["message"]
        )

    def test_delete_2_committees_with_forwarding(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"committee_ids": [1, 2]},
                "user/20": {
                    "committee_ids": [1, 2],
                    "committee_management_ids": [1, 2],
                },
                "committee/1": {
                    "organization_id": 1,
                    "user_ids": [20],
                    "manager_ids": [20],
                    "forward_to_committee_ids": [2],
                },
                "committee/2": {
                    "organization_id": 1,
                    "user_ids": [20],
                    "manager_ids": [20],
                    "receive_forwardings_from_committee_ids": [1],
                },
            }
        )
        response = self.request_multi("committee.delete", [{"id": 1}, {"id": 2}])
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("committee/1")
        self.assert_model_not_exists("committee/2")
        self.assert_model_exists(
            "user/20",
            {
                "committee_management_ids": [],
                "committee_ids": [],
            },
        )
