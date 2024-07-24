from typing import Any, cast

from openslides_backend.services.datastore.commands import GetManyRequest

from ....action.action import Action
from ....action.mixins.meeting_user_helper import get_meeting_user
from ....action.util.typing import ActionData, ActionResults
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import And, Filter, FilterOperator, Or
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import fqid_from_collection_and_id
from .history_mixin import MeetingUserHistoryMixin

meeting_user_standard_fields = [
    "comment",
    "number",
    "vote_weight",
    "structure_level_ids",
    "locked_out",
]


LockingStatusCheckResult = tuple[str, list[int] | None]  # message to broken group ids


class CheckLockOutPermissionMixin(Action):
    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> tuple[WriteRequest | None, ActionResults | None]:
        self.meeting_id_to_can_manage_group_ids: dict[int, set[int]] = {}
        return super().perform(action_data, user_id, internal)

    def check_locking_status(
        self,
        meeting_id: int | None,
        instance: dict[str, Any],
        user_id: int | None = None,
        user: dict[str, Any] | None = None,
        raise_exception: bool = True,
    ) -> list[LockingStatusCheckResult]:
        if not any(
            field in instance
            for field in [
                "locked_out",
                "group_ids",
                "organization_management_level",
                "committee_management_ids",
            ]
        ):
            return []
        result: list[LockingStatusCheckResult] = []
        if meeting_id and (user_id or user):
            db_instance = (
                get_meeting_user(
                    self.datastore,
                    meeting_id,
                    user_id or cast(dict[str, Any], user)["id"],
                    ["locked_out", "group_ids", "meeting_id", "user_id"],
                )
                or {}
            )
        else:
            db_instance = {}
        final: dict[str, Any] = db_instance.copy()
        final.update(instance)
        if not user_id:
            user_id = (user or {}).get("id") or final.get("user_id")
        if user_id == self.user_id and final.get("locked_out"):
            self._add_message(
                "You may not lock yourself out of a meeting", result, raise_exception
            )
        if user_id:
            self._check_setting_oml_cml_for_locking(
                cast(int, user_id),
                final.get("meeting_id"),
                instance,
                result,
                raise_exception,
            )
            if not user:
                try:
                    user = self.datastore.get(
                        fqid_from_collection_and_id("user", cast(int, user_id)),
                        ["organization_management_level", "committee_management_ids"],
                    )
                except Exception as err:
                    if (
                        len(err.args)
                        and isinstance(err.args[0], str)
                        and "does not exist" in err.args[0]
                    ):
                        return result
                    else:
                        raise err
        if not final.get("locked_out"):
            return result
        if user:
            user_copy = user.copy()
            user_copy.update(final)
            final = user_copy
        self._check_setting_locked_for_oml_cml(final, result, raise_exception)
        self._check_setting_locked_for_groups(final, result, raise_exception)
        return result

    def _add_message(
        self,
        message: str,
        result: list[LockingStatusCheckResult],
        raise_exception: bool,
        group_ids: list[int] | None = None,
    ) -> None:
        if raise_exception:
            raise ActionException(message)
        result.append((message, group_ids))

    def _check_setting_locked_for_groups(
        self,
        final: dict[str, Any],
        result: list[LockingStatusCheckResult],
        raise_exception: bool,
    ) -> None:
        if final["meeting_id"] not in self.meeting_id_to_can_manage_group_ids:
            groups = self.datastore.filter(
                "group",
                FilterOperator("meeting_id", "=", final["meeting_id"]),
                ["permissions", "admin_group_for_meeting_id"],
            )
            self.meeting_id_to_can_manage_group_ids[final["meeting_id"]] = {
                id_
                for id_, group in groups.items()
                if group.get("admin_group_for_meeting_id")
                or Permissions.User.CAN_MANAGE in (group.get("permissions") or [])
            }
        forbidden_group_ids = self.meeting_id_to_can_manage_group_ids[
            final["meeting_id"]
        ]
        if forbidden_groups := forbidden_group_ids.intersection(
            final.get("group_ids", [])
        ):
            self._add_message(
                f"Group(s) {', '.join([str(id_) for id_ in forbidden_groups])} have user.can_manage permissions and may therefore not be used by users who are locked out",
                result,
                raise_exception,
                list(forbidden_groups),
            )

    def _check_setting_locked_for_oml_cml(
        self,
        final: dict[str, Any],
        result: list[LockingStatusCheckResult],
        raise_exception: bool,
    ) -> None:
        if oml := final.get("organization_management_level"):
            self._add_message(
                f"Cannot lock user from meeting {final['meeting_id']} as long as he has the OrganizationManagementLevel {oml}",
                result,
                raise_exception,
            )
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", final["meeting_id"]),
            ["committee_id"],
        )
        if meeting["committee_id"] in (final.get("committee_management_ids") or []):
            self._add_message(
                f"Cannot lock user out of meeting {final['meeting_id']} as he is manager of the meetings committee",
                result,
                raise_exception,
            )

    def _check_setting_oml_cml_for_locking(
        self,
        user_id: int,
        meeting_id: int | None,
        instance: dict[str, Any],
        result: list[LockingStatusCheckResult],
        raise_exception: bool,
    ) -> None:
        if not (
            instance.get("organization_management_level")
            or instance.get("committee_management_ids")
        ):
            return
        filters = [
            FilterOperator("user_id", "=", user_id),
            FilterOperator("locked_out", "=", True),
        ]
        if (new_locked := instance.get("locked_out")) is False and meeting_id:
            filters.append(FilterOperator("meeting_id", "!=", meeting_id))
        filter_: Filter = And(filters)
        if new_locked and meeting_id:
            filter_ = Or(FilterOperator("meeting_id", "=", meeting_id), filter_)
        locked_from_meeting_users = self.datastore.filter(
            "meeting_user", filter_, ["meeting_id"]
        )
        locked_from_meeting_ids = {
            meeting_user["meeting_id"]
            for meeting_user in locked_from_meeting_users.values()
        }
        if len(locked_from_meeting_ids):
            self._check_set_oml_for_locking(
                instance, user_id, locked_from_meeting_ids, result, raise_exception
            )
            self._check_set_cml_for_locking(
                instance, user_id, locked_from_meeting_ids, result, raise_exception
            )

    def _check_set_oml_for_locking(
        self,
        instance: dict[str, Any],
        user_id: int,
        locked_from_meeting_ids: set[int],
        result: list[LockingStatusCheckResult],
        raise_exception: bool,
    ) -> None:
        if (oml := instance.get("organization_management_level")) and len(
            locked_from_meeting_ids
        ):
            self._add_message(
                f"Cannot give OrganizationManagementLevel {oml} to user {user_id} as he is locked out of meeting(s) {', '.join([str(id_) for id_ in locked_from_meeting_ids])}",
                result,
                raise_exception,
            )

    def _check_set_cml_for_locking(
        self,
        instance: dict[str, Any],
        user_id: int,
        locked_from_meeting_ids: set[int],
        result: list[LockingStatusCheckResult],
        raise_exception: bool,
    ) -> None:
        if committee_ids := instance.get("committee_management_ids"):
            committees = self.datastore.get_many(
                [GetManyRequest("committee", committee_ids, ["meeting_ids", "id"])]
            )["committee"]
            meeting_id_to_committee_id = {
                meeting_id: committee["id"]
                for committee in committees.values()
                for meeting_id in committee.get("meeting_ids", [])
            }
            if len(
                forbidden_committee_meeting_ids := locked_from_meeting_ids.intersection(
                    meeting_id_to_committee_id.keys()
                )
            ):
                forbidden_committee_ids = {
                    str(meeting_id_to_committee_id[meeting_id])
                    for meeting_id in forbidden_committee_meeting_ids
                }
                self._add_message(
                    f"Cannot set user {user_id} as manager for committee(s) {', '.join(forbidden_committee_ids)} due to being locked out of meeting(s) {', '.join([str(id_) for id_ in forbidden_committee_meeting_ids])}",
                    result,
                    raise_exception,
                )


class MeetingUserMixin(MeetingUserHistoryMixin):
    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        meeting_user_self = self.datastore.get(
            fqid_from_collection_and_id("meeting_user", instance["id"]),
            [
                "vote_delegated_to_id",
                "vote_delegations_from_ids",
                "user_id",
                "meeting_id",
            ],
            raise_exception=False,
        )
        if "vote_delegations_from_ids" in instance:
            meeting_user_self.update(
                {"vote_delegations_from_ids": instance["vote_delegations_from_ids"]}
            )
        if "vote_delegated_to_id" in instance:
            meeting_user_self.update(
                {"vote_delegated_to_id": instance["vote_delegated_to_id"]}
            )

        user_id_self = meeting_user_self.get("user_id", instance.get("user_id"))
        meeting_id_self = meeting_user_self.get(
            "meeting_id", instance.get("meeting_id")
        )

        if "vote_delegated_to_id" in instance:
            self.check_vote_delegated_to_id(
                instance, meeting_user_self, user_id_self, meeting_id_self
            )
        if "vote_delegations_from_ids" in instance:
            self.check_vote_delegations_from_ids(
                instance, meeting_user_self, user_id_self, meeting_id_self
            )
        return instance

    def check_vote_delegated_to_id(
        self,
        instance: dict[str, Any],
        meeting_user_self: dict[str, Any],
        user_id_self: int,
        meeting_id_self: int,
    ) -> None:
        if instance["id"] == instance.get("vote_delegated_to_id"):
            raise ActionException(
                f"User {user_id_self} can't delegate the vote to himself."
            )

        if instance["vote_delegated_to_id"]:
            if meeting_user_self.get("vote_delegations_from_ids"):
                raise ActionException(
                    f"User {user_id_self} cannot delegate his vote, because there are votes delegated to him."
                )
            meeting_user_delegated_to = self.datastore.get(
                fqid_from_collection_and_id(
                    "meeting_user", instance["vote_delegated_to_id"]
                ),
                ["vote_delegated_to_id", "user_id", "meeting_id"],
            )
            if meeting_user_delegated_to.get("meeting_id") != meeting_id_self:
                raise ActionException(
                    f"User {meeting_user_delegated_to.get('user_id')}'s delegation id don't belong to meeting {meeting_id_self}."
                )
            if (
                meeting_user_delegated_to.get("vote_delegated_to_id")
                and instance["id"] != meeting_user_delegated_to["vote_delegated_to_id"]
            ):
                raise ActionException(
                    f"User {user_id_self} cannot delegate his vote to user {meeting_user_delegated_to['user_id']}, because that user has delegated his vote himself."
                )

    def check_vote_delegations_from_ids(
        self,
        instance: dict[str, Any],
        meeting_user_self: dict[str, Any],
        user_id_self: int,
        meeting_id_self: int,
    ) -> None:
        delegated_from_ids = instance["vote_delegations_from_ids"]
        if delegated_from_ids and meeting_user_self.get("vote_delegated_to_id"):
            raise ActionException(
                f"User {user_id_self} cannot receive vote delegations, because he delegated his own vote."
            )
        if instance["id"] in delegated_from_ids:
            raise ActionException(
                f"User {user_id_self} can't delegate the vote to himself."
            )
        vote_error_user_ids: list[int] = []
        meeting_error_user_ids: list[int] = []
        for meeting_user_id in delegated_from_ids:
            meeting_user = self.datastore.get(
                fqid_from_collection_and_id("meeting_user", meeting_user_id),
                ["vote_delegations_from_ids", "user_id", "meeting_id"],
            )
            if meeting_user.get("meeting_id") != meeting_id_self:
                meeting_error_user_ids.append(cast(int, meeting_user.get("user_id")))
            if meeting_user.get("vote_delegations_from_ids") and meeting_user[
                "vote_delegations_from_ids"
            ] != [instance["id"]]:
                vote_error_user_ids.append(cast(int, meeting_user.get("user_id")))
        if meeting_error_user_ids:
            raise ActionException(
                f"User(s) {meeting_error_user_ids} delegation ids don't belong to meeting {meeting_id_self}."
            )
        elif vote_error_user_ids:
            raise ActionException(
                f"User(s) {vote_error_user_ids} can't delegate their votes because they receive vote delegations."
            )
