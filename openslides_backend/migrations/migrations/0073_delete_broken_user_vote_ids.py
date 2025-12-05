from collections import defaultdict

from datastore.migrations import BaseModelMigration
from datastore.reader.core.requests import GetManyRequestPart
from datastore.writer.core.write_request import BaseRequestEvent, RequestUpdateEvent

from ...shared.filters import And, FilterOperator


class Migration(BaseModelMigration):
    """
    This migration removes non existent relations from user to vote
    which were created due to pseudoanonymization.
    """

    target_migration_index = 74

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        potentially_broken_users = self.reader.filter(
            "user",
            And(
                FilterOperator("vote_ids", "!=", None),
                FilterOperator("vote_ids", "!=", []),
                FilterOperator("meta_deleted", "!=", True),
            ),
            ["vote_ids"],
        )
        potentially_broken_votes = self.reader.get_many(
            [
                GetManyRequestPart(
                    "vote",
                    list(
                        {
                            id_
                            for user in potentially_broken_users.values()
                            for id_ in user["vote_ids"]
                        }
                    ),
                    ["user_id"],
                )
            ]
        ).get("vote", {})
        to_delete_vote_ids_per_user = defaultdict(set)
        for user_id, user in potentially_broken_users.items():
            for vote_id in user["vote_ids"]:
                if not (
                    vote_id in potentially_broken_votes
                    and user_id == potentially_broken_votes[vote_id].get("user_id")
                ):
                    to_delete_vote_ids_per_user[user_id].add(vote_id)
        return [
            RequestUpdateEvent(
                f"user/{id_}", {}, list_fields={"remove": {"vote_ids": list(vote_ids)}}
            )
            for id_, vote_ids in to_delete_vote_ids_per_user.items()
        ]
