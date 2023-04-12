from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple, cast

from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.typing import HistoryInformation

from ....action.action import Action
from ....shared.exceptions import ActionException, MissingPermission, PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id


class MeetingUserHistoryMixin(Action):
    def get_history_information(self) -> Optional[HistoryInformation]:
        information = {}

        # Scan the instances and collect the info for the history information
        # Copy instances first since they are modified
        for instance in deepcopy(self.instances):
            instance_information = []

            # Fetch the current instance from the db to diff with the given instance
            db_instance = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                list(instance.keys()) + ["user_id", "meeting_id"],
                use_changed_models=False,
                raise_exception=False,
            )
            if not db_instance:
                continue
            user_id = db_instance["user_id"]
            meeting_id = db_instance["meeting_id"]

            # Compare db version with payload
            for field in list(instance.keys()):
                # Remove fields if equal
                if instance[field] == db_instance.get(field):
                    del instance[field]

            # meeting specific data
            update_fields = ["structure_level", "number", "vote_weight"]
            if any(field in instance for field in update_fields):
                instance_information.extend(
                    [
                        "Participant data updated in meeting {}",
                        fqid_from_collection_and_id("meeting", meeting_id),
                    ]
                )

            # groups
            if "group_ids" in instance:
                instance_group_ids = set(instance["group_ids"])
                db_group_ids = set(db_instance.get("group_ids", []))
                added = instance_group_ids - db_group_ids
                removed = db_group_ids - instance_group_ids

                # remove default groups
                meeting = self.datastore.get(
                    fqid_from_collection_and_id("meeting", meeting_id),
                    ["default_group_id"],
                )
                added.discard(meeting.get("default_group_id"))
                removed.discard(meeting.get("default_group_id"))
                changed = added | removed

                group_information: List[str] = []
                if added and removed:
                    group_information.append("Groups changed")
                else:
                    if added:
                        group_information.append("Participant added to")
                    else:
                        group_information.append("Participant removed from")
                    if len(changed) == 1:
                        group_information[0] += " group {} in"
                        changed_group = changed.pop()
                        group_information.append(
                            fqid_from_collection_and_id("group", changed_group)
                        )
                    elif instance_group_ids:
                        group_information[0] += " multiple groups in"
                    group_information[0] += " meeting {}"
                    group_information.append(
                        fqid_from_collection_and_id("meeting", meeting_id)
                    )
                instance_information.extend(group_information)

            if instance_information:
                information[
                    fqid_from_collection_and_id("user", user_id)
                ] = instance_information
        return information


class MeetingUserMixin(MeetingUserHistoryMixin):
    standard_fields = [
        "comment",
        "number",
        "structure_level",
        "vote_weight",
        "personal_note_ids",
        "speaker_ids",
        "supported_motion_ids",
        "motion_submitter_ids",
        "assignment_candidate_ids",
        "vote_delegated_to_id",
        "vote_delegations_from_ids",
        "chat_message_ids",
    ]

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        """standard_fields have to be checked for user.can_manage, which is always sufficient and
        even needed, if there is no data at all exempt the required fields.
        Special fields like about_me and group_ids could be managed also with other permissions.
        Details see https://github.com/OpenSlides/OpenSlides/wiki/meeting_user.create"""
        if any(fname in self.standard_fields for fname in instance.keys()) or not any(
            fname in ["about_me", "group_ids"] for fname in instance
        ):
            return super().check_permissions(instance)

        def get_user_and_meeting_id() -> Tuple[int, int]:
            fields = ["user_id", "meeting_id"]
            if any(fname not in instance for fname in fields):
                mu = self.datastore.get(
                    fqid_from_collection_and_id("meeting_user", instance["id"]),
                    ["user_id", "meeting_id"],
                    lock_result=False,
                )
                return cast(Tuple[int, int], ([mu[fname] for fname in fields]))
            return cast(Tuple[int, int], (instance[fname] for fname in fields))

        def get_request_user_data() -> Dict[str, Any]:
            return self.datastore.get(
                fqid_from_collection_and_id("user", self.user_id),
                ["organization_management_level", "committee_management_ids"],
                lock_result=False,
            )

        def get_committee_id() -> int:
            return self.datastore.get(
                fqid_from_collection_and_id("meeting", meeting_id),
                ["committee_id"],
                lock_result=False,
            )["committee_id"]

        def raise_own_exception() -> bool:
            try:
                super(MeetingUserMixin, self).check_permissions(instance)
                return False
            except PermissionDenied:
                return True

        user_id, meeting_id = get_user_and_meeting_id()
        if "about_me" in instance:
            if self.user_id != user_id:
                if raise_own_exception():
                    raise PermissionDenied(
                        f"The user needs Permission user.can_manage in meeting {meeting_id} to set 'about me', if it is not his own"
                    )
                else:
                    return

        if "group_ids" in instance:
            user = get_request_user_data()
            if (
                OrganizationManagementLevel(user.get("organization_management_level"))
                < OrganizationManagementLevel.CAN_MANAGE_USERS
            ):
                committee_id = get_committee_id()
                if (
                    committee_id not in user.get("committee_management_ids", [])
                    and raise_own_exception()
                ):
                    raise MissingPermission(
                        {
                            OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                            CommitteeManagementLevel.CAN_MANAGE: committee_id,
                            Permissions.User.CAN_MANAGE: meeting_id,
                        }
                    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
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
        instance: Dict[str, Any],
        meeting_user_self: Dict[str, Any],
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
            if meeting_user_delegated_to.get("vote_delegated_to_id"):
                raise ActionException(
                    f"User {user_id_self} cannot delegate his vote to user {meeting_user_delegated_to['user_id']}, because that user has delegated his vote himself."
                )

    def check_vote_delegations_from_ids(
        self,
        instance: Dict[str, Any],
        meeting_user_self: Dict[str, Any],
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
        vote_error_user_ids: List[int] = []
        meeting_error_user_ids: List[int] = []
        for meeting_user_id in delegated_from_ids:
            meeting_user = self.datastore.get(
                fqid_from_collection_and_id("meeting_user", meeting_user_id),
                ["vote_delegations_from_ids", "user_id", "meeting_id"],
            )
            if meeting_user.get("meeting_id") != meeting_id_self:
                meeting_error_user_ids.append(cast(int, meeting_user.get("user_id")))
            if meeting_user.get("vote_delegations_from_ids"):
                vote_error_user_ids.append(cast(int, meeting_user.get("user_id")))
        if meeting_error_user_ids:
            raise ActionException(
                f"User(s) {meeting_error_user_ids} delegation ids don't belong to meeting {meeting_id_self}."
            )
        elif vote_error_user_ids:
            raise ActionException(
                f"User(s) {vote_error_user_ids} can't delegate their votes because they receive vote delegations."
            )
