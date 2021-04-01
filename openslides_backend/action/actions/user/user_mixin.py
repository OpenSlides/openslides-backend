from collections import defaultdict
from functools import reduce
from typing import Any, Dict, List

from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action
from ...util.assert_belongs_to_meeting import assert_belongs_to_meeting


class UserMixin(Action):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        user_fqid = FullQualifiedId(Collection("user"), instance["id"])
        if "username" in instance:
            exists = self.datastore.exists(
                Collection("user"),
                FilterOperator("username", "=", instance["username"]),
                lock_result=True,
            )
            if exists:
                raise ActionException(
                    f"A user with the username {instance['username']} already exists."
                )
        self.check_existence_of_to_and_from_users(instance)
        self.check_meeting_and_users(instance, user_fqid)
        if "vote_delegated_$_to_id" in instance:
            self.check_vote_delegated__to_id(instance, user_fqid)
        if "vote_delegations_$_from_ids" in instance:
            self.check_vote_delegations__from_ids(instance, user_fqid)
        return instance

    def check_vote_delegated__to_id(
        self, instance: Dict[str, Any], user_fqid: FullQualifiedId
    ) -> None:
        mapped_fields = [
            f"vote_delegations_${meeting_id}_from_ids"
            for meeting_id, delegated_to in instance["vote_delegated_$_to_id"].items()
            if delegated_to
        ]
        if not mapped_fields:
            return
        user_self = self.datastore.fetch_model(
            user_fqid, mapped_fields, lock_result=True, exception=False
        )
        if "vote_delegations_$_from_ids" in instance:
            update_dict = {
                f"vote_delegations_${meeting_id}_from_ids": delegated_from
                for meeting_id, delegated_from in instance[
                    "vote_delegations_$_from_ids"
                ].items()
            }
            user_self.update(update_dict)
        for meeting_id, delegated_to_id in instance["vote_delegated_$_to_id"].items():
            if user_fqid.id == delegated_to_id:
                raise ActionException(
                    f"User {delegated_to_id} can't delegate the vote to himself."
                )
            if user_self.get(f"vote_delegations_${meeting_id}_from_ids"):
                raise ActionException(
                    f"User {user_fqid.id} cannot delegate his vote, because there are votes delegated to him."
                )
            mapped_field = f"vote_delegated_${meeting_id}_to_id"
            user_delegated_to = self.datastore.fetch_model(
                FullQualifiedId(Collection("user"), delegated_to_id),
                [mapped_field],
                lock_result=True,
            )
            if user_delegated_to.get(mapped_field):
                raise ActionException(
                    f"User {user_fqid.id} cannot delegate his vote to user {delegated_to_id}, because that user has delegated his vote himself."
                )

    def check_vote_delegations__from_ids(
        self, instance: Dict[str, Any], user_fqid: FullQualifiedId
    ) -> None:
        mapped_fields = [
            f"vote_delegated_${meeting_id}_to_id"
            for meeting_id, delegated_from in instance[
                "vote_delegations_$_from_ids"
            ].items()
            if delegated_from
        ]
        if not mapped_fields:
            return
        user_self = self.datastore.fetch_model(
            user_fqid, mapped_fields, lock_result=True, exception=False
        )
        if "vote_delegated_$_to_id" in instance:
            update_dict = {
                f"vote_delegated_${meeting_id}_to_id": delegated_to
                for meeting_id, delegated_to in instance[
                    "vote_delegated_$_to_id"
                ].items()
            }
            user_self.update(update_dict)
        for meeting_id, delegated_from_ids in instance[
            "vote_delegations_$_from_ids"
        ].items():
            if user_fqid.id in delegated_from_ids:
                raise ActionException(
                    f"User {user_fqid.id} can't delegate the vote to himself."
                )
            if user_self.get(f"vote_delegated_${meeting_id}_to_id"):
                raise ActionException(
                    f"User {user_fqid.id} cannot receive vote delegations, because he delegated his own vote."
                )
            mapped_field = f"vote_delegations_${meeting_id}_from_ids"
            error_user_ids: List[int] = []
            for user_id in delegated_from_ids:
                user = self.datastore.fetch_model(
                    FullQualifiedId(Collection("user"), user_id),
                    [mapped_field],
                    lock_result=True,
                )
                if user.get(mapped_field):
                    error_user_ids.append(user_id)
            if error_user_ids:
                raise ActionException(
                    f"User(s) {error_user_ids} can't delegate their votes , because they receive vote delegations."
                )

    def check_existence_of_to_and_from_users(self, instance: Dict[str, Any]) -> None:
        user_ids = set(
            filter(bool, instance.get("vote_delegated_$_to_id", dict()).values())
        )
        if "vote_delegations_$_from_ids" in instance:
            user_ids = user_ids.union(
                set(
                    reduce(
                        (lambda x, y: x + y),  # type: ignore
                        instance["vote_delegations_$_from_ids"].values(),
                    )
                )
            )
        if user_ids:
            get_many_request = GetManyRequest(
                self.model.collection, list(user_ids), ["id"]
            )
            gm_result = self.datastore.get_many([get_many_request])
            users = gm_result.get(self.model.collection, {})

            set_action_data = user_ids
            diff = set_action_data.difference(users.keys())
            if len(diff):
                raise ActionException(f"The following users were not found: {diff}")

    def check_meeting_and_users(
        self, instance: Dict[str, Any], user_fqid: FullQualifiedId
    ) -> None:
        user_collection = Collection("user")
        meeting_users = defaultdict(list)
        if instance.get("group_$_ids") is not None:
            self.datastore.additional_relation_models[user_fqid].update(
                {
                    f"group_${meeting_id}_ids": ids
                    for meeting_id, ids in instance.get("group_$_ids").items()  # type: ignore
                }
            )
        for field_name in ("meeting_id", "guest_meeting_ids"):
            if instance.get(field_name) is not None:
                self.datastore.additional_relation_models[user_fqid].update(
                    {field_name: instance.get(field_name)}
                )
        for meeting_id, user_id in instance.get("vote_delegated_$_to_id", {}).items():
            if user_id:
                meeting_users[meeting_id].append(
                    FullQualifiedId(user_collection, user_id)
                )
        for meeting_id, user_ids in instance.get(
            "vote_delegations_$_from_ids", {}
        ).items():
            if user_ids:
                meeting_users[meeting_id].extend(
                    [FullQualifiedId(user_collection, user_id) for user_id in user_ids]
                )
        for meeting_id, users in meeting_users.items():
            users.append(user_fqid)
            assert_belongs_to_meeting(self.datastore, users, int(meeting_id))
