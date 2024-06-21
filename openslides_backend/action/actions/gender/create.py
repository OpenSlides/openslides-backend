from typing import Any

from .mixins import GenderUniqueMixin
from ....models.models import Gender
from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.util import ONE_ORGANIZATION_ID
from ....shared.exceptions import ActionException
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("gender.create")
class GenderCreate(CreateAction, CheckForArchivedMeetingMixin, GenderUniqueMixin):
    """
    Action to create a gender.
    """

    model = Gender()
    schema = DefaultSchema(Gender()).get_create_schema(
        required_properties=["name"],
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        gender = instance.get("name")
        if gender == "":
            raise ActionException("Empty gender name not allowed.")
       # gender_dict = self.datastore.get_all("gender", ["id", "name"], lock_result=False)
       # if next((row for row in gender_dict.values() if row["name"] == gender), None):
       #     raise ActionException(f"Gender '{gender}' already exists.")
        instance["organization_id"] = ONE_ORGANIZATION_ID
        return instance