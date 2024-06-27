from typing import Any

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import Gender
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import GenderPermissionMixin, GenderUniqueMixin


@register_action("gender.update")
class GenderUpdateAction(
    UpdateAction, CheckForArchivedMeetingMixin, GenderPermissionMixin, GenderUniqueMixin
):
    """
    Action to update a gender.
    """

    model = Gender()
    schema = DefaultSchema(Gender()).get_update_schema(
        required_properties=["name"],
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        super().check_editable(instance)
        instance = super().update_instance(instance)
        return instance
