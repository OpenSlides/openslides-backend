from collections import defaultdict
from collections.abc import Callable
from functools import reduce
from typing import Any, cast

from openslides_backend.action.relations.relation_manager import RelationManager
from openslides_backend.permissions.base_classes import Permission
from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permission_helper import (
    has_committee_management_level,
)
from openslides_backend.permissions.permissions import Permissions, permission_parents
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.services.datastore.interface import DatastoreService
from openslides_backend.shared.base_service_provider import BaseServiceProvider
from openslides_backend.shared.exceptions import (
    ActionException,
    AnyPermission,
    MissingPermission,
    PermissionDenied,
)
from openslides_backend.shared.interfaces.env import Env
from openslides_backend.shared.interfaces.logging import LoggingModule
from openslides_backend.shared.interfaces.services import Services
from openslides_backend.shared.mixins.user_scope_mixin import UserScope, UserScopeMixin
from openslides_backend.shared.patterns import fqid_from_collection_and_id


class PermissionVarStore:
    permission: Permission

    def __init__(
        self,
        datastore: DatastoreService,
        user_id: int,
        manage_permission: Permission = Permissions.User.CAN_MANAGE,
    ) -> None:
        self.datastore = datastore
        self.user_id = user_id
        self.permission = manage_permission
        self.all_permissions = [self.permission, *permission_parents[self.permission]]
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
        self._user_committees: set[int] | None = None
        self._user_meetings: set[int] | None = None

    @property
    def user_committees(self) -> set[int]:
        """Set of committee-ids where the request user has manage rights"""
        if self._user_committees is None:
            (
                self._user_committees,
                self._user_committees_meetings,
            ) = self._get_user_committees_and_meetings()
        return self._user_committees

    @property
    def user_committees_meetings(self) -> set[int]:
        """Set of meetings where the request user has manage rights from committee"""
        if self._user_committees is None:
            (
                self._user_committees,
                self._user_committees_meetings,
            ) = self._get_user_committees_and_meetings()
        return self._user_committees_meetings

    @property
    def user_meetings(self) -> set[int]:
        """Set of meetings where the request user has user.can_manage/can_update permissions"""
        if self._user_meetings is None:
            self._user_meetings = self._get_user_meetings_with_permission(
                self.user.get("meeting_user_ids", [])
            )
        return self._user_meetings

    def _get_user_committees_and_meetings(self) -> tuple[set[int], set[int]]:
        """
        Returns a set of committees and a set of meetings
        belonging to those committees, where the request user has minimum
        CommitteeManagementLevel.CAN_MANAGE and is member of committee_id,
        """
        user_committees = set(self.user.get("committee_management_ids") or [])
        if user_committees:
            committees_d = list(
                self.datastore.get_many(
                    [
                        GetManyRequest(
                            "committee",
                            list(user_committees),
                            ["meeting_ids", "all_child_ids"],
                        )
                    ]
                )
                .get("committee", {})
                .values()
            )
            child_ids = {
                child_id
                for committee in committees_d
                for child_id in committee.get("all_child_ids", [])
                if child_id not in user_committees
            }
            user_committees.update(child_ids)
            if len(child_ids):
                committees_d.extend(
                    self.datastore.get_many(
                        [
                            GetManyRequest(
                                "committee",
                                list(child_ids),
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

    def _get_user_meetings_with_permission(
        self, meeting_user_ids: list[str] = []
    ) -> set[int]:
        """
        Returns a set of meetings, where the request user has user.can_manage/can_update permissions
        """
        user_meetings = set()
        if meeting_user_ids:
            # fetch all group_ids
            all_groups: list[int] = []
            for meeting_user_id in meeting_user_ids:
                meeting_user = self.datastore.get(
                    fqid_from_collection_and_id("meeting_user", meeting_user_id),
                    ["group_ids", "locked_out"],
                )
                group_ids = (
                    meeting_user.get("group_ids")
                    if not meeting_user.get("locked_out")
                    else []
                )
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
                if any(
                    [
                        permission in group.get("permissions", [])
                        for permission in self.all_permissions
                    ]
                ) or group.get("admin_group_for_meeting_id"):
                    if group.get("meeting_id"):
                        user_meetings.add(group["meeting_id"])

        return user_meetings


class CreateUpdatePermissionsMixin(UserScopeMixin, BaseServiceProvider):
    permstore: PermissionVarStore
    permission: Permission
    internal: bool

    field_rights: dict[str, list] = {
        "A": [
            "title",
            "first_name",
            "last_name",
            "username",
            "is_active",
            "is_physical_person",
            "can_change_own_password",
            "gender_id",
            "pronoun",
            "email",
            "default_vote_weight",
            "member_number",
        ],
        "B": [
            "number",
            "vote_weight",
            "about_me",
            "comment",
            "structure_level_ids",
            "vote_delegated_to_id",
            "vote_delegations_from_ids",
            "is_present_in_meeting_ids",
            "locked_out",
            "is_present",  # participant import
        ],
        "C": ["meeting_id", "group_ids"],
        "D": ["committee_management_ids"],
        "E": ["organization_management_level"],
        "F": ["default_password"],
        "G": ["is_demo_user"],
        "H": ["saml_id"],
        "I": ["home_committee_id"],
        "J": ["guest"],
    }

    def check_permissions(self, instance: dict[str, Any]) -> None:
        """
        Checks the permissions on a per field and user.scope base, details see
        https://github.com/OpenSlides/OpenSlides/wiki/Users
        https://github.com/OpenSlides/OpenSlides/wiki/Permission-System
        https://github.com/OpenSlides/OpenSlides/wiki/Restrictions-Overview
        The fields groups and their necessary permissions are also documented there.
        Returns true if permissions are given.
        """

        if not hasattr(self, "permstore"):
            self.permstore = PermissionVarStore(
                self.datastore, self.user_id, self.permission
            )
        actual_group_fields = self._get_actual_grouping_from_instance(instance)

        # store scope, scope id, OML-permission and committee ids including the the respective meetings for requested user
        (
            self.instance_user_scope,
            self.instance_user_scope_id,
            self.instance_user_oml_permission,
            self.instance_committee_meeting_ids,
            self.user_in_archived_meetings_only,
            self.instance_home_committee_id,
        ) = self.get_user_scope(instance.get("id") or instance)

        if self.permstore.user_oml != OrganizationManagementLevel.SUPERADMIN:
            self._check_for_higher_OML(actual_group_fields, instance)

        instance_meeting_id = instance.get("meeting_id")
        locked_from_inside = False
        if instance_meeting_id:
            locked_from_inside = self.datastore.get(
                fqid_from_collection_and_id("meeting", instance_meeting_id),
                ["locked_from_inside"],
                lock_result=False,
            ).get("locked_from_inside", False)

        # Ordered by supposed speed advantages. Changing order can only effect the sequence of detected errors for tests
        self.check_group_H(actual_group_fields["H"])
        self.check_group_E(actual_group_fields["E"], instance)
        self.check_group_D(actual_group_fields["D"], instance)
        self.check_group_C(actual_group_fields["C"], instance, locked_from_inside)
        self.check_group_B(actual_group_fields["B"], instance, locked_from_inside)
        self.check_group_A(actual_group_fields["A"], instance)
        self.check_group_F(actual_group_fields["F"], instance)
        self.check_group_G(actual_group_fields["G"])
        self.check_group_I(actual_group_fields["I"], instance)
        self.check_group_J(actual_group_fields["J"], instance)

    def check_group_A(self, fields: list[str], instance: dict[str, Any]) -> None:
        """Check Group A: Depending on scope of user to act on"""
        if (
            not fields
            or self.permstore.user_oml >= OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return

        missing_permissions: dict[AnyPermission, int | set[int]] = dict()
        if self.instance_user_scope == UserScope.Organization:
            if not (
                self.permstore.user_committees.intersection(
                    self.instance_committee_meeting_ids
                )
            ):
                missing_permissions = {OrganizationManagementLevel.CAN_MANAGE_USERS: 1}
        elif self.instance_user_scope == UserScope.Committee:
            if self.instance_user_scope_id not in self.permstore.user_committees:
                missing_permissions = {
                    OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                    CommitteeManagementLevel.CAN_MANAGE: self.instance_user_scope_id,
                }
        elif (
            self.instance_user_scope_id not in self.permstore.user_committees_meetings
            and self.instance_user_scope_id not in self.permstore.user_meetings
        ):
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", self.instance_user_scope_id),
                ["committee_id"],
                lock_result=False,
            )
            missing_permissions = {
                OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                self.permission: self.instance_user_scope_id,
            }
        if missing_permissions:
            self._check_missing_permissions_groups_AF(instance, missing_permissions)

    def check_group_B(
        self, fields: list[str], instance: dict[str, Any], locked_from_inside: bool
    ) -> None:
        """Check Group B meeting fields: Only meeting.permissions for each meeting"""
        if (
            self.permstore.user_oml
            < OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
            or locked_from_inside
        ) and fields:
            meeting_ids = self._meetings_from_group_B_fields_from_instance(instance)
            if diff := meeting_ids - (
                self.permstore.user_meetings
                if locked_from_inside
                else {
                    *self.permstore.user_meetings,
                    *self.permstore.user_committees_meetings,
                }
            ):
                raise MissingPermission(
                    {self.permission: meeting_id for meeting_id in diff}
                )

    def check_group_C(
        self, fields: list[str], instance: dict[str, Any], locked_from_inside: bool
    ) -> None:
        """Check Group C group_ids: OML, CML or meeting.permissions for each meeting"""
        if (
            (self.permstore.user_oml < OrganizationManagementLevel.CAN_MANAGE_USERS)
            or locked_from_inside
        ) and fields:
            touch_meeting_id = instance.get("meeting_id")
            if (
                locked_from_inside
                or touch_meeting_id not in self.permstore.user_committees_meetings
            ) and touch_meeting_id not in self.permstore.user_meetings:
                raise PermissionDenied(
                    f"The user needs Permission {self.permission} for meeting {touch_meeting_id}"
                    if locked_from_inside
                    else f"The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission {self.permission} for meeting {touch_meeting_id}"
                )

    def check_group_D(self, fields: list[str], instance: dict[str, Any]) -> None:
        """Check Group D committee-related fields: OML or CML level for each committee"""
        if self.permstore.user_oml != OrganizationManagementLevel.SUPERADMIN and (
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

    def check_group_E(self, fields: list[str], instance: dict[str, Any]) -> None:
        """Check Group E organization_management_level: OML level necessary"""
        if self.permstore.user_oml != OrganizationManagementLevel.SUPERADMIN and fields:
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

    def check_group_F(self, fields: list[str], instance: dict[str, Any]) -> None:
        """Check F common fields: scoped permissions necessary, but if instance user has
        an oml-permission, that of the request user must be higher"""
        if (
            self.permstore.user_oml == OrganizationManagementLevel.SUPERADMIN
            or not fields
        ):
            return

        missing_permissions: dict[AnyPermission, int | set[int]] = dict()
        if (
            self.instance_user_oml_permission
            or self.instance_user_scope == UserScope.Organization
        ):
            if self.instance_user_oml_permission:
                expected_oml_permission = OrganizationManagementLevel(
                    self.instance_user_oml_permission
                )
            else:
                if self.permstore.user_committees.intersection(
                    self.instance_committee_meeting_ids
                ):
                    return
                expected_oml_permission = OrganizationManagementLevel.CAN_MANAGE_USERS
            if expected_oml_permission > self.permstore.user_oml:
                missing_permissions = {expected_oml_permission: 1}
            else:
                return
        elif self.permstore.user_oml >= OrganizationManagementLevel.CAN_MANAGE_USERS:
            return
        elif self.instance_user_scope == UserScope.Committee:
            if self.instance_user_scope_id not in self.permstore.user_committees:
                missing_permissions = {
                    OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                    CommitteeManagementLevel.CAN_MANAGE: self.instance_user_scope_id,
                }
        elif (
            self.instance_user_scope_id not in self.permstore.user_committees_meetings
            and self.instance_user_scope_id not in self.permstore.user_meetings
        ):
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", self.instance_user_scope_id),
                ["committee_id"],
                lock_result=False,
            )
            missing_permissions = {
                OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                self.permission: self.instance_user_scope_id,
            }
        if missing_permissions:
            self._check_missing_permissions_groups_AF(instance, missing_permissions)

    def check_group_G(self, fields: list[str]) -> None:
        """Group G: OML SUPERADMIN necessary"""
        if (
            self.permstore.user_oml != OrganizationManagementLevel.SUPERADMIN
            and fields
            and self.permstore.user_oml < OrganizationManagementLevel.SUPERADMIN
        ):
            raise MissingPermission(OrganizationManagementLevel.SUPERADMIN)

    def check_group_H(
        self,
        fields: list[str],
    ) -> None:
        """
        Check Group H: Like group A, but only on internal calls, which will never call
        the check_permissions automatically or oml.can_manage_user permission in user.create
        """
        if (
            self.permstore.user_oml != OrganizationManagementLevel.SUPERADMIN
            and fields
            and not (
                self.internal
                or (
                    self.name == "user.create"
                    and self.permstore.user_oml
                    >= OrganizationManagementLevel.CAN_MANAGE_USERS
                )
            )
        ):
            msg = "The field 'saml_id' can only be used in internal action calls"
            if self.name == "user.create":
                msg += f" or with {OrganizationManagementLevel.CAN_MANAGE_USERS} permission"
            raise ActionException(msg)

    def check_group_I(self, fields: list[str], instance: dict[str, Any]) -> list[int]:
        """Check Group I committee-related fields: OML or CML level both for setting and unsetting"""
        if (
            fields
            and self.permstore.user_oml
            < OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        ):
            db_instance = (
                {}
                if "id" not in instance
                else self.datastore.get(
                    fqid_from_collection_and_id("user", instance["id"]),
                    ["home_committee_id"],
                    lock_result=False,
                )
            )
            committee_ids: list[int] = []
            for payload in [instance, db_instance]:
                if payload.get("home_committee_id"):
                    committee_ids.append(payload["home_committee_id"])
            if forbidden_committees := {
                committee_id
                for committee_id in committee_ids
                if not has_committee_management_level(
                    self.datastore,
                    self.user_id,
                    CommitteeManagementLevel.CAN_MANAGE,
                    committee_id,
                )
            }:
                raise MissingPermission(
                    {CommitteeManagementLevel.CAN_MANAGE: forbidden_committees}
                )
            return committee_ids
        return []

    def check_group_J(self, fields: list[str], instance: dict[str, Any]) -> None:
        if fields:
            committee_ids = self.check_group_I(fields, instance)
            if not committee_ids:
                self.check_group_A(fields, instance)

    def _check_for_higher_OML(
        self,
        fields: dict[str, list[str]],
        instance: dict[str, Any],
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

    def _check_missing_permissions_groups_AF(
        self,
        instance: dict[str, Any],
        missing_permissions: dict[AnyPermission, int | set[int]],
    ) -> None:
        """
        Conditionally raises MissingPermission exceptions based on shared conditions between groups A and F.
        It functions as follows:
        * If the called user has a home committee it throws an exception with the precalulated missing_permissions that were passed.
        * Else if the caller is not admin in all meetings of the instance user, it throws an exception with the precalulated
           missing_permissions and additionally user.can_update for every one of the related meetings.
        * Else if the user is only in archived meetings it again throws an exception with the precalulated missing_permissions.
        """
        if self.instance_home_committee_id or not self.check_for_admin_in_all_meetings(
            instance.get("id", 0)
        ):
            if not self.instance_home_committee_id:
                missing_permissions.update(
                    {
                        Permissions.User.CAN_UPDATE: {
                            meeting_id
                            for meeting_ids in self.instance_committee_meeting_ids.values()
                            if meeting_ids is not None
                            for meeting_id in meeting_ids
                            if meeting_id is not None
                        },
                    }
                )
            raise MissingPermission(missing_permissions)
        elif self.user_in_archived_meetings_only:
            raise MissingPermission(missing_permissions)

    def _get_actual_grouping_from_instance(
        self, instance: dict[str, Any]
    ) -> dict[str, list[str]]:
        """
        Returns a dictionary with an entry for each field group A-E with
        a list of fields from payload instance.
        The field groups A-F refer to https://github.com/OpenSlides/openslides-meta/blob/main/models.yml
        or https://github.com/OpenSlides/openslides-backend/blob/main/docs/actions/user.create.md
        or https://github.com/OpenSlides/openslides-backend/blob/main/docs/actions/user.update.md
        """
        act_grouping: dict[str, list[str]] = defaultdict(list)
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

    def _get_all_committees_from_instance(self, instance: dict[str, Any]) -> set[int]:
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
        self, instance: dict[str, Any]
    ) -> set[int]:
        """
        Gets a set of all meetings from the curious field is_present_in_meeting_ids.
        The meeting_id don't belong explicitly to group B and is only added, if there is
        any other group B field.
        """
        meetings: set[int] = set(instance.get("is_present_in_meeting_ids", []))
        meeting_id = cast(int, instance.get("meeting_id"))
        if meeting_id:
            meetings.add(meeting_id)
        return meetings


class CreateUpdatePermissionsFailingFields(CreateUpdatePermissionsMixin):
    permission = Permissions.User.CAN_MANAGE

    def __init__(
        self,
        user_id: int,
        permstore: PermissionVarStore,
        services: Services,
        datastore: DatastoreService,
        relation_manager: RelationManager,
        logging: LoggingModule,
        env: Env,
        skip_archived_meeting_check: bool | None = None,
        use_meeting_ids_for_archived_meeting_check: bool | None = None,
    ) -> None:
        self.permstore = permstore
        self.user_id = user_id
        super().__init__(
            services,
            datastore,
            logging,
        )

    def get_failing_fields(
        self, instance: dict[str, Any], groups: str = "ABDEFGHIJ"
    ) -> list[str]:
        """
        Checks the permissions on a per field and user.scope base, details see
        https://github.com/OpenSlides/OpenSlides/wiki/user.update or user.create
        The fields groups and their necessary permissions are also documented there.

        This check here should be used in imports, where not permitted fields
        will be stripped by the import. They are caught here.
        The group C can't fail, because one of user.can_manage/can_update, committee- or oml-rights
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
            self.instance_committee_meeting_ids,
            self.user_in_archived_meetings_only,
            self.instance_home_committee_id,
        ) = self.get_user_scope(instance.get("id") or instance)

        instance_meeting_id = instance.get("meeting_id")
        locked_from_inside = False
        if instance_meeting_id:
            locked_from_inside = self.datastore.get(
                fqid_from_collection_and_id("meeting", instance_meeting_id),
                ["locked_from_inside"],
                lock_result=False,
            ).get("locked_from_inside", False)

        actual_group_fields = self._get_actual_grouping_from_instance(instance)

        """ group[H] fields are internal, but generally allowed in import.
        They have to be checked like group[A] fields"""
        if actual_group_fields["H"]:
            actual_group_fields["A"] += actual_group_fields["H"]
        failing_fields: list[str] = []
        for method, group, inst_param, other_param in [
            tup
            for tup in [
                (self.check_group_E, "E", instance, None),
                (self.check_group_D, "D", instance, None),
                (self.check_group_B, "B", instance, locked_from_inside),
                (self.check_group_A, "A", instance, None),
                (self.check_group_F, "F", instance, None),
                (self.check_group_G, "G", None, None),
                (self.check_group_I, "I", instance, None),
                (self.check_group_J, "J", instance, None),
            ]
            if tup[1] in groups
        ]:
            fields = actual_group_fields[group]
            try:
                if inst_param is None:
                    cast(Callable[[list[str]], None], method)(fields)
                elif other_param is None:
                    cast(Callable[[list[str], dict[str, Any]], None], method)(
                        fields, inst_param
                    )
                else:
                    cast(Callable[[list[str], dict[str, Any], bool], None], method)(
                        fields, inst_param, other_param
                    )
            except PermissionDenied:
                failing_fields += fields
        return failing_fields

    def get_all_checked_fields(self, groups: str = "ABDEFGHIJ") -> set[str]:
        all_fields = set()
        for letter in groups:
            all_fields.update(self.field_rights[letter])
        return all_fields
