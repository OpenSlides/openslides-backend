from typing import Any

from .mixins import GenderPermissionMixin, GenderUniqueMixin
from ....models.models import Gender
from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....shared.exceptions import ActionException
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("gender.update")
class GenderUpdateAction(UpdateAction, CheckForArchivedMeetingMixin, GenderPermissionMixin, GenderUniqueMixin):
    """
    Action to update a gender.
    """

    model = Gender() 
    schema = DefaultSchema(Gender()).get_update_schema(
        required_properties=["name"],
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        super().check_editable(instance)
        gender = instance.get("name")
        if gender == "":
            raise ActionException("Empty gender name not allowed.")
        #moved to validate instance
       # gender_dict = self.datastore.get_all("gender", ["id", "name"], lock_result=False)
       # if next((row for row in gender_dict.values() if row["name"] == gender), None):
       #     raise ActionException(f"Gender '{gender}' already exists.")
        instance = super().update_instance(instance)
        return instance
