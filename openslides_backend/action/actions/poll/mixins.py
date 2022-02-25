from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permission, Permissions
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.exceptions import MissingPermission, VoteServiceException
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...action import Action
from ..option.set_auto_fields import OptionSetAutoFields
from ..projector_countdown.mixins import CountdownControl
from ..vote.create import VoteCreate
from ..vote.user_token_helper import get_user_token


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
            [
                "state",
                "meeting_id",
                "pollmethod",
                "global_option_id",
                "entitled_group_ids",
            ],
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

        # stop poll in vote service and create vote objects
        results = self.vote_service.stop(instance["id"])
        action_data = []
        votesvalid = Decimal("0.000000")
        option_results: Dict[int, Dict[str, Decimal]] = defaultdict(
            lambda: defaultdict(lambda: Decimal("0.000000"))
        )  # maps options to their respective YNA sums
        for ballot in results["votes"]:
            user_token = get_user_token()
            vote_weight = Decimal(ballot["weight"])
            votesvalid += vote_weight
            vote_template = {"user_token": user_token}
            if "vote_user_id" in ballot:
                vote_template["user_id"] = ballot["vote_user_id"]
            if "request_user_id" in ballot:
                vote_template["delegated_user_id"] = ballot["request_user_id"]

            if isinstance(ballot["value"], dict):
                for option_id_str, value in ballot["value"].items():
                    option_id = int(option_id_str)

                    vote_value = value
                    vote_weighted = vote_weight # use new variable vote_weighted because pollmethod=Y/N does not imply anymore that only one loop is done (see max_votes_per_person)
                    if poll["pollmethod"] in ("Y", "N"):
                        if value == 0:
                            continue
                        vote_value = poll["pollmethod"]
                        # print("Summing up")
                        # print(vote_value)
                        # print(value)
                        # print(vote_weight)
                        # print(ballot["weight"])
                        # vote_weight *= value
                        vote_weighted *= value

                    option_results[option_id][vote_value] += vote_weighted
                    action_data.append(
                        {
                            "value": vote_value,
                            "option_id": option_id,
                            "weight": str(vote_weighted),
                            **vote_template,
                        }
                    )
            elif isinstance(ballot["value"], str):
                vote_value = ballot["value"]
                option_id = poll["global_option_id"]
                option_results[option_id][vote_value] += vote_weight
                action_data.append(
                    {
                        "value": vote_value,
                        "option_id": option_id,
                        "weight": str(vote_weight),
                        **vote_template,
                    }
                )
            else:
                raise VoteServiceException("Invalid response from vote service")
        self.execute_other_action(VoteCreate, action_data)
        # update results into option
        self.execute_other_action(
            OptionSetAutoFields,
            [
                {
                    "id": _id,
                    "yes": str(option["Y"]),
                    "no": str(option["N"]),
                    "abstain": str(option["A"]),
                }
                for _id, option in option_results.items()
            ],
        )
        # set voted ids
        voted_ids = results["user_ids"]
        instance["voted_ids"] = voted_ids

        # set votescast, votesvalid, votesinvalid
        instance["votesvalid"] = str(votesvalid)
        instance["votescast"] = str(Decimal("0.000000") + Decimal(len(voted_ids)))
        instance["votesinvalid"] = "0.000000"

        # set entitled users at stop.
        instance["entitled_users_at_stop"] = self.get_entitled_users(
            {**poll, **instance}
        )

    def get_entitled_users(self, poll: Dict[str, Any]) -> List[Dict[str, Any]]:
        entitled_users = []
        entitled_users_ids = set()
        all_voted_users = set(poll.get("voted_ids", []))
        meeting_id = poll["meeting_id"]

        # get all users from the groups.
        gmr = GetManyRequest(
            Collection("group"), poll.get("entitled_group_ids", []), ["user_ids"]
        )
        gm_result = self.datastore.get_many([gmr])
        groups = gm_result.get(Collection("group"), {}).values()

        for group in groups:
            user_ids = group.get("user_ids", [])
            entitled_users_ids.update(user_ids)

        gmr = GetManyRequest(
            Collection("user"),
            list(entitled_users_ids),
            [
                "id",
                "is_present_in_meeting_ids",
                f"vote_delegated_${meeting_id}_to_id",
            ],
        )
        gm_result = self.datastore.get_many([gmr])
        users = gm_result.get(Collection("user"), {}).values()

        for user in users:
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
