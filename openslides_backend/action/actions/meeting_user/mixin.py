from typing import Any, cast

from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from .history_mixin import MeetingUserHistoryMixin

meeting_user_standard_fields = [
    "comment",
    "number",
    "vote_weight",
    "structure_level_ids",
]


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
