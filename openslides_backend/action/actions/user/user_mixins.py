import re
from copy import deepcopy
from typing import Any

from openslides_backend.shared.typing import HistoryInformation
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....presenter.search_users import SearchUsers
from ....services.datastore.interface import DatastoreService
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import FullQualifiedId, fqid_from_collection_and_id
from ....shared.schema import decimal_schema, id_list_schema, optional_id_schema
from ...action import Action, original_instances
from ...mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ...util.typing import ActionData
from ..meeting_user.set_data import MeetingUserSetData


class UsernameMixin(Action):
    def generate_usernames(
        self, usernames: list[str], fix_usernames: list[str] | None = None
    ) -> list[str]:
        """
        Generate unique usernames in parallel to a given list of usernames
        """
        if fix_usernames is None:
            fix_usernames = []
        used_usernames: list[str] = []
        for username in usernames:
            template_username = username
            count = 0
            while True:
                if username in used_usernames or username in fix_usernames:
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

    def generate_username(self, entry: dict[str, Any]) -> str:
        return self.generate_usernames(
            [
                re.sub(
                    r"\W",
                    "",
                    entry.get("first_name", "") + entry.get("last_name", ""),
                )
            ]
        )[0]


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
        "about_me": {"type": "string"},
        "vote_weight": decimal_schema,
        "structure_level_ids": id_list_schema,
        "vote_delegated_to_id": optional_id_schema,
        "vote_delegations_from_ids": id_list_schema,
        "group_ids": id_list_schema,
    }

    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        if "meeting_id" not in instance and any(
            key in self.transfer_field_list for key in instance.keys()
        ):
            raise ActionException(
                "Missing meeting_id in instance, because meeting related fields used"
            )

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            for field in ("username", "first_name", "last_name", "email", "saml_id"):
                self.strip_field(field, instance)
        return super().get_updated_instances(action_data)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)

        def check_existence(what: str) -> None:
            if what in instance:
                if not instance[what]:
                    raise ActionException(f"This {what} is forbidden.")
                result = self.datastore.filter(
                    "user",
                    FilterOperator(what, "=", instance[what]),
                    ["id"],
                )
                if result and instance["id"] not in result.keys():
                    raise ActionException(
                        f"A user with the {what} {instance[what]} already exists."
                    )

        check_existence("username")
        check_existence("saml_id")
        check_existence("member_number")

        self.check_meeting_and_users(
            instance, fqid_from_collection_and_id("user", instance["id"])
        )
        self.meeting_user_set_data(instance)
        return instance

    def strip_field(self, field: str, instance: dict[str, Any]) -> None:
        if instance.get(field):
            instance[field] = instance[field].strip()

    def check_meeting_and_users(
        self, instance: dict[str, Any], user_fqid: FullQualifiedId
    ) -> None:
        if instance.get("meeting_id") is not None:
            self.datastore.apply_changed_model(
                user_fqid, {"meeting_id": instance.get("meeting_id")}
            )

    def meeting_user_set_data(self, instance: dict[str, Any]) -> None:
        meeting_user_data = {}
        meeting_id = instance.pop("meeting_id", None)
        for field in self.transfer_field_list:
            if field in instance:
                meeting_user_data[field] = instance.pop(field)
        if meeting_user_data:
            self.apply_instance(instance)
            meeting_user_data["meeting_id"] = meeting_id
            meeting_user_data["user_id"] = instance["id"]
            self.execute_other_action(MeetingUserSetData, [meeting_user_data])


class UpdateHistoryMixin(Action):
    def get_history_information(self) -> HistoryInformation | None:
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
                information[fqid_from_collection_and_id("user", instance["id"])] = (
                    instance_information
                )
        return information


class DuplicateCheckMixin(Action):
    def init_duplicate_set(self, data: list[Any]) -> None:
        self.users_in_double_lists = self.execute_presenter(
            SearchUsers,
            {
                "permission_type": "organization",
                "permission_id": 1,
                "search": data,
            },
        )
        self.used_usernames: list[str] = []
        self.used_saml_ids: list[str] = []
        self.used_names_and_email: list[Any] = []

    def check_username_for_duplicate(self, username: str, payload_index: int) -> bool:
        result = (
            bool(self.users_in_double_lists[payload_index])
            or username in self.used_usernames
        )
        if username not in self.used_usernames:
            self.used_usernames.append(username)
        return result

    def check_saml_id_for_duplicate(self, saml_id: str, payload_index: int) -> bool:
        result = (
            bool(self.users_in_double_lists[payload_index])
            or saml_id in self.used_saml_ids
        )
        if saml_id not in self.used_saml_ids:
            self.used_saml_ids.append(saml_id)
        return result

    def check_name_and_email_for_duplicate(
        self, first_name: str, last_name: str, email: str, payload_index: int
    ) -> bool:
        entry = (first_name, last_name, email)
        result = (
            self.users_in_double_lists[payload_index]
            or entry in self.used_names_and_email
        )
        if entry not in self.used_names_and_email:
            self.used_names_and_email.append(entry)
        return result

    def get_search_data(self, payload_index: int) -> dict[str, Any] | None:
        if len(self.users_in_double_lists[payload_index]) == 1:
            return self.users_in_double_lists[payload_index][0]
        return None

    def has_multiple_search_data(self, payload_index: int) -> list[str]:
        if len(self.users_in_double_lists[payload_index]) >= 2:
            return [
                entry["username"] for entry in self.users_in_double_lists[payload_index]
            ]
        return []


def check_gender_helper(datastore: DatastoreService, instance: dict[str, Any]) -> None:
    if instance.get("gender"):
        organization = datastore.get(ONE_ORGANIZATION_FQID, ["genders"])
        if organization.get("genders"):
            if not instance["gender"] in organization["genders"]:
                raise ActionException(
                    f"Gender '{instance['gender']}' is not in the allowed gender list."
                )
