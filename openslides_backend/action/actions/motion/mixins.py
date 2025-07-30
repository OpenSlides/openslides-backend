from datetime import datetime
from hashlib import md5
from typing import Any

import simplejson as json

from ....services.database.commands import GetManyRequest
from ....services.database.interface import Database
from ....shared.filters import And, FilterOperator
from ....shared.html import get_text_from_html
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.util import ALLOWED_HTML_TAGS_STRICT, validate_html
from ...action import Action


class PermissionHelperMixin(Action):
    def is_allowed_and_submitter(self, submitter_ids: list[int], state_id: int) -> bool:
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

    def is_submitter(self, submitter_ids: list[int]) -> bool:
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
    def validate_amendment_paragraphs(self, instance: dict[str, Any]) -> None:
        for key, html in instance["amendment_paragraphs"].items():
            instance["amendment_paragraphs"][key] = validate_html(
                html, ALLOWED_HTML_TAGS_STRICT
            )


def set_workflow_timestamp_helper(
    datastore: Database, instance: dict[str, Any], timestamp: datetime
) -> None:
    state = datastore.get(
        fqid_from_collection_and_id("motion_state", instance["state_id"]),
        ["set_workflow_timestamp"],
    )
    if state.get("set_workflow_timestamp"):
        instance["workflow_timestamp"] = timestamp


class TextHashMixin(Action):
    def set_text_hash(self, instance: dict[str, Any]) -> None:
        if hash := self.get_hash_for_motion(instance):
            instance["text_hash"] = hash

            # find identical motions
            lead_motion_id = self.get_field_from_instance("lead_motion_id", instance)
            filter = [
                FilterOperator("text_hash", "=", hash),
                FilterOperator("meeting_id", "=", self.get_meeting_id(instance)),
                FilterOperator("lead_motion_id", "=", lead_motion_id),
            ]
            result = self.datastore.filter(
                self.model.collection,
                And(*filter),
                ["id"],
            )
            instance["identical_motion_ids"] = [
                id for id in result.keys() if id != instance.get("id")
            ]

    @staticmethod
    def get_hash_for_motion(motion: dict[str, Any]) -> str | None:
        if html := motion.get("text"):
            text = get_text_from_html(html)
        elif paragraphs := motion.get("amendment_paragraphs"):
            paragraph_texts = {
                key: get_text_from_html(html) for key, html in paragraphs.items()
            }
            text = json.dumps(paragraph_texts, sort_keys=True)
        else:
            return None
        return TextHashMixin.get_hash(text)

    @staticmethod
    def get_hash(text: str) -> str:
        return md5(text.encode()).hexdigest()
