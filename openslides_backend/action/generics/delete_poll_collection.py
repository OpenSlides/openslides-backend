from typing import Any

from ...shared.patterns import fqid_from_collection_and_id
from .delete import DeleteAction


class PollCollectionDeleteAction(DeleteAction):
    """
    Generic delete action for collections related to Poll.
    """

    def get_meeting_id(self, instance: dict[str, Any]) -> int:
        """Retrieves meeting_id from the related poll."""

        poll_id = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["poll_id"],
        )["poll_id"]
        return self.datastore.get(
            fqid_from_collection_and_id("poll", poll_id),
            ["meeting_id"],
        )["meeting_id"]
