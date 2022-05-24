from typing import List

from ....services.datastore.commands import GetManyRequest
from ....shared.patterns import to_fqid
from ...action import Action


class PermissionHelperMixin(Action):
    def is_allowed_and_submitter(self, submitter_ids: List[int], state_id: int) -> bool:
        if not submitter_ids:
            return False
        state = self.datastore.get(
            to_fqid("motion_state", state_id),
            ["allow_submitter_edit"],
        )
        if not state.get("allow_submitter_edit"):
            return False
        get_many_request = GetManyRequest(
            "motion_submitter", submitter_ids, ["user_id"]
        )
        result = self.datastore.get_many([get_many_request])
        submitters = result.get("motion_submitter", {}).values()
        return any(self.user_id == s.get("user_id") for s in submitters)
