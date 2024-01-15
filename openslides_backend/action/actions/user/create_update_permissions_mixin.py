from collections import defaultdict
from functools import reduce
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

from openslides_backend.action.action import Action
from openslides_backend.action.relations.relation_manager import RelationManager
from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.services.datastore.interface import DatastoreService
from openslides_backend.shared.exceptions import (
    ActionException,
    MissingPermission,
    PermissionDenied,
)
from openslides_backend.shared.interfaces.env import Env
from openslides_backend.shared.interfaces.logging import LoggingModule
from openslides_backend.shared.interfaces.services import Services
from openslides_backend.shared.mixins.user_scope_mixin import UserScope, UserScopeMixin
from openslides_backend.shared.patterns import fqid_from_collection_and_id

from .user_mixins import UserMixin


class PermissionVarStore:
    def __init__(self, datastore: DatastoreService, user_id: int) -> None:
        self.datastore = datastore
        self.user_id = user_id
        self.user = self.datastore.get(
            fqid_from_collection_and_id("user", self.user_id),
            [
                "organization_management_level",
                "committee_ids",
                "committee_management_ids",
                "meeting_user_ids",
            ],
            lock_result=False,
        )
        self.user_oml = OrganizationManagementLevel(
            self.user.get("organization_management_level")
        )
        self._user_committees: Optional[Set[int]] = None
        self._user_meetings: Optional[Set[int]] = None

    @property
    def user_committees(self) -> Set[int]:
        """Set of committee-ids where the request user has manage rights"""
        if self._user_committees is None:
            (
                self._user_committees,
                self._user_committees_meetings,
            ) = self._get_user_committees_and_meetings()
        return self._user_committees

    @property
    def user_committees_meetings(self) -> Set[int]:
        """Set of meetings where the request user has manage rights from committee"""
        if self._user_committees is None:
            (
                self._user_committees,
                self._user_committees_meetings,
            ) = self._get_user_committees_and_meetings()
        return self._user_committees_meetings

    @property
    def user_meetings(self) -> Set[int]:
        """Set of meetings where the request user has user.can_manage permissions"""
        if self._user_meetings is None:
            self._user_meetings = self._get_user_meetings_with_user_can_manage(
                self.user.get("meeting_user_ids", [])
            )
        return self._user_meetings

    def _get_user_committees_and_meetings(self) -> Tuple[Set[int], Set[int]]:
        """
        Returns a set of committees and a set of meetings
        belonging to those committees, where the request user has minimum
        CommitteeManagementLevel.CAN_MANAGE and is member of committee_id,
        """
        user_committees = set(self.user.get("committee_management_ids") or [])
        if user_committees:
            committees_d = (
                self.datastore.get_many(
                    [
                        GetManyRequest(
                            "committee",
                            list(user_committees),
                            ["meeting_ids"],
                        )
                    ]
                )
                .get("committee", {})
                .values()
            )
            user_meetings = reduce(
                lambda i1, i2: i1 | i2,
                [
                    set(committee.get("meeting_ids", set()))
                    for committee in committees_d
                ],
            )
        else:
            user_meetings = set()
        return user_committees, user_meetings

    def _get_user_meetings_with_user_can_manage(
        self, meeting_user_ids: List[str] = []
    ) -> Set[int]:
        """
        Returns a set of meetings, where the request user has user.can_manage permissions
        """
        user_meetings = set()
        if meeting_user_ids:
            # fetch all group_ids
            all_groups: List[int] = []
            for meeting_user_id in meeting_user_ids:
                meeting_user = self.datastore.get(
                    fqid_from_collection_and_id("meeting_user", meeting_user_id),
                    ["group_ids"],
                )
                group_ids = meeting_user.get("group_ids")
                if group_ids:
                    for group_id in group_ids:
                        if group_id not in all_groups:
                            all_groups.append(group_id)

            # fetch the groups for permissions
            groups = (
                self.datastore.get_many(
                    [
                        GetManyRequest(
                            "group",
                            list(all_groups),
                            ["meeting_id", "permissions", "admin_group_for_meeting_id"],
                        )
                    ]
                )
                .get("group", {})
                .values()
            )

            # use permissions to add the meetings to user_meeting
            for group in groups:
                if Permissions.User.CAN_MANAGE in group.get(
                    "permissions", []
                ) or group.get("admin_group_for_meeting_id"):
                    if group.get("meeting_id"):
                        user_meetings.add(group["meeting_id"])

        return user_meetings


class CreateUpdatePermissionsMixin(UserMixin, UserScopeMixin, Action):
    internal: bool
    permstore: PermissionVarStore
    field_rights: Dict[str, list] = {
        "A": [
            "title",
            "first_name",
            "last_name",
            "username",
            "is_active",
            "is_physical_person",
            "can_change_own_password",
            "gender",
            "pronoun",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
        ],
        "B": [
            "number",
            "structure_level",
            "vote_weight",
            "about_me",
            "comment",
            "vote_delegated_to_id",
            "vote_delegations_from_ids",
            "is_present_in_meeting_ids",
            "is_present",  # participant import
        ],
        "C": ["meeting_id", "group_ids"],
        "D": ["committee_ids", "committee_management_ids"],
        "E": ["organization_management_level"],
        "F": ["default_password"],
        "G": ["is_demo_user"],
        "H": ["saml_id"],
    }

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        """
        Checks the permissions on a per field and user.scope base, details see
        https://github.com/OpenSlides/OpenSlides/wiki/user.update or user.create
        The fields groups and their necessary permissions are also documented there.
        """
        self.assert_not_anonymous()

        if "forwarding_committee_ids" in instance:
            raise PermissionDenied("forwarding_committee_ids is not allowed.")

        if not hasattr(self, "permstore"):
            self.permstore = PermissionVarStore(self.datastore, self.user_id)
        actual_group_fields = self._get_actual_grouping_from_instance(instance)
        if self.permstore.user_oml == OrganizationManagementLevel.SUPERADMIN:
            return None

        # store scope, id and OML-permission for requested user
        (
            self.instance_user_scope,
            self.instance_user_scope_id,
            self.instance_user_oml_permission,
        ) = self.get_user_scope(instance.get("id") or instance)

        self._check_for_higher_OML(actual_group_fields, instance)

        # Ordered by supposed velocity advantages. Changing order only can effect the sequence of detected errors for tests
        self.check_group_H(actual_group_fields["H"])
        self.check_group_E(actual_group_fields["E"], instance)
        self.check_group_D(actual_group_fields["D"], instance)
        self.check_group_C(actual_group_fields["C"], instance)
        self.check_group_B(actual_group_fields["B"], instance)
        self.check_group_A(actual_group_fields["A"])
        self.check_group_F(actual_group_fields["F"])
        self.check_group_G(actual_group_fields["G"])

    def check_group_A(
        self,
        fields: List[str],
    ) -> None:
        """Check Group A: Depending on scope of user to act on"""
        if (
            not fields
            or self.permstore.user_oml >= OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return

        if self.instance_user_scope == UserScope.Organization:
            raise MissingPermission({OrganizationManagementLevel.CAN_MANAGE_USERS: 1})
        if self.instance_user_scope == UserScope.Committee:
            if self.instance_user_scope_id not in self.permstore.user_committees:
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                        CommitteeManagementLevel.CAN_MANAGE: self.instance_user_scope_id,
                    }
                )
        elif (
            self.instance_user_scope_id not in self.permstore.user_committees_meetings
            and self.instance_user_scope_id not in self.permstore.user_meetings
        ):
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", self.instance_user_scope_id),
                ["committee_id"],
                lock_result=False,
            )
            raise MissingPermission(
                {
                    OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                    CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                    Permissions.User.CAN_MANAGE: self.instance_user_scope_id,
                }
            )

    def check_group_B(self, fields: List[str], instance: Dict[str, Any]) -> None:
        """Check Group B meeting fields: Only meeting.permissions for each meeting"""
        if fields:
            meeting_ids = self._meetings_from_group_B_fields_from_instance(instance)
            if diff := meeting_ids - self.permstore.user_meetings:
                raise MissingPermission(
                    {Permissions.User.CAN_MANAGE: meeting_id for meeting_id in diff}
                )

    def check_group_C(self, fields: List[str], instance: Dict[str, Any]) -> None:
        """Check Group C group_ids: OML, CML or meeting.permissions for each meeting"""
        if (
            fields
            and self.permstore.user_oml < OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            touch_meeting_id = instance.get("meeting_id")
            if (
                touch_meeting_id not in self.permstore.user_committees_meetings
                and touch_meeting_id not in self.permstore.user_meetings
            ):
                raise PermissionDenied(
                    f"The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_manage for meeting {touch_meeting_id}"
                )

    def check_group_D(self, fields: List[str], instance: Dict[str, Any]) -> None:
        """Check Group D committee-related fields: OML or CML level for each committee"""
        if (
            fields
            and self.permstore.user_oml < OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            committees = self._get_all_committees_from_instance(instance)
            if diff := committees - self.permstore.user_committees:
                raise MissingPermission(
                    {
                        CommitteeManagementLevel.CAN_MANAGE: committee_id
                        for committee_id in diff
                    }
                )

    def check_group_E(self, fields: List[str], instance: Dict[str, Any]) -> None:
        """Check Group E organization_management_level: OML level necessary"""
        if fields:
            expected_oml = max(
                OrganizationManagementLevel(
                    instance.get("organization_management_level")
                ),
                OrganizationManagementLevel.CAN_MANAGE_USERS,
            )
            if expected_oml > self.permstore.user_oml:
                raise PermissionDenied(
                    f"Your organization management level is not high enough to set a Level of {instance.get('organization_management_level', OrganizationManagementLevel.CAN_MANAGE_USERS.get_verbose_type())}."
                )

    def check_group_F(
        self,
        fields: List[str],
    ) -> None:
        """Check F common fields: scoped permissions necessary, but if instance user has
        an oml-permission, that of the request user must be higher"""
        if not fields:
            return

        if (
            self.instance_user_oml_permission
            or self.instance_user_scope == UserScope.Organization
        ):
            if self.instance_user_oml_permission:
                expected_oml_permission = OrganizationManagementLevel(
                    self.instance_user_oml_permission
                )
            else:
                expected_oml_permission = OrganizationManagementLevel.CAN_MANAGE_USERS
            if expected_oml_permission > self.permstore.user_oml:
                raise MissingPermission({expected_oml_permission: 1})
            else:
                return
        else:
            if self.permstore.user_oml >= OrganizationManagementLevel.CAN_MANAGE_USERS:
                return
        if self.instance_user_scope == UserScope.Committee:
            if self.instance_user_scope_id not in self.permstore.user_committees:
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                        CommitteeManagementLevel.CAN_MANAGE: self.instance_user_scope_id,
                    }
                )
        elif (
            self.instance_user_scope_id not in self.permstore.user_committees_meetings
            and self.instance_user_scope_id not in self.permstore.user_meetings
        ):
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", self.instance_user_scope_id),
                ["committee_id"],
                lock_result=False,
            )
            raise MissingPermission(
                {
                    OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                    CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                    Permissions.User.CAN_MANAGE: self.instance_user_scope_id,
                }
            )

    def check_group_G(self, fields: List[str]) -> None:
        """Group G: OML SUPERADMIN necessary"""
        if fields and self.permstore.user_oml < OrganizationManagementLevel.SUPERADMIN:
            raise MissingPermission(OrganizationManagementLevel.SUPERADMIN)

    def check_group_H(
        self,
        fields: List[str],
    ) -> None:
        """
        Check Group H: Like group A, but only on internal calls, which will never call
        the check_permissions automatically or oml.can_manage_user permission in user.create
        """
        if fields and not (
            self.internal
            or (
                self.name == "user.create"
                and self.permstore.user_oml
                >= OrganizationManagementLevel.CAN_MANAGE_USERS
            )
        ):
            msg = "The field 'saml_id' can only be used in internal action calls"
            if self.name == "user.create":
                msg += f" or with {OrganizationManagementLevel.CAN_MANAGE_USERS} permission"
            raise ActionException(msg)

    def _check_for_higher_OML(
        self,
        fields: Dict[str, List[str]],
        instance: Dict[str, Any],
    ) -> None:
        # groups B and C are meeting-specific and therefore allowed to be changed, even by lower-OML users
        if "id" in instance and any(
            fields[group] for group in fields.keys() if group not in ["B", "C"]
        ):
            if (
                OrganizationManagementLevel(self.instance_user_oml_permission)
                > self.permstore.user_oml
            ):
                raise PermissionDenied(
                    f"Your organization management level is not high enough to change a user with a Level of {self.instance_user_oml_permission}!"
                )

    def _get_actual_grouping_from_instance(
        self, instance: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Returns a dictionary with an entry for each field group A-E with
        a list of fields from payload instance.
        The field groups A-F refer to https://github.com/OpenSlides/OpenSlides/wiki/user.create
        or user.update
        """
        act_grouping: Dict[str, List[str]] = defaultdict(list)
        for key, _ in instance.items():
            for group in self.field_rights.keys():
                if key in self.field_rights[group]:
                    act_grouping[group].append(key)
                    break
            else:
                if key not in ["id"]:
                    raise PermissionDenied(
                        f"There is no field group for field {key} in payload"
                    )
        return act_grouping

    def _get_all_committees_from_instance(self, instance: Dict[str, Any]) -> Set[int]:
        """
        Gets a Set of all committees from the instance regarding committees from group D.
        To get committees, that should be removed from cml, the user must be read.
        """
        committees = set(instance.get("committee_management_ids") or [])
        if instance_user_id := instance.get("id"):
            user = self.datastore.get(
                fqid_from_collection_and_id("user", instance_user_id),
                ["committee_management_ids"],
                lock_result=False,
                use_changed_models=False,
            )
            committees_existing = set(user.get("committee_management_ids") or [])
            # Just changes with ^ symmetric_difference operat
            committees = committees ^ committees_existing

        return committees

    def _meetings_from_group_B_fields_from_instance(
        self, instance: Dict[str, Any]
    ) -> Set[int]:
        """
        Gets a set of all meetings from the curious field is_present_in_meeting_ids.
        The meeting_id don't belong explicitly to group B and is only added, if there is
        any other group B field.
        """
        meetings: Set[int] = set(instance.get("is_present_in_meeting_ids", []))
        meetings.add(cast(int, instance.get("meeting_id")))
        return meetings


class CreateUpdatePermissionsFailingFields(CreateUpdatePermissionsMixin):
    def __init__(
        self,
        permstore: PermissionVarStore,
        services: Services,
        datastore: DatastoreService,
        relation_manager: RelationManager,
        logging: LoggingModule,
        env: Env,
        skip_archived_meeting_check: Optional[bool] = None,
        use_meeting_ids_for_archived_meeting_check: Optional[bool] = None,
    ) -> None:
        self.permstore = permstore
        super().__init__(
            services,
            datastore,
            relation_manager,
            logging,
            env,
            skip_archived_meeting_check,
            use_meeting_ids_for_archived_meeting_check,
        )

    def get_failing_fields(self, instance: Dict[str, Any]) -> List[str]:
        """
        Checks the permissions on a per field and user.scope base, details see
        https://github.com/OpenSlides/OpenSlides/wiki/user.update or user.create
        The fields groups and their necessary permissions are also documented there.

        This check here should be used in imports, where not permitted fields
        will be stripped by the import. They are caught here.
        The group C can't fail, because one of user.can_manage, committee- or oml-rights
        is the minimum permission for this import action.
        group[H] fields are internal, but generally allowed in import.
        Therefore they have to be checked like group[A] fields
        """

        if self.permstore.user_oml == OrganizationManagementLevel.SUPERADMIN:
            return []

        # store scope, id and OML-permission for requested user
        (
            self.instance_user_scope,
            self.instance_user_scope_id,
            self.instance_user_oml_permission,
        ) = self.get_user_scope(instance.get("id") or instance)

        actual_group_fields = self._get_actual_grouping_from_instance(instance)

        """ group[H] fields are internal, but generally allowed in import.
        They have to be checked like group[A] fields"""
        if actual_group_fields["H"]:
            actual_group_fields["A"] += actual_group_fields["H"]
        failing_fields: List[str] = []
        for method, fields, inst_param in [
            (self.check_group_E, actual_group_fields["E"], instance),
            (self.check_group_D, actual_group_fields["D"], instance),
            (self.check_group_B, actual_group_fields["B"], instance),
            (self.check_group_A, actual_group_fields["A"], None),
            (self.check_group_F, actual_group_fields["F"], None),
            (self.check_group_G, actual_group_fields["G"], None),
        ]:
            try:
                if inst_param is None:
                    cast(Callable[[List[str]], None], method)(fields)
                else:
                    cast(Callable[[List[str], Dict[str, Any]], None], method)(
                        fields, inst_param
                    )
            except PermissionDenied:
                failing_fields += fields
        return failing_fields

    def get_all_checked_fields(self) -> Set[str]:
        all_fields = set()
        for letter in "ABDEFGH":
            all_fields.update(self.field_rights[letter])
        return all_fields
