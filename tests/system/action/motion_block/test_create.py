from openslides_backend.models.models import AgendaItem
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionBlockActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            "meeting/42",
            {
                "name": "test",
                "agenda_item_creation": "always",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
        response = self.request(
            "motion_block.create", {"title": "test_Xcdfgee", "meeting_id": 42}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_block/1")
        self.assertEqual(model.get("title"), "test_Xcdfgee")
        self.assertEqual(model.get("sequential_number"), 1)
        self.assert_model_exists(
            f"agenda_item/{model['agenda_item_id']}",
            {
                "id": 1,
                "is_hidden": False,
                "is_internal": False,
                "level": 0,
                "type": AgendaItem.AGENDA_ITEM,
                "weight": 1,
                "meeting_id": 42,
                "content_object_id": "motion_block/1",
                "meta_deleted": False,
            },
        )
        self.assert_model_exists(
            "list_of_speakers/1", {"content_object_id": "motion_block/1"}
        )

    def test_create_empty_data(self) -> None:
        response = self.request("motion_block.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'title'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_block.create", {"wrong_field": "text_AefohteiF8"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'title'] properties",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/1": {
                    "name": "test",
                    "agenda_item_creation": "always",
                    "is_active_in_organization_id": 1,
                }
            },
            "motion_block.create",
            {"title": "test_Xcdfgee", "meeting_id": 1},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/1": {
                    "name": "test",
                    "agenda_item_creation": "always",
                    "is_active_in_organization_id": 1,
                }
            },
            "motion_block.create",
            {"title": "test_Xcdfgee", "meeting_id": 1},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "meeting/1": {
                    "name": "test",
                    "agenda_item_creation": "always",
                    "is_active_in_organization_id": 1,
                }
            },
            "motion_block.create",
            {"title": "test_Xcdfgee", "meeting_id": 1},
        )

    def test_create_add_forwarding_relations(
        self, fail_forward_from: bool = False, fail_forward_to: bool = False
    ) -> None:
        self.create_committee(2)
        self.create_committee(3)
        self.create_committee(4)
        self.create_committee(5)
        self.create_committee(6, parent_id=5)
        self.set_models(
            {
                "committee/1": {
                    "forward_to_committee_ids": [2],
                    "receive_forwardings_from_committee_ids": [2],
                },
                "committee/2": {
                    "forward_to_committee_ids": [1],
                    "receive_forwardings_from_committee_ids": [1],
                },
            }
        )
        cmls = [1, 2]
        to_fail = {3, 4, 6}
        if not fail_forward_to:
            cmls.extend([3, 5])
            to_fail.remove(3)
            to_fail.remove(6)
        if not fail_forward_from:
            cmls.append(4)
            to_fail.remove(4)
        self.set_committee_management_level(cmls)
        self.set_organization_management_level(None)
        response = self.request(
            "committee.create",
            {
                "name": "It's in Arameic",
                "organization_id": 1,
                "forward_to_committee_ids": [3, 6],
                "receive_forwardings_from_committee_ids": [2, 4],
            },
        )
        if to_fail:
            self.assert_status_code(response, 403)
            msg: str = response.json["message"]
            self.assertIn(
                "You are not allowed to perform action committee.update. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee",
                msg,
            )
            numbers = {
                int(numstr.strip())
                for numstr in msg.split("{")[1].split("}")[0].split(",")
            }
            assert len(numbers.intersection(to_fail)) == len(to_fail)
        else:
            self.assert_status_code(response, 200)
            self.assert_model_exists(
                "committee/7",
                {
                    "name": "It's in Arameic",
                    "organization_id": 1,
                    "forward_to_committee_ids": [3, 6],
                    "receive_forwardings_from_committee_ids": [2, 4],
                },
            )

    def test_create_add_forwarding_relations_fail_forward_to(self) -> None:
        self.test_create_add_forwarding_relations(fail_forward_to=True)

    def test_create_add_forwarding_relations_fail_forward_from(self) -> None:
        self.test_create_add_forwarding_relations(fail_forward_from=True)

    def test_create_add_forwarding_relations_fail_forward_to_and_from(self) -> None:
        self.test_create_add_forwarding_relations(
            fail_forward_to=True, fail_forward_from=True
        )
