from typing import Any, Dict, List

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....action.action import Action
from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import FullQualifiedId, fqid_from_collection_and_id


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
        self.check_meeting_and_users(instance, user_fqid)
        return instance

    def strip_field(self, field: str, instance: Dict[str, Any]) -> None:
        if instance.get(field):
            instance[field] = instance[field].strip()

    def check_meeting_and_users(
        self, instance: Dict[str, Any], user_fqid: FullQualifiedId
    ) -> None:
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
