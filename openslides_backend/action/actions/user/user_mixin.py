from copy import deepcopy
from typing import Any, Dict, List, Optional

from openslides_backend.shared.typing import HistoryInformation
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....action.action import Action
from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import FullQualifiedId, fqid_from_collection_and_id
from ....shared.schema import decimal_schema, id_list_schema, required_id_schema
from ..meeting_user.set_data import MeetingUserSetData


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
    transfer_field_list = {
        "comment": {"type": "string"},
        "number": {"type": "string"},
        "structure_level": {"type": "string"},
        "about_me": {"type": "string"},
        "vote_weight": decimal_schema,
        "vote_delegated_to_id": required_id_schema,
        "vote_delegations_from_ids": id_list_schema,
        "group_ids": id_list_schema,
    }

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        for field in ("username", "first_name", "last_name", "email"):
            self.strip_field(field, instance)
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
        self.check_meeting_and_users(
            instance, fqid_from_collection_and_id("user", instance["id"])
        )
        self.meeting_user_set_data(instance)
        return instance

    def strip_field(self, field: str, instance: Dict[str, Any]) -> None:
        if instance.get(field):
            instance[field] = instance[field].strip()

    def check_meeting_and_users(
        self, instance: Dict[str, Any], user_fqid: FullQualifiedId
    ) -> None:
        if instance.get("meeting_id") is not None:
            self.datastore.apply_changed_model(
                user_fqid, {"meeting_id": instance.get("meeting_id")}
            )

    def meeting_user_set_data(self, instance: Dict[str, Any]) -> None:
        meeting_user_data = {}
        meeting_id = instance.pop("meeting_id", None)
        for field in self.transfer_field_list:
            if field in instance:
                meeting_user_data[field] = instance.pop(field)
        if meeting_user_data:
            self.apply_instance(instance)
            if not meeting_id:
                raise ActionException("Transfer data needs meeting_id.")
            meeting_user_data["meeting_id"] = meeting_id
            meeting_user_data["user_id"] = instance["id"]
            self.execute_other_action(MeetingUserSetData, [meeting_user_data])


class UpdateHistoryMixin(Action):
    def get_history_information(self) -> Optional[HistoryInformation]:
        information = {}

        # Scan the instances and collect the info for the history information
        # Copy instances first since they are modified
        for instance in deepcopy(self.instances):
            instance_information = []

            # Fetch the current instance from the db to diff with the given instance
            db_instance = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                list(instance.keys()),
                use_changed_models=False,
                raise_exception=False,
            )
            if not db_instance:
                continue

            # Compare db version with payload
            for field in list(instance.keys()):
                # Remove fields if equal
                if field != "id" and instance[field] == db_instance.get(field):
                    del instance[field]

            # personal data
            update_fields = [
                "title",
                "first_name",
                "last_name",
                "email",
                "username",
                "default_structure_level",
                "default_number",
                "default_vote_weight",
            ]
            if any(field in instance for field in update_fields):
                instance_information.append("Personal data changed")

            # other fields
            if "organization_management_level" in instance:
                instance_information.append("Organization Management Level changed")
            if "committee_management_ids" in instance:
                instance_information.append("Committee management changed")
            if "is_active" in instance:
                if instance["is_active"]:
                    instance_information.append("Set active")
                else:
                    instance_information.append("Set inactive")

            if instance_information:
                information[
                    fqid_from_collection_and_id("user", instance["id"])
                ] = instance_information
        return information
