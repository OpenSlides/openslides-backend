from typing import Any, Dict, List

from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action


class PermissionHelperMixin(Action):
    def is_allowed_and_submitter(self, submitter_ids: List[int], state_id: int) -> bool:
        if not submitter_ids:
            return False
        state = self.datastore.get(
            fqid_from_collection_and_id("motion_state", state_id),
            ["allow_submitter_edit"],
            lock_result=False,
        )
        if not state.get("allow_submitter_edit"):
            return False
        return self.is_submitter(submitter_ids)

    def is_submitter(self, submitter_ids: List[int]) -> bool:
        get_many_request = GetManyRequest(
            "motion_submitter", submitter_ids, ["user_id"]
        )
        result = self.datastore.get_many([get_many_request])
        submitters = result.get("motion_submitter", {}).values()
        return any(self.user_id == s.get("user_id") for s in submitters)


def set_workflow_timestamp_helper(
    datastore: DatastoreService, instance: Dict[str, Any], timestamp: int
) -> None:
    state = datastore.get(
        fqid_from_collection_and_id("motion_state", instance["state_id"]),
        ["set_workflow_timestamp"],
    )
    if state.get("set_workflow_timestamp"):
        instance["workflow_timestamp"] = timestamp
