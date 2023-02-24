from copy import deepcopy
from typing import Any, Dict, List, Optional, Set

from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.shared.typing import HistoryInformation
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....action.action import Action
from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import fqid_from_collection_and_id, FullQualifiedId
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
        self.check_meeting_and_users(instance, fqid_from_collection_and_id("user", instance["id"]))
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
                raise ActionException("Transfer data need meeting_id.")
            meeting_user_data["meeting_id"] = meeting_id
            meeting_user_data["user_id"] = instance["id"]
            self.execute_other_action(MeetingUserSetData, [meeting_user_data])


class UpdateHistoryMixin(Action):
    def get_history_information(self) -> Optional[HistoryInformation]:
        # Currently not working, will be reimplemented after template fields are fully removed
        return None
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
            )
            # Only keep the fields that are different
            instance = {
                field: value
                for field, value in instance.items()
                if value != db_instance.get(field)
            }

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

            # meeting specific data
            meeting_ids: Set[str] = set()
            for field in ("structure_level_$", "number_$", "vote_weight_$"):
                if field in instance:
                    meeting_ids.update(instance[field] or set())
            if len(meeting_ids) == 1:
                meeting_id = meeting_ids.pop()
                instance_information.extend(
                    [
                        "Participant data updated in meeting {}",
                        fqid_from_collection_and_id("meeting", meeting_id),
                    ]
                )
            elif len(meeting_ids) > 1:
                instance_information.append(
                    "Participant data updated in multiple meetings"
                )

            # groups
            if "group_$_ids" in instance:
                group_ids_from_instance = self.get_group_ids_from_instance(instance)
                group_ids_from_db = self.get_group_ids_from_db(instance)
                added = group_ids_from_instance - group_ids_from_db
                removed = group_ids_from_db - group_ids_from_instance

                group_information: List[str] = []
                changed = added | removed
                result = self.datastore.get_many(
                    [
                        GetManyRequest(
                            "group",
                            list(changed),
                            ["meeting_id", "default_group_for_meeting_id"],
                        )
                    ]
                )
                # remove default groups
                groups = result.get("group", {})
                default_groups = {
                    id
                    for id, group in groups.items()
                    if group.get("default_group_for_meeting_id")
                }
                if len(changed) > 1:
                    added -= default_groups
                    removed -= default_groups
                    changed = added | removed
                if added and removed:
                    group_information.append("Groups changed")
                else:
                    if added:
                        group_information.append("Participant added to")
                    else:
                        group_information.append("Participant removed from")
                    if len(changed) == 1:
                        group_information[0] += " group {}"
                        changed_group = changed.pop()
                        group_information.append(
                            fqid_from_collection_and_id("group", changed_group)
                        )
                    else:
                        group_information[0] += " multiple groups"

                meeting_ids = {group["meeting_id"] for group in groups.values()}
                if len(meeting_ids) == 1:
                    group_information[0] += " in meeting {}"
                    meeting_id = meeting_ids.pop()
                    group_information.append(
                        fqid_from_collection_and_id("meeting", meeting_id)
                    )
                else:
                    group_information[0] += " in multiple meetings"
                instance_information.extend(group_information)

            # other fields
            if "organization_management_level" in instance:
                instance_information.append("Organization Management Level changed")
            if "committee_$_management_level" in instance:
                instance_information.append("Committee Management Level changed")
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

    def get_group_ids_from_db(self, instance: Dict[str, Any]) -> Set[int]:
        user_fqid = fqid_from_collection_and_id("user", instance["id"])
        user_prepare_fetch = self.datastore.get(
            user_fqid, ["group_$_ids"], use_changed_models=False
        )
        if not user_prepare_fetch.get("group_$_ids"):
            return set()
        # You can give partial group_$_ids in the instance.
        # so groups of meetings, which meeting is not in instance,
        # doesn't count.
        fields = [
            f"group_${meeting_id}_ids"
            for meeting_id in user_prepare_fetch["group_$_ids"]
            if f"group_${meeting_id}_ids" in instance
        ]
        group_ids: Set[int] = set()
        user = self.datastore.get(user_fqid, fields, use_changed_models=False)
        for field in fields:
            group_ids.update(user.get(field) or [])
        return group_ids

    def get_group_ids_from_instance(self, instance: Dict[str, Any]) -> Set[int]:
        fields = [
            f"group_${meeting_id}_ids" for meeting_id in (instance["group_$_ids"] or [])
        ]
        group_ids: Set[int] = set()
        for field in fields:
            group_ids.update(instance.get(field) or [])
        return group_ids
