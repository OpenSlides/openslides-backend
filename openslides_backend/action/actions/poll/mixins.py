from collections import defaultdict
from decimal import Decimal
from typing import Any

import simplejson as json

from openslides_backend.models.models import Poll
from openslides_backend.shared.typing import HistoryInformation

from ....action.util.typing import ActionResultElement
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permission, Permissions
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.exceptions import MissingPermission, VoteServiceException
from ....shared.patterns import (
    KEYSEPARATOR,
    collection_from_fqid,
    fqid_from_collection_and_id,
)
from ...action import Action
from ..option.set_auto_fields import OptionSetAutoFields
from ..projector_countdown.mixins import CountdownCommand, CountdownControl
from ..vote.create import VoteCreate
from ..vote.user_token_helper import get_user_token


class PollPermissionMixin(Action):
    def check_permissions(self, instance: dict[str, Any]) -> None:
        if "meeting_id" in instance:
            content_object_id = instance.get("content_object_id", "")
            meeting_id = instance["meeting_id"]
        else:
            poll = self.datastore.get(
                fqid_from_collection_and_id("poll", instance["id"]),
                ["content_object_id", "meeting_id"],
                lock_result=False,
            )
            content_object_id = poll.get("content_object_id", "")
            meeting_id = poll["meeting_id"]
        check_poll_or_option_perms(
            content_object_id, self.datastore, self.user_id, meeting_id
        )


def check_poll_or_option_perms(
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
    invalid_votes: list[dict[str, str]] = []

    def on_stop(self, instance: dict[str, Any]) -> None:
        poll = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            [
                "type",
                "state",
                "meeting_id",
                "pollmethod",
                "global_option_id",
                "entitled_group_ids",
            ],
        )
        # reset countdown given by meeting
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", poll["meeting_id"]),
            [
                "poll_couple_countdown",
                "poll_countdown_id",
                "users_enable_vote_weight",
            ],
        )
        if meeting.get("poll_couple_countdown") and meeting.get("poll_countdown_id"):
            self.control_countdown(meeting["poll_countdown_id"], CountdownCommand.RESET)

        # stop poll in vote service and create vote objects
        results = self.vote_service.stop(instance["id"])
        votes_raw = results["votes"]
        invalid = results.get("invalid", {})
        votes = json.loads(votes_raw)
        if poll["type"] == Poll.TYPE_CRYPTOGRAPHIC:
            votes = votes["votes"]
            instance["votes_raw"] = votes_raw
            instance["votes_signature"] = results.get("signature")
        action_data = []
        votesvalid = Decimal("0.000000")
        self.invalid_votes: list[dict[str, str]] = []
        option_results: dict[int, dict[str, Decimal]] = defaultdict(
            lambda: defaultdict(lambda: Decimal("0.000000"))
        )  # maps options to their respective YNA sums
        for i, ballot in enumerate(votes):
            if msg := invalid.get(str(i)):
                self.invalid_votes.append(
                    {
                        "msg": msg,
                        "ballot": json.dumps(ballot),
                    }
                )
                continue

            if poll["type"] == Poll.TYPE_CRYPTOGRAPHIC:
                user_token = ballot.get("token")
            else:
                user_token = get_user_token()
            vote_weight = Decimal(ballot.get("weight", "1.000000")) or Decimal(
                "1.000000"
            )
            votesvalid += vote_weight
            vote_template: dict[str, str | int] = {"user_token": user_token}
            if "vote_user_id" in ballot:
                vote_template["user_id"] = ballot["vote_user_id"]
            if "request_user_id" in ballot:
                vote_template["delegated_user_id"] = ballot["request_user_id"]

            if isinstance(ballot.get("value"), dict):
                for option_id_str, value in ballot["value"].items():
                    option_id = int(option_id_str)

                    vote_value = value
                    vote_weighted = vote_weight  # use new variable vote_weighted because pollmethod=Y/N does not imply anymore that only one loop is done (see max_votes_per_option)
                    if poll["pollmethod"] in ("Y", "N"):
                        if value == 0:
                            continue
                        vote_value = poll["pollmethod"]
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
            elif isinstance(ballot.get("value"), str):
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
            elif poll["type"] == Poll.TYPE_CRYPTOGRAPHIC:
                for option_id_str, value in ballot["votes"].items():
                    option_id = int(option_id_str)

                    vote_value = value
                    vote_weighted = vote_weight  # use new variable vote_weighted because pollmethod=Y/N does not imply anymore that only one loop is done (see max_votes_per_option)
                    if poll["pollmethod"] in ("Y", "N"):
                        if value == 0:
                            continue
                        vote_value = poll["pollmethod"]
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
        instance["votesinvalid"] = str(
            Decimal("0.000000") + Decimal(len(self.invalid_votes))
        )

        # set entitled users at stop.
        instance["entitled_users_at_stop"] = self.get_entitled_users(poll | instance)

    def get_entitled_users(self, poll: dict[str, Any]) -> list[dict[str, Any]]:
        entitled_users = []
        all_voted_users = set(poll.get("voted_ids", []))

        # get all users from the groups.
        gmr = GetManyRequest(
            "group", poll.get("entitled_group_ids", []), ["meeting_user_ids"]
        )
        gm_result = self.datastore.get_many([gmr])
        groups = gm_result.get("group", {}).values()

        # fetch presence status
        meeting_user_ids = set()
        for group in groups:
            meeting_user_ids.update(group.get("meeting_user_ids", []))
        gmr = GetManyRequest(
            "meeting_user", list(meeting_user_ids), ["user_id", "vote_delegated_to_id"]
        )
        gm_result = self.datastore.get_many([gmr])
        meeting_users = gm_result.get("meeting_user", {}).values()

        # fetch vote delegations
        delegated_to_mu_ids = list(
            {id_ for mu in meeting_users if (id_ := mu.get("vote_delegated_to_id"))}
        )
        mu_to_user_id = {}
        if delegated_to_mu_ids:
            gmr = GetManyRequest("meeting_user", delegated_to_mu_ids, ["user_id"])
            mu_to_user_id = self.datastore.get_many([gmr]).get("meeting_user", {})

        gmr = GetManyRequest(
            "user",
            [mu["user_id"] for mu in meeting_users],
            ["is_present_in_meeting_ids"],
        )
        users = self.datastore.get_many([gmr]).get("user", {})

        for mu in meeting_users:
            entitled_users.append(
                {
                    "voted": mu["user_id"] in all_voted_users,
                    "present": poll["meeting_id"]
                    in users[mu["user_id"]].get("is_present_in_meeting_ids", []),
                    "user_id": mu["user_id"],
                    "vote_delegated_to_user_id": (
                        mu_to_user_id[vote_mu_id]["user_id"]
                        if (vote_mu_id := mu.get("vote_delegated_to_id"))
                        else None
                    ),
                }
            )

        return entitled_users

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        return {"invalid_votes": self.invalid_votes}


class PollHistoryMixin(Action):
    poll_history_information: str

    def get_history_information(self) -> HistoryInformation | None:
        # no datastore access necessary if information is in payload
        polls = self.get_instances_with_fields(["content_object_id"])
        return {
            poll["content_object_id"]: [
                f"{self.get_history_title(poll)} {self.poll_history_information}"
            ]
            for poll in polls
        }

    def get_history_title(self, poll: dict[str, Any]) -> str:
        content_collection = collection_from_fqid(poll["content_object_id"])
        if content_collection == "assignment":
            return "Ballot"
        return "Voting"
