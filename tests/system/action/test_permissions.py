from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions

from .base import BaseActionTestCase


class FakeModelP(Model):
    collection = "fake_model_p"
    verbose_name = "fake model for permissions"
    id = fields.IntegerField()
    meeting_id = fields.IntegerField()


@register_action("fake_model_p.create")
class FakeModelPCreate(CreateAction):
    model = FakeModelP()
    schema = {}  # type: ignore
    permission = Permissions.Motion.CAN_CREATE


class TestPermissions(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)

    def test_anonymous_disabled(self) -> None:
        self.set_anonymous(False)
        response = self.request(
            "fake_model_p.create", {"meeting_id": 1}, anonymous=True
        )
        self.assert_status_code(response, 403)
        assert response.json["message"] == "Anonymous is not enabled for meeting 1"

    def test_anonymous_no_permission(self) -> None:
        self.set_anonymous(True)
        # 1 is default group
        self.set_group_permissions(1, [])
        response = self.request(
            "fake_model_p.create", {"meeting_id": 1}, anonymous=True
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action fake_model_p.create. Missing Permission: motion.can_create"
        )

    def test_anonymous_valid(self) -> None:
        self.set_anonymous(True, permissions=[Permissions.Motion.CAN_CREATE])
        response = self.request(
            "fake_model_p.create", {"meeting_id": 1}, anonymous=True
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_p/1")

    def test_not_related_user(self) -> None:
        response = self.request("fake_model_p.create", {"meeting_id": 1})
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action fake_model_p.create. Missing Permission: motion.can_create"
        )

    def test_superadmin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        response = self.request("fake_model_p.create", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_p/1")

    def test_user_in_admin_group(self) -> None:
        # 2 is admin group
        self.set_user_groups(self.user_id, [2])
        response = self.request("fake_model_p.create", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_p/1")

    def test_user_in_some_group(self) -> None:
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_CREATE])
        response = self.request("fake_model_p.create", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_p/1")

    def test_user_has_parent_perm(self) -> None:
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE])
        response = self.request("fake_model_p.create", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_p/1")

    def test_user_has_child_perm(self) -> None:
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        response = self.request("fake_model_p.create", {"meeting_id": 1})
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action fake_model_p.create. Missing Permission: motion.can_create"
        )
