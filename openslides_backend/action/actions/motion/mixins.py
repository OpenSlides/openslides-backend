from typing import Any, Dict, List

from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.util import ALLOWED_HTML_TAGS_STRICT, validate_html
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
        return self.is_submitter(submitter_ids, state_id)

    def is_submitter(self, submitter_ids: List[int], state_id: int) -> bool:
        user = self.datastore.get(
            fqid_from_collection_and_id("user", self.user_id), ["meeting_user_ids"]
        )
        get_many_request = GetManyRequest(
            "motion_submitter", submitter_ids, ["meeting_user_id"]
        )
        result = self.datastore.get_many([get_many_request])
        submitters = result.get("motion_submitter", {}).values()
        return any(
            s.get("meeting_user_id") in (user.get("meeting_user_ids") or [])
            for s in submitters
        )


class AmendmentParagraphHelper:
    def validate_amendment_paragraph(self, instance: Dict[str, Any]) -> None:
        if not isinstance(instance["amendment_paragraph"], dict):
            raise ActionException("Wrong amendment_paragraph except dict")
        for key, html in instance["amendment_paragraph"].items():
            if not str.isdigit(key):
                raise ActionException(f"amendment_paragraph {key} not allowed.")
            instance["amendment_paragraph"][key] = validate_html(
                html, ALLOWED_HTML_TAGS_STRICT
            )
