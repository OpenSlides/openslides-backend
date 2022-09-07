import re
import time
from typing import Any, Dict, List, Optional, Set

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.patterns import (
    KEYSEPARATOR,
    POSITIVE_NUMBER_REGEX,
    Collection,
    fqid_from_collection_and_id,
)
from ....shared.schema import optional_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionHelperMixin

RECOMMENDATION_EXTENSION_REFERENCE_IDS_PATTERN = re.compile(r"\[(?P<fqid>\w+/\d+)\]")


@register_action("motion.update")
class MotionUpdate(UpdateAction, PermissionHelperMixin):
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
            "supporter_ids",
            "tag_ids",
            "attachment_ids",
        ],
        additional_optional_fields={
            **Motion().get_property("amendment_paragraph_$", POSITIVE_NUMBER_REGEX),
            "workflow_id": optional_id_schema,
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = round(time.time())
        instance["last_modified"] = timestamp
        if (
            instance.get("text")
            or instance.get("amendment_paragraph_$")
            or instance.get("reason") == ""
        ):
            motion = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["text", "amendment_paragraph_$", "meeting_id"],
            )

        if instance.get("text"):
            if not motion.get("text"):
                raise ActionException(
                    "Cannot update text, because it was not set in the old values."
                )
        if instance.get("amendment_paragraph_$"):
            if not motion.get("amendment_paragraph_$"):
                raise ActionException(
                    "Cannot update amendment_paragraph_$, because it was not set in the old values."
                )
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
                ["state_id", "created"],
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
                if not motion.get("created"):
                    first_state = self.datastore.get(
                        fqid_from_collection_and_id(
                            "motion_state", instance["state_id"]
                        ),
                        ["set_created_timestamp"],
                    )
                    if first_state.get("set_created_timestamp"):
                        instance["created"] = timestamp

        if instance.get("recommendation_extension"):
            self.set_recommendation_extension_reference_ids(instance)

        return instance

    def set_recommendation_extension_reference_ids(
        self, instance: Dict[str, Any]
    ) -> None:
        recommendation_extension_reference_ids = []
        possible_rerids = RECOMMENDATION_EXTENSION_REFERENCE_IDS_PATTERN.findall(
            instance["recommendation_extension"]
        )
        motion_ids = []
        for fqid_str in possible_rerids:
            collection, id_ = fqid_str.split(KEYSEPARATOR)
            if collection != "motion":
                raise ActionException(f"Found {fqid_str} but only motion is allowed.")
            motion_ids.append(int(id_))
        gm_request = GetManyRequest("motion", motion_ids, ["id"])
        gm_result = self.datastore.get_many([gm_request]).get("motion", {})
        for motion_id in gm_result:
            recommendation_extension_reference_ids.append(
                fqid_from_collection_and_id("motion", motion_id)
            )
        instance[
            "recommendation_extension_reference_ids"
        ] = recommendation_extension_reference_ids

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        motion = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["meeting_id", "state_id", "submitter_ids"],
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
                "motion_block_id",
                "origin",
                "supporters_id",
                "recommendation_extension",
                "start_line_number",
            ]

        # check for self submitter and whitelist
        if self.is_allowed_and_submitter(
            motion.get("submitter_ids", []), motion["state_id"]
        ):
            allowed_fields += [
                "title",
                "text",
                "reason",
                "amendment_paragraph_$",
            ]

        forbidden_fields = [field for field in instance if field not in allowed_fields]
        if forbidden_fields:
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Forbidden fields: {', '.join(forbidden_fields)}"
            raise PermissionDenied(msg)

    def get_history_information(self) -> Optional[List[str]]:
        informations: List[str] = []
        all_instance_fields = set(
            field for instance in self.instances for field in instance
        )

        # supporters changed
        if "supporter_ids" in all_instance_fields:
            all_instance_fields.remove("supporter_ids")
            informations.append("Supporters changed")

        # category changed
        informations.extend(
            self.create_history_information_for_field(
                all_instance_fields,
                "category_id",
                "motion_category",
                "Category",
                "name",
            )
        )

        # block changed
        informations.extend(
            self.create_history_information_for_field(
                all_instance_fields, "block_id", "motion_block", "Motion block", "title"
            )
        )

        generic_update_fields = set(
            [
                "title",
                "text",
                "reason",
                "attachment_ids",
                "amendment_paragraph_$",
                "workflow_id",
                "start_line_number",
                "state_extension",
            ]
        )
        if all_instance_fields & generic_update_fields:
            # still other fields given, so we also add the generic "updated" message
            informations.append("Motion updated")

        return informations

    def create_history_information_for_field(
        self,
        all_instance_fields: Set[str],
        field: str,
        collection: Collection,
        verbose_collection: str,
        name_field: str,
    ) -> List[str]:
        if field in all_instance_fields:
            all_instance_fields.remove(field)
            all_values = set(
                instance[field] for instance in self.instances if field in instance
            )
            if len(all_values) == 1:
                single_value = all_values.pop()
                if single_value is None:
                    return [verbose_collection + " removed"]
                else:
                    instance = self.datastore.get(
                        fqid_from_collection_and_id(collection, single_value),
                        [name_field],
                    )
                    return [verbose_collection + " set to {}", instance[name_field]]
            else:
                return [verbose_collection + " changed"]
        return []
