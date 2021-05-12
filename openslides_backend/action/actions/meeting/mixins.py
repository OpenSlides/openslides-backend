from typing import Any, Dict

from ....permissions.management_levels import OrganisationManagementLevel
from ....permissions.permission_helper import has_organisation_management_level
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action


class MeetingPermissionMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if has_organisation_management_level(
            self.datastore, self.user_id, OrganisationManagementLevel.SUPERADMIN
        ):
            return

        committee_id = self.get_committee_id(instance)
        cml_field = f"committee_${committee_id}_management_level"
        user = self.datastore.get(
            FullQualifiedId(Collection("user"), self.user_id), [cml_field]
        )
        is_manager = user.get(cml_field) == "can_manage"
        if not is_manager:
            raise PermissionDenied("Not committee manager.")

    def get_committee_id(self, instance: Dict[str, Any]) -> int:
        return instance["committee_id"]
