from enum import Enum
from typing import Any, Dict, List, Set, Tuple, cast

from openslides_backend.shared.base_service_provider import BaseServiceProvider

from ...models.models import Committee
from ...permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ...permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
    has_perm,
)
from ...permissions.permissions import Permissions
from ...services.datastore.interface import GetManyRequest
from ..exceptions import MissingPermission
from ..patterns import fqid_from_collection_and_id
from ..util_dict_sets import get_set_from_dict_by_fieldlist, get_set_from_dict_from_dict


class UserScope(str, Enum):
    Meeting = "meeting"
    Committee = "committee"
    Organization = "organization"

    def __repr__(self) -> str:
        return repr(self.value)


class UserScopeMixin(BaseServiceProvider):
    def get_user_scope(
        self, id_or_instance: int | Dict[str, Any]
    ) -> Tuple[UserScope, int, str]:
        """
        Returns the scope of the given user id together with the relevant scope id (either meeting,
        committee or organization) and the OML level of the user as string (empty string if the user
        has none). 
        """
        meetings: Set[int] = set()
        committees_manager: Set[int] = set()
        cml_fields = [
            f"committee_${cml_field}_management_level"
            for cml_field in cast(
                List[str], Committee.user__management_level.replacement_enum
            )
        ]
        if isinstance(id_or_instance, dict):
            meetings.update(map(int, id_or_instance.get("group_$_ids", {}).keys()))
            committees_manager.update(
                get_set_from_dict_from_dict(
                    id_or_instance, "committee_$_management_level"
                )
            )
            oml_right = id_or_instance.get("organization_management_level", "")
        else:
            user = self.datastore.get(
                fqid_from_collection_and_id("user", id_or_instance),
                ["meeting_ids", "organization_management_level", *cml_fields],
            )
            meetings.update(user.get("meeting_ids", []))
            committees_manager.update(get_set_from_dict_by_fieldlist(user, cml_fields))
            oml_right = user.get("organization_management_level", "")
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list(meetings),
                    ["committee_id"],
                )
            ]
        ).get("meeting", {})

        meetings_committee: Dict[int, int] = {
            meeting_id: meeting_data["committee_id"]
            for meeting_id, meeting_data in result.items()
        }
        committees = committees_manager | set(meetings_committee.values())
        if len(meetings_committee) == 1 and len(committees) == 1:
            return UserScope.Meeting, next(iter(meetings_committee)), oml_right
        elif len(committees) == 1:
            return UserScope.Committee, next(iter(committees)), oml_right
        return UserScope.Organization, 1, oml_right

    def check_permissions_for_scope(
        self, id: int, always_check_user_oml: bool = True
    ) -> None:
        """
        Checks the permissions for user-altering actions depending on the user scope.
        With check_user_oml_always=True it will be checked whether the request user
        has at minimum the same OML-level than the requested user to pass.
        Reason: A user with OML-level-permission has scope "meeting" or "committee" if
        he belongs to only 1 meeting or 1 committee.
        """
        scope, scope_id, user_oml = self.get_user_scope(id)
        if (
            always_check_user_oml
            and user_oml
            and not has_organization_management_level(
                self.datastore,
                self.user_id,
                perm := OrganizationManagementLevel(user_oml),
            )
        ):
            raise MissingPermission({perm: 1})
        if has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return

        if scope == UserScope.Committee:
            if not has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                scope_id,
            ):
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                        CommitteeManagementLevel.CAN_MANAGE: scope_id,
                    }
                )
        elif scope == UserScope.Meeting:
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", scope_id),
                ["committee_id"],
                lock_result=False,
            )
            if not has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                meeting["committee_id"],
            ) and not has_perm(
                self.datastore, self.user_id, Permissions.User.CAN_MANAGE, scope_id
            ):
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                        CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                        Permissions.User.CAN_MANAGE: scope_id,
                    }
                )
        else:
            raise MissingPermission({OrganizationManagementLevel.CAN_MANAGE_USERS: 1})
