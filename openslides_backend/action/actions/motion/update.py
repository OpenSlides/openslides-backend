import time
from copy import deepcopy
from typing import Any

from openslides_backend.shared.typing import HistoryInformation

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.patterns import (
    EXTENSION_REFERENCE_IDS_PATTERN,
    Collection,
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
)
from ....shared.schema import (
    id_list_schema,
    number_string_json_schema,
    optional_id_schema,
)
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..meeting_mediafile.attachment_mixin import AttachmentMixin
from .mixins import (
    AmendmentParagraphHelper,
    PermissionHelperMixin,
    TextHashMixin,
    set_workflow_timestamp_helper,
)
from .payload_validation_mixin import MotionUpdatePayloadValidationMixin


@register_action("motion.update")
class MotionUpdate(
    MotionUpdatePayloadValidationMixin,
    AmendmentParagraphHelper,
    PermissionHelperMixin,
    TextHashMixin,
    AttachmentMixin,
    UpdateAction,
):
    """
    Action to update motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(
        optional_properties=[
            "title",
            "number",
            "diff_version",
            "additional_submitter",
            "text",
            "reason",
            "modified_final_version",
            "state_extension",
            "recommendation_extension",
            "start_line_number",
            "category_id",
            "block_id",
            "tag_ids",
            "created",
            "workflow_timestamp",
        ],
        additional_optional_fields={
            "workflow_id": optional_id_schema,
            "amendment_paragraphs": number_string_json_schema,
            "attachment_mediafile_ids": id_list_schema,
        },
    )

    def prefetch(self, action_data: ActionData) -> None:
        self.datastore.get_many(
            [
                GetManyRequest(
                    "motion",
                    list(
                        {
                            instance["id"]
                            for instance in action_data
                            if instance.get("id")
                        }
                    ),
                    [
                        "meeting_id",
                        "id",
                        "lead_motion_id",
                        "identical_motion_ids",
                        "category_id",
                        "block_id",
                        "tag_ids",
                        "attachment_meeting_mediafile_ids",
                        "recommendation_extension_reference_ids",
                        "state_id",
                        "submitter_ids",
                        "text",
                        "amendment_paragraphs",
                    ],
                )
            ]
        )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        timestamp = round(time.time())
        instance["last_modified"] = timestamp
        motion = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["meeting_id"],
        )
        error_messages = self.get_update_payload_integrity_error_message(
            instance, motion["meeting_id"]
        )
        if len(error_messages):
            raise ActionException(error_messages[0]["message"])
        if instance.get("amendment_paragraphs"):
            self.validate_amendment_paragraphs(instance)

        if instance.get("workflow_id"):
            workflow_id = instance.pop("workflow_id")
            motion = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["state_id", "workflow_timestamp"],
            )
            state = self.datastore.get(
                fqid_from_collection_and_id("motion_state", motion["state_id"]),
                ["workflow_id"],
            )
            if workflow_id != state.get("workflow_id"):
                workflow = self.datastore.get(
                    fqid_from_collection_and_id("motion_workflow", workflow_id),
                    ["first_state_id"],
                )
                instance["state_id"] = workflow["first_state_id"]
                instance["recommendation_id"] = None
                if "workflow_timestamp" not in instance:
                    set_workflow_timestamp_helper(self.datastore, instance, timestamp)

        for prefix in ("recommendation", "state"):
            if f"{prefix}_extension" in instance:
                self.set_extension_reference_ids(prefix, instance)

        self.set_text_hash(instance)
        return instance

    def set_extension_reference_ids(
        self, prefix: str, instance: dict[str, Any]
    ) -> None:
        extension_reference_ids = []
        possible_rerids = EXTENSION_REFERENCE_IDS_PATTERN.findall(
            instance[f"{prefix}_extension"]
        )
        motion_ids = []
        for fqid in possible_rerids:
            collection, id_ = collection_and_id_from_fqid(fqid)
            motion_ids.append(int(id_))
        if motion_ids:
            gm_request = GetManyRequest("motion", motion_ids, ["id"])
            gm_result = self.datastore.get_many([gm_request]).get("motion", {})
            for motion_id in gm_result:
                extension_reference_ids.append(
                    fqid_from_collection_and_id("motion", motion_id)
                )
        instance[f"{prefix}_extension_reference_ids"] = extension_reference_ids

    def check_permissions(self, instance: dict[str, Any]) -> None:
        motion = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["meeting_id", "state_id", "submitter_ids"],
            lock_result=False,
        )

        # check for can_manage, all allowed
        perm = Permissions.Motion.CAN_MANAGE
        if has_perm(self.datastore, self.user_id, perm, motion["meeting_id"]):
            return

        # check for can_manage_metadata and whitelist
        perm = Permissions.Motion.CAN_MANAGE_METADATA
        allowed_fields = ["id"]
        if has_perm(self.datastore, self.user_id, perm, motion["meeting_id"]):
            allowed_fields += [
                "category_id",
                "block_id",
                "additional_submitter",
                "recommendation_extension",
                "start_line_number",
                "tag_ids",
                "state_extension",
                "created",
                "workflow_timestamp",
            ]

        # check for self submitter and whitelist
        if self.is_allowed_and_submitter(
            motion.get("submitter_ids", []), motion["state_id"]
        ):
            allowed_fields += [
                "title",
                "text",
                "reason",
                "amendment_paragraphs",
            ]

        forbidden_fields = [field for field in instance if field not in allowed_fields]
        if forbidden_fields:
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Forbidden fields: {', '.join(forbidden_fields)}"
            raise PermissionDenied(msg)

    def get_history_information(self) -> HistoryInformation | None:
        information = {}
        for instance in deepcopy(self.instances):
            instance_information = []

            # workflow timestamp changed
            if "workflow_timestamp" in instance:
                timestamp = instance.pop("workflow_timestamp")
                instance_information.extend(
                    ["Workflow_timestamp set to {}", f"{timestamp}"]
                )

            # category changed
            instance_information.extend(
                self.create_history_information_for_field(
                    instance,
                    "category_id",
                    "motion_category",
                    "Category",
                )
            )

            # block changed
            instance_information.extend(
                self.create_history_information_for_field(
                    instance, "block_id", "motion_block", "Motion block"
                )
            )

            generic_update_fields = [
                "title",
                "text",
                "reason",
                "attachment_meeting_mediafile_ids",
                "amendment_paragraphs",
                "workflow_id",
                "start_line_number",
                "state_extension",
            ]
            if any(field in instance for field in generic_update_fields):
                # still other fields given, so we also add the generic "updated" message
                instance_information.append("Motion updated")

            if instance_information:
                information[
                    fqid_from_collection_and_id(self.model.collection, instance["id"])
                ] = instance_information

        return information

    def create_history_information_for_field(
        self,
        instance: dict[str, Any],
        field: str,
        collection: Collection,
        verbose_collection: str,
    ) -> list[str]:
        if field in instance:
            value = instance.pop(field)
            if value is None:
                return [verbose_collection + " removed"]
            else:
                return [
                    verbose_collection + " set to {}",
                    fqid_from_collection_and_id(collection, value),
                ]
        return []
