from typing import Any, Dict

from openslides_backend.shared.patterns import (
    EXTENSION_REFERENCE_IDS_PATTERN,
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
)

from .set_number_mixin import SetNumberMixin


class MotionCheckCreateUpdatePayloadMixin(SetNumberMixin):
    """
    TODO: Add description
    """

    def get_payload_integrity_error_message(
        self, instance: Dict[str, Any], is_update: bool = False
    ) -> str | None:
        meeting_id = instance["meeting_id"] if not is_update else 0
        if is_update:
            if (
                instance.get("text")
                or instance.get("amendment_paragraphs")
                or instance.get("reason") == ""
                or instance.get("number")
            ):
                motion = self.datastore.get(
                    fqid_from_collection_and_id(self.model.collection, instance["id"]),
                    ["text", "amendment_paragraphs", "meeting_id"],
                )
                meeting_id = motion["meeting_id"]

            if instance.get("text"):
                if not motion.get("text"):
                    return (
                        "Cannot update text, because it was not set in the old values."
                    )
            if instance.get("amendment_paragraphs"):
                if not motion.get("amendment_paragraphs"):
                    return "Cannot update amendment_paragraphs, because it was not set in the old values."
        else:
            if instance.get("lead_motion_id"):
                if instance.get("statute_paragraph_id"):
                    return "You can't give both of lead_motion_id and statute_paragraph_id."
                if not instance.get("text") and not instance.get(
                    "amendment_paragraphs"
                ):
                    return "Text or amendment_paragraphs is required in this context."
                if instance.get("text") and instance.get("amendment_paragraphs"):
                    return "You can't give both of text and amendment_paragraphs"
            else:
                if not instance.get("text"):
                    return "Text is required"
                if instance.get("amendment_paragraphs"):
                    return "You can't give amendment_paragraphs in this context"
        if instance.get("reason") == "" if is_update else not instance.get("reason"):
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", meeting_id),
                ["motions_reason_required"],
            )
            if meeting.get("motions_reason_required"):
                return (
                    "Reason is required to update."
                    if is_update
                    else "Reason is required"
                )
        if instance.get("number"):
            if not self._check_if_unique(
                instance["number"], meeting_id, instance["id"]
            ):
                return "Number is not unique."
        for prefix in ("recommendation", "state"):
            if f"{prefix}_extension" in instance:
                possible_rerids = EXTENSION_REFERENCE_IDS_PATTERN.findall(
                    instance[f"{prefix}_extension"]
                )
                for fqid in possible_rerids:
                    collection, id_ = collection_and_id_from_fqid(fqid)
                    if collection != "motion":
                        return f"Found {fqid} but only motion is allowed."
        return None
