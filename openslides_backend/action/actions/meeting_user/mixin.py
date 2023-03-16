from typing import Any, Dict, Tuple

from ....action.action import Action
from ....shared.exceptions import ActionException, PermissionDenied
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from ....shared.patterns import (
    FullQualifiedId,
    fqid_from_collection_and_id,
    id_from_fqid,
)


class MeetingUserMixin(Action):
    standard_fields = [
        "comment",
        "number",
        "structure_level",
        "vote_weight",
        "personal_note_ids",
        "speaker_ids",
        "supported_motion_ids",
        "submitted_motion_ids",
        "assignment_candidate_ids",
        "vote_delegated_vote_ids",
        "vote_delegated_to_id",
        "vote_delegations_from_ids",
        "chat_message_ids",
    ]

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        """ standard_fields have to be checked, but also it is not permitted, create an empty meeting_value instance"""
        if any(fname in self.standard_fields for fname in instance.keys()) or not any(fname in ["about_me", "group_ids"] for fname in instance):
            return super().check_permissions(instance)

        def get_user_and_meeting_id() -> Tuple[int]:
            fields = ["user_id", "meeting_id"]
            if any(fname not in instance for fname in fields):
                mu = self.datastore.get(
                    fqid_from_collection_and_id("meeting_user", instance["id"]),
                    ["user_id", "meeting_id"],
                    lock_result=False,
                )
                return (mu[fname] for fname in fields)
            return (instance[fname] for fname in fields)

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
                super().check_permissions(instance)
                return False
            except:
                return True

        user_id, meeting_id = get_user_and_meeting_id()
        if "about_me" in instance:
            if self.user_id != user_id:
                if raise_own_exception():
                    raise PermissionDenied(f"The user needs Permission user.can_manage in meeting {meeting_id} to set 'about me', if it is not his own")
                else:
                    return

        if "group_ids" in instance:
            user = get_request_user_data()
            if OrganizationManagementLevel(user.get("organization_management_level")) < OrganizationManagementLevel.CAN_MANAGE_USERS:
                committee_id = get_committee_id()
                if committee_id not in user.get("committee_management_ids", []) and raise_own_exception():
                    raise PermissionDenied(
                        f"The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_manage for meeting {meeting_id}"
                )


    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if "vote_delegated_to_id" in instance:
            self.check_vote_delegated_to_id(
                instance, fqid_from_collection_and_id("meeting_user", instance["id"])
            )
        if "vote_delegations_from_ids" in instance:
            self.check_vote_delegations_from_ids(
                instance, fqid_from_collection_and_id("meeting_user", instance["id"])
            )
        return instance

    def check_vote_delegated_to_id(
        self, instance: Dict[str, Any], meeting_user_fqid: FullQualifiedId
    ) -> None:
        from_ids = "vote_delegations_from_ids"
        to_id = "vote_delegated_to_id"

        if not instance.get(to_id):
            return
        user_self = self.datastore.get(
            meeting_user_fqid, [from_ids], raise_exception=False
        )
        if from_ids in instance:
            update_dict = {from_ids: instance[from_ids]}
            user_self.update(update_dict)

        if id_from_fqid(meeting_user_fqid) == instance.get(to_id):
            raise ActionException(
                f"MeetingUser {instance.get(to_id)} can't delegate the vote to himself."
            )
        if user_self.get(from_ids):
            raise ActionException(
                f"MeetingUser {id_from_fqid(meeting_user_fqid)} cannot delegate his vote, because there are votes delegated to him."
            )
        delegated_to_id = instance[to_id]
        user_delegated_to = self.datastore.get(
            fqid_from_collection_and_id("meeting_user", delegated_to_id),
            [to_id],
        )
        if user_delegated_to.get(to_id):
            raise ActionException(
                f"MeetingUser {id_from_fqid(meeting_user_fqid)} cannot delegate his vote to user {delegated_to_id}, because that user has delegated his vote himself."
            )

    def check_vote_delegations_from_ids(
        self, instance: Dict[str, Any], meeting_user_fqid: FullQualifiedId
    ) -> None:
        to_id = "vote_delegated_to_id"  # mapped_fields
        from_ids = "vote_delegations_from_ids"
        if not instance.get(from_ids):
            return
        meeting_user_self = self.datastore.get(
            meeting_user_fqid, [to_id], raise_exception=False
        )
        if to_id in instance:
            delegated_to = instance[to_id]
            update_dict = {"vote_delegated_to_id": delegated_to}
            meeting_user_self.update(update_dict)

        delegated_from_ids = instance[from_ids]
        if id_from_fqid(meeting_user_fqid) in delegated_from_ids:
            raise ActionException(
                f"MeetingUser {id_from_fqid(meeting_user_fqid)} can't delegate the vote to himself."
            )
        if meeting_user_self.get("vote_delegated_to_id"):
            raise ActionException(
                f"MeetingUser {id_from_fqid(meeting_user_fqid)} cannot receive vote delegations, because he delegated his own vote."
            )
        mapped_field = "vote_delegations_from_ids"
        error_meeting_user_ids: List[int] = []
        for meeting_user_id in delegated_from_ids:
            meeting_user = self.datastore.get(
                fqid_from_collection_and_id("meeting_user", meeting_user_id),
                [mapped_field],
            )
            if meeting_user.get(mapped_field):
                error_meeting_user_ids.append(meeting_user_id)
        if error_meeting_user_ids:
            raise ActionException(
                f"MeetingUser(s) {error_meeting_user_ids} can't delegate their votes because they receive vote delegations."
            )
