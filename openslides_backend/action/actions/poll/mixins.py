from decimal import Decimal
from typing import Any, Dict, List

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permission, Permissions
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.exceptions import MissingPermission
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...action import Action
from ..projector_countdown.mixins import CountdownControl


class PollPermissionMixin(Action):
    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if "meeting_id" in instance:
            content_object_id = instance.get("content_object_id", "")
            meeting_id = instance["meeting_id"]
        else:
            poll = self.datastore.get(
                FullQualifiedId(Collection("poll"), instance["id"]),
                ["content_object_id", "meeting_id"],
            )
            content_object_id = poll.get("content_object_id", "")
            meeting_id = poll["meeting_id"]
        check_poll_or_option_perms(
            self.name, content_object_id, self.datastore, self.user_id, meeting_id
        )


def check_poll_or_option_perms(
    action_name: str,
    content_object_id: str,
    datastore: DatastoreService,
    user_id: int,
    meeting_id: int,
) -> None:

    if content_object_id.startswith("motion" + KEYSEPARATOR):
        perm: Permission = Permissions.Motion.CAN_MANAGE_POLLS
    elif content_object_id.startswith("assignment" + KEYSEPARATOR):
        perm = Permissions.Assignment.CAN_MANAGE
    else:
        perm = Permissions.Poll.CAN_MANAGE
    if not has_perm(datastore, user_id, perm, meeting_id):
        raise MissingPermission(perm)


class StopControl(CountdownControl, Action):
    def on_stop(self, instance: Dict[str, Any]) -> None:
        poll = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["state", "meeting_id", "voted_ids"],
        )
        # reset countdown given by meeting
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), poll["meeting_id"]),
            [
                "poll_couple_countdown",
                "poll_countdown_id",
                "users_enable_vote_weight",
            ],
        )
        if meeting.get("poll_couple_countdown") and meeting.get("poll_countdown_id"):
            self.control_countdown(meeting["poll_countdown_id"], "reset")

        # calculate votescast, votesvalid, votesinvalid
        voted_ids = poll.get("voted_ids", [])
        instance["votescast"] = str(Decimal("0.000000") + Decimal(len(voted_ids)))
        if not meeting.get("users_enable_vote_weight") or not voted_ids:
            instance["votesvalid"] = instance["votescast"]
        else:
            gmr = GetManyRequest(
                Collection("user"), voted_ids, [f"vote_weight_${poll['meeting_id']}"]
            )
            gm_result = self.datastore.get_many([gmr])
            users = gm_result.get(Collection("user"), {}).values()
            instance["votesvalid"] = str(
                sum(
                    Decimal(entry.get(f"vote_weight_${poll['meeting_id']}", "1.000000"))
                    for entry in users
                )
            )
        instance["votesinvalid"] = "0.000000"

        # set entitled users at stop.
        instance["entitled_users_at_stop"] = self.get_entitled_users(poll)

    def get_entitled_users(self, poll: Dict[str, Any]) -> List[Dict[str, Any]]:
        entitled_users = []
        entitled_users_ids = set()
        all_voted_users = poll.get("voted_ids", [])
        meeting_id = poll["meeting_id"]

        # get all users from the groups.
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id), ["group_ids"]
        )
        gmr = GetManyRequest(
            Collection("group"), meeting.get("group_ids", []), ["user_ids"]
        )
        gm_result = self.datastore.get_many([gmr])
        groups = gm_result.get(Collection("group"), {}).values()

        for group in groups:
            user_ids = group.get("user_ids", [])
            if not user_ids:
                continue
            gmr = GetManyRequest(
                Collection("user"),
                list(user_ids),
                [
                    "id",
                    "is_present_in_meeting_ids",
                    f"vote_delegated_${meeting_id}_to_id",
                ],
            )
            gm_result = self.datastore.get_many([gmr])
            users = gm_result.get(Collection("user"), {}).values()
            for user in users:
                vote_delegated = {}
                if user.get(f"vote_delegated_${meeting_id}_to_id"):
                    vote_delegated = self.datastore.get(
                        FullQualifiedId(
                            Collection("user"),
                            user[f"vote_delegated_${meeting_id}_to_id"],
                        ),
                        ["is_present_in_meeting_ids"],
                    )

                if user["id"] in entitled_users_ids:
                    continue
                elif poll["meeting_id"] in user.get(
                    "is_present_in_meeting_ids", []
                ) or (
                    user.get(f"vote_delegated_${meeting_id}_to_id")
                    and poll["meeting_id"]
                    in vote_delegated.get("is_present_in_meeting_ids", [])
                ):
                    entitled_users_ids.add(user["id"])
                    entitled_users.append(
                        {
                            "user_id": user["id"],
                            "voted": user["id"] in all_voted_users,
                            "vote_delegated_to_id": user.get(
                                f"vote_delegated_${meeting_id}_to_id"
                            ),
                        }
                    )

        return entitled_users
