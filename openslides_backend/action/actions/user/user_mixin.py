from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....action.action import Action
from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import (
    FullQualifiedId,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from ...util.assert_belongs_to_meeting import assert_belongs_to_meeting


class UsernameMixin(Action):
    def generate_usernames(self, usernames: List[str]) -> List[str]:
        """
        Generate unique usernames in parallel to a given list of usernames
        """
        used_usernames: List[str] = []
        for username in usernames:
            template_username = username
            count = 0
            while True:
                if username in used_usernames:
                    count += 1
                    username = template_username + str(count)
                    continue
                result = self.datastore.filter(
                    "user",
                    FilterOperator("username", "=", username),
                    ["id"],
                )
                if result:
                    count += 1
                    username = template_username + str(count)
                    continue
                break
            used_usernames.append(username)
        return used_usernames


class LimitOfUserMixin(Action):
    def check_limit_of_user(self, number: int) -> None:
        organization = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["limit_of_users"],
            lock_result=False,
        )
        if limit_of_users := organization.get("limit_of_users"):
            filter_ = FilterOperator("is_active", "=", True)
            count_of_active_users = self.datastore.count("user", filter_)
            if number + count_of_active_users > limit_of_users:
                raise ActionException(
                    "The number of active users cannot exceed the limit of users."
                )


class UserMixin(CheckForArchivedMeetingMixin):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        for field in ("username", "first_name", "last_name", "email"):
            self.strip_field(field, instance)
        user_fqid = fqid_from_collection_and_id("user", instance["id"])
        if "username" in instance:
            if not instance["username"]:
                raise ActionException("This username is forbidden.")
            result = self.datastore.filter(
                "user",
                FilterOperator("username", "=", instance["username"]),
                ["id"],
            )
            if result and instance["id"] not in result.keys():
                raise ActionException(
                    f"A user with the username {instance['username']} already exists."
                )
        self.check_existence_of_to_and_from_users(instance)
        self.check_meeting_and_users(instance, user_fqid)
        if "vote_delegated_$_to_id" in instance:
            self.check_vote_delegated__to_id(instance, user_fqid)
        if "vote_delegations_$_from_ids" in instance:
            self.check_vote_delegations__from_ids(instance, user_fqid)
        return instance

    def strip_field(self, field: str, instance: Dict[str, Any]) -> None:
        if instance.get(field):
            instance[field] = instance[field].strip()

    def check_vote_delegated__to_id(
        self, instance: Dict[str, Any], user_fqid: FullQualifiedId
    ) -> None:
        mapped_fields = [
            f"vote_delegations_${meeting_id}_from_ids"
            for meeting_id, delegated_to in instance["vote_delegated_$_to_id"].items()
            if delegated_to
        ]
        if not mapped_fields:
            return
        user_self = self.datastore.get(user_fqid, mapped_fields, raise_exception=False)
        if "vote_delegations_$_from_ids" in instance:
            update_dict = {
                f"vote_delegations_${meeting_id}_from_ids": delegated_from
                for meeting_id, delegated_from in instance[
                    "vote_delegations_$_from_ids"
                ].items()
            }
            user_self.update(update_dict)
        for meeting_id, delegated_to_id in instance["vote_delegated_$_to_id"].items():
            if id_from_fqid(user_fqid) == delegated_to_id:
                raise ActionException(
                    f"User {delegated_to_id} can't delegate the vote to himself."
                )
            if user_self.get(f"vote_delegations_${meeting_id}_from_ids"):
                raise ActionException(
                    f"User {id_from_fqid(user_fqid)} cannot delegate his vote, because there are votes delegated to him."
                )
            mapped_field = f"vote_delegated_${meeting_id}_to_id"
            user_delegated_to = self.datastore.get(
                fqid_from_collection_and_id("user", delegated_to_id),
                [mapped_field],
            )
            if user_delegated_to.get(mapped_field):
                raise ActionException(
                    f"User {id_from_fqid(user_fqid)} cannot delegate his vote to user {delegated_to_id}, because that user has delegated his vote himself."
                )

    def check_vote_delegations__from_ids(
        self, instance: Dict[str, Any], user_fqid: FullQualifiedId
    ) -> None:
        mapped_fields = [
            f"vote_delegated_${meeting_id}_to_id"
            for meeting_id, delegated_from in instance[
                "vote_delegations_$_from_ids"
            ].items()
            if delegated_from
        ]
        if not mapped_fields:
            return
        user_self = self.datastore.get(user_fqid, mapped_fields, raise_exception=False)
        if "vote_delegated_$_to_id" in instance:
            update_dict = {
                f"vote_delegated_${meeting_id}_to_id": delegated_to
                for meeting_id, delegated_to in instance[
                    "vote_delegated_$_to_id"
                ].items()
            }
            user_self.update(update_dict)
        for meeting_id, delegated_from_ids in instance[
            "vote_delegations_$_from_ids"
        ].items():
            if id_from_fqid(user_fqid) in delegated_from_ids:
                raise ActionException(
                    f"User {id_from_fqid(user_fqid)} can't delegate the vote to himself."
                )
            if user_self.get(f"vote_delegated_${meeting_id}_to_id"):
                raise ActionException(
                    f"User {id_from_fqid(user_fqid)} cannot receive vote delegations, because he delegated his own vote."
                )
            mapped_field = f"vote_delegations_${meeting_id}_from_ids"
            error_user_ids: List[int] = []
            for user_id in delegated_from_ids:
                user = self.datastore.get(
                    fqid_from_collection_and_id("user", user_id),
                    [mapped_field],
                )
                if user.get(mapped_field):
                    error_user_ids.append(user_id)
            if error_user_ids:
                raise ActionException(
                    f"User(s) {error_user_ids} can't delegate their votes because they receive vote delegations."
                )

    def check_existence_of_to_and_from_users(self, instance: Dict[str, Any]) -> None:
        user_ids = set(
            filter(bool, instance.get("vote_delegated_$_to_id", dict()).values())
        )
        if "vote_delegations_$_from_ids" in instance:
            for ids in instance["vote_delegations_$_from_ids"].values():
                if isinstance(ids, list):
                    user_ids.update(ids)
                else:
                    raise ActionException(
                        f"value of vote_delegations_$_from_ids must be a list, but it is type '{type(ids)}'"
                    )

        if user_ids:
            get_many_request = GetManyRequest(
                self.model.collection, list(user_ids), ["id"]
            )
            gm_result = self.datastore.get_many([get_many_request], lock_result=False)
            users = gm_result.get(self.model.collection, {})

            set_action_data = user_ids
            diff = set_action_data.difference(users.keys())
            if len(diff):
                raise ActionException(f"The following users were not found: {diff}")

    def check_meeting_and_users(
        self, instance: Dict[str, Any], user_fqid: FullQualifiedId
    ) -> None:
        meeting_users = defaultdict(list)
        if instance.get("group_$_ids") is not None:
            self.datastore.apply_changed_model(
                user_fqid,
                {
                    **{
                        f"group_${meeting_id}_ids": ids
                        for meeting_id, ids in instance.get("group_$_ids", {}).items()
                    },
                    "meeting_ids": [
                        int(id) for id in instance.get("group_$_ids", {}).keys()
                    ],
                },
            )
        if instance.get("meeting_id") is not None:
            self.datastore.apply_changed_model(
                user_fqid, {"meeting_id": instance.get("meeting_id")}
            )
        for meeting_id, user_id in instance.get("vote_delegated_$_to_id", {}).items():
            if user_id:
                meeting_users[meeting_id].append(
                    fqid_from_collection_and_id("user", user_id)
                )
        for meeting_id, user_ids in instance.get(
            "vote_delegations_$_from_ids", {}
        ).items():
            if user_ids:
                meeting_users[meeting_id].extend(
                    [
                        fqid_from_collection_and_id("user", user_id)
                        for user_id in user_ids
                    ]
                )
        for meeting_id, users in meeting_users.items():
            users.append(user_fqid)
            assert_belongs_to_meeting(self.datastore, users, int(meeting_id))


class UpdateHistoryMixin(Action):
    def get_history_information(self) -> Optional[List[str]]:
        informations: List[str] = []

        # User updated
        for instance in self.instances:
            instance_fields = set(instance.keys())

            update_fields = set(
                [
                    "title",
                    "first_name",
                    "last_name",
                    "email",
                    "username",
                    "default_structure_level",
                    "default_number",
                    "default_vote_weight",
                ]
            )
            if instance_fields & update_fields:
                informations.append("User updated")
                break

        # User updated in meeting x
        all_meetings: List[Set[str]] = []
        for instance in self.instances:
            meeting_ids: Set[str] = set()
            for field in ("structure_level_$", "number_$", "vote_weight_$"):
                if field in instance:
                    meeting_ids.update(instance[field] or set())
            all_meetings.append(meeting_ids)
        if any(all_meetings):
            self.add_to_history(
                informations,
                all_meetings,
                "User updated in meeting {}",
                "User updated in multiple meetings",
            )

        # Group x added/removed
        all_groups_added: List[Set[int]] = []
        all_groups_removed: List[Set[int]] = []
        for instance in self.instances:
            if "group_$_ids" in instance:
                group_ids_from_instance = self.get_group_ids_from_instance(instance)
                group_ids_from_db = self.get_group_ids_from_db(instance)
                added = group_ids_from_instance - group_ids_from_db
                removed = group_ids_from_db - group_ids_from_instance
                all_groups_added.append(added)
                all_groups_removed.append(removed)
        check_added = any(all_groups_added)
        check_removed = any(all_groups_removed)
        if check_added and check_removed:
            informations.append("Groups changed")
        elif check_added:
            self.add_to_history(
                informations, all_groups_added, "Group {} added", "Groups changed"
            )
        elif check_removed:
            self.add_to_history(
                informations, all_groups_removed, "Group {} removed", "Groups changed"
            )

        # OML/CML changed
        for instance in self.instances:
            if (
                "organization_management_level" in instance
                or "committee_$_management_level" in instance
            ):
                informations.append("OML/CML changed")
                break

        # Set (in)active
        for instance in self.instances:
            if "is_active" in instance:
                informations.append("Set (in)active")
                break

        return informations

    def add_to_history(
        self,
        informations: List[str],
        data: List[Set[Any]],
        single_msg: str,
        multi_msg: str,
    ) -> None:
        # assert data not empty
        for entries in data:
            if entries:
                entry_id = list(entries)[0]
                break

        if all([set([entry_id]) == entries for entries in data]):
            informations.append(single_msg.format(entry_id))
        else:
            informations.append(multi_msg)

    def get_group_ids_from_db(self, instance: Dict[str, Any]) -> Set[int]:
        user_fqid = fqid_from_collection_and_id("user", instance["id"])
        user1 = self.datastore.get(user_fqid, ["group_$_ids"], use_changed_models=False)
        if not user1.get("group_$_ids"):
            return set()
        # You can give partial group_$_ids in the instance.
        # so groups of meetings, which meeting is not in instance,
        # doesn't count.
        fields = [
            f"group_${meeting_id}_ids"
            for meeting_id in user1["group_$_ids"]
            if f"group_${meeting_id}_ids" in instance
        ]
        group_ids: Set[int] = set()
        user2 = self.datastore.get(user_fqid, fields, use_changed_models=False)
        for field in fields:
            group_ids.update(user2.get(field) or [])
        return group_ids

    def get_group_ids_from_instance(self, instance: Dict[str, Any]) -> Set[int]:
        fields = [
            f"group_${meeting_id}_ids" for meeting_id in (instance["group_$_ids"] or [])
        ]
        group_ids: Set[int] = set()
        for field in fields:
            group_ids.update(instance.get(field) or [])
        return group_ids
