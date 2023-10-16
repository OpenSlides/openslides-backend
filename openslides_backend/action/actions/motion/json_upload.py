from typing import Any, Dict, List, Optional

from ....models.models import Motion
from ....permissions.permissions import Permissions
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import ImportState, JsonUploadMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .payload_validation_mixin import (
    MotionActionErrorData,
    MotionCreatePayloadValidationMixin,
    MotionUpdatePayloadValidationMixin,
)

LIST_TYPE = {
    "anyOf": [
        {
            "type": "array",
            "items": {"type": "string"},
        },
        {"type": "string"},
    ]
}


@register_action("motion.json_upload")
class MotionJsonUpload(
    JsonUploadMixin,
    MotionCreatePayloadValidationMixin,
    MotionUpdatePayloadValidationMixin,
):
    """
    Action to allow to upload a json. It is used as first step of an import.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_default_schema(
        additional_required_fields={
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        **model.get_properties(
                            "title",
                            "text",
                            "number",
                            "reason",
                        ),
                        **{
                            "submitters_verbose": LIST_TYPE,
                            "submitters_username": LIST_TYPE,
                            "supporters_verbose": LIST_TYPE,
                            "supporters_username": LIST_TYPE,
                            "category_name": {"type": "string"},
                            "category_prefix": {"type": "string"},
                            "tags": LIST_TYPE,
                            "block": {"type": "string"},
                            "motion_amendment": {"type": "string"},
                        },
                    },
                    "required": ["title", "text"],
                    "additionalProperties": False,
                },
                "minItems": 2,
                "uniqueItems": False,
            },
            "meeting_id": required_id_schema,
        }
    )

    headers = [
        {"property": "title", "type": "string"},
        {"property": "text", "type": "string"},
        {"property": "number", "type": "string", "is_object": True},
        {"property": "reason", "type": "string"},
        {"property": "submitters_verbose", "type": "string", "is_list": True},
        {
            "property": "submitters_username",
            "type": "string",
            "is_object": True,
            "is_list": True,
        },
        {"property": "supporters_verbose", "type": "string", "is_list": True},
        {
            "property": "supporters_username",
            "type": "string",
            "is_object": True,
            "is_list": True,
        },
        {"property": "category_name", "type": "string", "is_object": True},
        {"property": "category_prefix", "type": "string"},
        {"property": "tags", "type": "string", "is_object": True, "is_list": True},
        {"property": "block", "type": "string", "is_object": True},
        {"property": "motion_amendment", "type": "boolean", "is_object": True},
    ]
    permission = Permissions.Motion.CAN_MANAGE
    row_state: ImportState

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # transform instance into a correct create/update payload
        # try to find a pre-existing motion with the same number
        # if there is one, validate for a motion.create, otherwise for a motion.update
        # using get_create_payload_integrity_error_message and get_update_payload_integrity_error_message

        data = instance.pop("data")
        data = self.add_payload_index_to_action_data(data)

        # enrich data with meeting_id
        for entry in data:
            entry["meeting_id"] = instance["meeting_id"]

        self.rows = [self.validate_entry(entry) for entry in data]

        # generate statistics
        itemCount = len(self.rows)
        state_to_count = {state: 0 for state in ImportState}
        for row in self.rows:
            state_to_count[row["state"]] += 1
            state_to_count[ImportState.WARNING] += self.count_warnings_in_payload(
                row.get("data", {}).values()
            )
            row["data"].pop("payload_index", None)

        self.statistics = [
            {"name": "total", "value": itemCount},
            {"name": "created", "value": state_to_count[ImportState.NEW]},
            {"name": "updated", "value": state_to_count[ImportState.DONE]},
            {"name": "error", "value": state_to_count[ImportState.ERROR]},
            {"name": "warning", "value": state_to_count[ImportState.WARNING]},
        ]

        self.set_state(
            state_to_count[ImportState.ERROR], state_to_count[ImportState.WARNING]
        )
        self.store_rows_in_the_import_preview("motion")
        return {}

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        messages: List[str] = []
        id_: Optional[int] = None
        meeting_id: int = entry["meeting_id"]
        if (number := entry.get("number")) and type(number) == str:
            # look for motion with that number and, if found "id_ = motion_id"
            pass

        # transform entry

        # check via mixin
        payload = {
            **{
                k: v
                for k, v in entry.items()
                if k in ["title", "text", "number", "reason"]
            },
            **{
                k: self.get_ids(entry, v)
                for k, v in {
                    "submitter_ids": "submitters_username",
                    "supporter_meeting_user_ids": "supporters_username",
                    "tag_ids": "tags",
                }.items()
                if entry[v]
            },
            **{
                k: self.get_id(entry, v)
                for k, v in {
                    "category_id": "category_name",
                    "block_id": "block",
                }.items()
                if entry[v]
            },
        }
        errors: List[MotionActionErrorData] = []
        if id_:
            payload = {"id": id_, **payload}
            self.row_state = ImportState.DONE
            errors = self.get_update_payload_integrity_error_message(
                payload, meeting_id
            )
        else:
            payload = {"meeting_id": meeting_id, **payload}
            self.row_state = ImportState.NEW
            errors = self.get_create_payload_integrity_error_message(
                payload, meeting_id
            )

        for err in errors:
            entry = self.add_error_to_entry(entry, err)
            messages.append(err["message"])

        return {"state": self.row_state, "messages": messages, "data": entry}

    def get_ids(self, entry: Dict[str, Any], fieldname: str) -> List[int]:
        value = entry[fieldname]
        if not isinstance(value, list):
            value = [entry[fieldname]]
        return [val["id"] for val in value if val.get("id")]

    def get_id(self, entry: Dict[str, Any], fieldname: str) -> int:
        return entry[fieldname].get("id")

    def add_error_to_entry(
        self, entry: Dict[str, Any], err: MotionActionErrorData
    ) -> Dict[str, Any]:
        # TODO: Make a switch on err's type, determine the correct field and severity from that and change the state of the entry (and self.row_state) if necessary
        return entry
