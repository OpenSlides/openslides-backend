from typing import List

from ....services.datastore.commands import GetManyRequest
from ....shared.patterns import Collection
from ...action import Action


class PermissionHelperMixin(Action):
    def is_user_submitter(self, submitter_ids: List[int]) -> bool:
        get_many_request = GetManyRequest(
            Collection("motion_submitter"), submitter_ids, ["user_id"]
        )
        result = self.datastore.get_many([get_many_request])
        submitters = result.get(Collection("motion_submitter"), {}).values()
        for submitter in submitters:
            if self.user_id == submitter.get("user_id"):
                return True
        return False
