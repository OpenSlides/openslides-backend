from typing import Any, Dict

from ....permissions.permission_helper import check_not_anonymous
from ....permissions.permissions import OrganisationManagementLevel
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action


class PermissionMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if check_not_anonymous(self.user_id):
            user = self.datastore.get(
                FullQualifiedId(Collection("user"), self.user_id),
                ["organisation_management_level"],
            )
        else:
            user = {}
        if (
            user.get("organisation_management_level")
            == OrganisationManagementLevel.CAN_MANAGE_ORGANISATION
        ):
            return

        msg = f"You are not allowed to perform action {self.name}."
        msg += " Missing can_manage_organisation"
        raise PermissionDenied(msg)
