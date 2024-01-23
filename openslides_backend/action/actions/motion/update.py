import time
from copy import deepcopy
from typing import Any, Dict, List, Optional

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
from ....shared.schema import number_string_json_schema, optional_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import (
    AmendmentParagraphHelper,
    PermissionHelperMixin,
    set_workflow_timestamp_helper,
)
from .set_number_mixin import SetNumberMixin


@register_action("motion.update")
class MotionUpdate(
    UpdateAction, AmendmentParagraphHelper, PermissionHelperMixin, SetNumberMixin
):
    """
    Action to update motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(
        optional_properties=[
            "title",
            "number",
            "text",
            "reason",
            "modified_final_version",
            "state_extension",
            "recommendation_extension",
            "start_line_number",
            "category_id",
            "block_id",
            "supporter_meeting_user_ids",
            "editor_id",
            "working_group_speaker_id",
            "tag_ids",
            "attachment_ids",
            "created",
        ],
        additional_optional_fields={
            "workflow_id": optional_id_schema,
            "amendment_paragraphs": number_string_json_schema,
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
                        "is_active_in_organization_id",
                        "name",
                        "id",
                        "category_id",
                        "block_id",
                        "supporter_meeting_user_ids",
                        "tag_ids",
                        "attachment_ids",
                        "recommendation_extension_reference_ids",
                        "state_id",
                        "submitter_ids",
                        "text",
                        "amendment_paragraphs",
                    ],
                )
            ]
        )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = round(time.time())
        instance["last_modified"] = timestamp
        if (
            instance.get("text")
            or instance.get("amendment_paragraphs")
            or instance.get("reason") == ""
        ):
            motion = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["text", "amendment_paragraphs", "meeting_id"],
            )

        if instance.get("text"):
            if not motion.get("text"):
                raise ActionException(
                    "Cannot update text, because it was not set in the old values."
                )
        if instance.get("amendment_paragraphs"):
            if not motion.get("amendment_paragraphs"):
                raise ActionException(
                    "Cannot update amendment_paragraphs, because it was not set in the old values."
                )
            self.validate_amendment_paragraphs(instance)
        if instance.get("reason") == "":
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", motion["meeting_id"]),
                ["motions_reason_required"],
            )
            if meeting.get("motions_reason_required"):
                raise ActionException("Reason is required to update.")

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
                set_workflow_timestamp_helper(self.datastore, instance, timestamp)

        for prefix in ("recommendation", "state"):
            if f"{prefix}_extension" in instance:
                self.set_extension_reference_ids(prefix, instance)

        if instance.get("number"):
            meeting_id = self.get_meeting_id(instance)
            if not self._check_if_unique(
                instance["number"], meeting_id, instance["id"]
            ):
                raise ActionException("Number is not unique.")

        return instance

    def set_extension_reference_ids(
        self, prefix: str, instance: Dict[str, Any]
    ) -> None:
        extension_reference_ids = []
        possible_rerids = EXTENSION_REFERENCE_IDS_PATTERN.findall(
            instance[f"{prefix}_extension"]
        )
        motion_ids = []
        for fqid in possible_rerids:
            collection, id_ = collection_and_id_from_fqid(fqid)
            if collection != "motion":
                raise ActionException(f"Found {fqid} but only motion is allowed.")
            motion_ids.append(int(id_))
        if motion_ids:
            gm_request = GetManyRequest("motion", motion_ids, ["id"])
            gm_result = self.datastore.get_many([gm_request]).get("motion", {})
            for motion_id in gm_result:
                extension_reference_ids.append(
                    fqid_from_collection_and_id("motion", motion_id)
                )
        instance[f"{prefix}_extension_reference_ids"] = extension_reference_ids

    def check_permissions(self, instance: Dict[str, Any]) -> None:
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
                "supporter_meeting_user_ids",
                "recommendation_extension",
                "start_line_number",
                "tag_ids",
                "state_extension",
                "created",
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

    def get_history_information(self) -> Optional[HistoryInformation]:
        information = {}
        for instance in deepcopy(self.instances):
            instance_information = []

            # supporters changed
            if "supporter_meeting_user_ids" in instance:
                instance.pop("supporter_meeting_user_ids")
                instance_information.append("Supporters changed")

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
                "attachment_ids",
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
        instance: Dict[str, Any],
        field: str,
        collection: Collection,
        verbose_collection: str,
    ) -> List[str]:
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
