from enum import Enum
from typing import Any, TypedDict

from openslides_backend.shared.patterns import (
    EXTENSION_REFERENCE_IDS_PATTERN,
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
)

from .set_number_mixin import SetNumberMixin


class MotionErrorType(str, Enum):
    ADDITIONAL_SUBMITTER = "addtional_submitter"
    UNIQUE_NUMBER = "number_unique"
    RECO_EXTENSION = "recommendation_extension"
    STATE_EXTENSION = "state_extension"
    MOTION_TYPE = "motion_type"
    TEXT = "text"
    AMENDMENT_PARAGRAPHS = "amendment_paragraphs"
    REASON = "reason"
    WORKFLOW = "workflow"
    TITLE = "title"
    DIFF_VERSION = "diff_version"


class MotionActionErrorData(TypedDict):
    type: MotionErrorType
    message: str


class MotionBasePayloadValidationMixin(SetNumberMixin):
    """
    Contains functions necessary for the validation of both motion.create and motion.update actions
    """

    def conduct_common_checks(
        self,
        instance: dict[str, Any],
        meeting_id: int,
        previous_numbers: list[str] = [],
    ) -> list[MotionActionErrorData]:
        errors: list[MotionActionErrorData] = []
        if instance.get("number"):
            if not self._check_if_unique(
                instance["number"], meeting_id, instance.get("id"), previous_numbers
            ):
                errors.append(
                    {
                        "type": MotionErrorType.UNIQUE_NUMBER,
                        "message": "Number is not unique.",
                    }
                )
        recommendation_check = self._check_recommendation_and_state(instance)
        if recommendation_check:
            errors += recommendation_check
        return errors

    def check_reason_required(self, meeting_id: int) -> bool:
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            ["motions_reason_required"],
        )
        return meeting.get("motions_reason_required", False)

    def _check_recommendation_and_state(
        self, instance: dict[str, Any]
    ) -> list[MotionActionErrorData]:
        errors: list[MotionActionErrorData] = []
        for prefix in ("recommendation", "state"):
            if f"{prefix}_extension" in instance:
                possible_rerids = EXTENSION_REFERENCE_IDS_PATTERN.findall(
                    instance[f"{prefix}_extension"]
                )
                for fqid in possible_rerids:
                    collection, id_ = collection_and_id_from_fqid(fqid)
                    if collection != "motion":
                        errors.append(
                            {
                                "type": (
                                    MotionErrorType.STATE_EXTENSION
                                    if prefix == "state"
                                    else MotionErrorType.RECO_EXTENSION
                                ),
                                "message": f"Found {fqid} but only motion is allowed.",
                            }
                        )
        return errors

    def _check_diff_version(
        self, instance: dict[str, Any], datastore_instance: dict[str, Any] = {}
    ) -> list[MotionActionErrorData]:
        if instance.get("lead_motion_id") or datastore_instance.get("lead_motion_id"):
            return [
                {
                    "type": (MotionErrorType.DIFF_VERSION),
                    "message": "You can define a diff_version only for the lead motion",
                }
            ]
        return []


class MotionCreatePayloadValidationMixin(MotionBasePayloadValidationMixin):
    """
    Mixin for validating motion.create payloads.
    The function get_create_payload_integrity_error_message will deliver a string array with all error messages
    """

    def get_create_payload_integrity_error_message(
        self, instance: dict[str, Any], meeting_id: int
    ) -> list[MotionActionErrorData]:
        return (
            self._create_conduct_before_checks(instance, meeting_id)
            + self.conduct_common_checks(instance, meeting_id)
            + self._create_conduct_after_checks(instance)
        )

    def _create_conduct_before_checks(
        self, instance: dict[str, Any], meeting_id: int
    ) -> list[MotionActionErrorData]:
        errors: list[MotionActionErrorData] = []
        if not instance.get("title"):
            errors.append(
                {"type": MotionErrorType.TITLE, "message": "Title is required"}
            )
        if instance.get("lead_motion_id"):
            if not instance.get("text") and not instance.get("amendment_paragraphs"):
                errors.append(
                    {
                        "type": MotionErrorType.TEXT,
                        "message": "Text or amendment_paragraphs is required in this context.",
                    }
                )
            elif instance.get("text") and instance.get("amendment_paragraphs"):
                errors.append(
                    {
                        "type": MotionErrorType.MOTION_TYPE,
                        "message": "You can't give both of text and amendment_paragraphs",
                    }
                )
        else:
            if not instance.get("text"):
                errors.append(
                    {"type": MotionErrorType.TEXT, "message": "Text is required"}
                )
            if instance.get("amendment_paragraphs"):
                errors.append(
                    {
                        "type": MotionErrorType.AMENDMENT_PARAGRAPHS,
                        "message": "You can't give amendment_paragraphs in this context",
                    }
                )
        if instance.get("diff_version"):
            errors += self._check_diff_version(instance)
        if (not instance.get("reason")) and self.check_reason_required(meeting_id):
            errors.append(
                {"type": MotionErrorType.REASON, "message": "Reason is required"}
            )
        if "additional_submitter" in instance and not self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            ["motions_create_enable_additional_submitter_text"],
        ).get("motions_create_enable_additional_submitter_text"):
            errors.append(
                {
                    "type": MotionErrorType.ADDITIONAL_SUBMITTER,
                    "message": "This meeting doesn't allow additional_submitter to be set in creation",
                }
            )
        return errors

    def _create_conduct_after_checks(
        self, instance: dict[str, Any]
    ) -> list[MotionActionErrorData]:
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            [
                "motions_default_workflow_id",
                "motions_default_amendment_workflow_id",
            ],
        )
        workflow_id = instance.get("workflow_id", None)
        if workflow_id is None:
            if instance.get("lead_motion_id"):
                workflow_id = meeting.get("motions_default_amendment_workflow_id")
            else:
                workflow_id = meeting.get("motions_default_workflow_id")
        if not workflow_id:
            return [
                {
                    "type": MotionErrorType.WORKFLOW,
                    "message": "No matching default workflow defined on this meeting",
                }
            ]
        return []


class MotionUpdatePayloadValidationMixin(MotionBasePayloadValidationMixin):
    """
    Mixin for validating motion.update payloads.
    The function get_update_payload_integrity_error_message will deliver a string array with all error messages
    """

    def get_update_payload_integrity_error_message(
        self, instance: dict[str, Any], meeting_id: int
    ) -> list[MotionActionErrorData]:
        return self._update_conduct_before_checks(
            instance, meeting_id
        ) + self.conduct_common_checks(instance, meeting_id)

    def _update_conduct_before_checks(
        self, instance: dict[str, Any], meeting_id: int
    ) -> list[MotionActionErrorData]:
        errors: list[MotionActionErrorData] = []
        if (
            instance.get("text")
            or instance.get("amendment_paragraphs")
            or instance.get("diff_version")
        ):
            motion = self.datastore.get(
                fqid_from_collection_and_id("motion", instance["id"]),
                ["text", "amendment_paragraphs", "lead_motion_id"],
            )
        if instance.get("text"):
            if not motion.get("text"):
                errors.append(
                    {
                        "type": MotionErrorType.TEXT,
                        "message": "Cannot update text, because it was not set in the old values.",
                    }
                )
        if instance.get("amendment_paragraphs"):
            if not motion.get("amendment_paragraphs"):
                errors.append(
                    {
                        "type": MotionErrorType.AMENDMENT_PARAGRAPHS,
                        "message": "Cannot update amendment_paragraphs, because it was not set in the old values.",
                    }
                )
        if instance.get("reason") == "" and self.check_reason_required(meeting_id):
            errors.append(
                {
                    "type": MotionErrorType.REASON,
                    "message": "Reason is required to update.",
                }
            )
        if instance.get("diff_version"):
            errors += self._check_diff_version(instance, motion)
        return errors
