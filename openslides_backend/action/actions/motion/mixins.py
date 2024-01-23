import re
from hashlib import md5
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from openslides_backend.shared.filters import And, FilterOperator

from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
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
        return self.is_submitter(submitter_ids)

    def is_submitter(self, submitter_ids: List[int]) -> bool:
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
    def validate_amendment_paragraphs(self, instance: Dict[str, Any]) -> None:
        for key, html in instance["amendment_paragraphs"].items():
            instance["amendment_paragraphs"][key] = validate_html(
                html, ALLOWED_HTML_TAGS_STRICT
            )


def set_workflow_timestamp_helper(
    datastore: DatastoreService, instance: Dict[str, Any], timestamp: int
) -> None:
    state = datastore.get(
        fqid_from_collection_and_id("motion_state", instance["state_id"]),
        ["set_workflow_timestamp"],
    )
    if state.get("set_workflow_timestamp"):
        instance["workflow_timestamp"] = timestamp


class TextHashMixin(Action):
    def set_text_hash(self, instance: Dict[str, Any]) -> None:
        if html := instance.get("text"):
            text = self.get_text_from_html(html)
            hash = md5(text.encode()).hexdigest()
            instance["text_hash"] = hash

            # find identical motions
            filter = [
                FilterOperator("text_hash", "=", hash),
                FilterOperator("meeting_id", "=", instance["meeting_id"]),
            ]
            result = self.datastore.filter(
                self.model.collection,
                And(*filter),
                ["id"],
            )
            instance["identical_motion_ids"] = [
                id for id in result.keys() if id != instance.get("id")
            ]

    def get_text_from_html(self, html: str) -> str:
        soup = BeautifulSoup(html, features="html.parser")
        text = soup.get_text()
        # remove all non-word characters
        text = re.sub(r"\W|-?\n", "", text)
        return text
