from typing import Any, Dict, List, Optional, cast

from openslides_backend.shared.filters import FilterOperator

from ....models.models import Motion
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import ImportState, JsonUploadMixin, Lookup, ResultType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .payload_validation_mixin import (
    MotionActionErrorData,
    MotionCreatePayloadValidationMixin,
    MotionErrorType,
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
    number_lookup: Lookup
    username_lookup: Lookup
    category_lookup: Lookup
    tags_lookup: Lookup
    block_lookup: Lookup

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

        # TODO if motion_amendment is true, throw error

        if (category_name := entry.get("category_name")) and type(category_name) == str:
            categories = self.number_lookup.name_to_ids[category_name]
            if (category_prefix := entry.get("category_prefix")) and type(
                category_prefix
            ) == str:
                categories = [
                    category
                    for category in categories
                    if category.get("prefix") == category_prefix and category.get("id")
                ]
            if len(categories) == 1:
                entry["category_name"] = {
                    "value": category_name,
                    "info": ImportState.DONE,
                    "id": categories[0].get("id"),
                }
            else:
                entry["category_name"] = {
                    "value": category_name,
                    "info": ImportState.WARNING,
                }
                messages.append("Category could not be found")
        elif (category_prefix := entry.get("category_prefix")) and type(
            category_prefix
        ) == str:
            entry["category_name"] = {"value": "", "info": ImportState.WARNING}
            messages.append("Category could not be found")

        if (number := entry.get("number")) and type(number) == str:
            check_result = self.number_lookup.check_duplicate(number)
            id_ = cast(int, self.number_lookup.get_field_by_name(number, "id"))
            if check_result == ResultType.FOUND_ID and id_ != 0:
                self.row_state = ImportState.DONE
                entry["id"] = id_
                entry["number"] = {
                    "value": number,
                    "info": ImportState.DONE,
                    "id": id_,
                }
            elif check_result == ResultType.NOT_FOUND or id_ == 0:
                self.row_state = ImportState.NEW
                entry["number"] = {
                    "value": number,
                    "info": ImportState.DONE,
                }
            elif check_result == ResultType.FOUND_MORE_IDS:
                self.row_state = ImportState.ERROR
                entry["number"] = {
                    "value": number,
                    "info": ImportState.ERROR,
                }
                messages.append("Found more motions with the same number")
        else:
            default_workflows = self.datastore.filter(
                "motion_workflow",
                FilterOperator("default_workflow_meeting_id", "=", meeting_id),
                mapped_fields=["first_state_id"],
            ).values()
            if len(default_workflows) != 1:
                raise ActionException("Couldn't determine default workflow")
            value: Dict[str, Any] = {}
            self.set_number(
                value,
                meeting_id,
                default_workflows[0].get("first_state_id"),
                None,
                entry["category_name"].get("id"),
            )
            if number := value["number"]:
                entry["number"] = {"value": number, "info": ImportState.GENERATED}

        # TODO transform entry for submitter, supporter, tags and block

        # check via mixin
        payload = {
            **{
                k: v
                for k, v in entry.items()
                if k in ["title", "text", "number", "reason"]
            },
            **{
                k: self._get_field_ids(entry, v)
                for k, v in {
                    "submitter_ids": "submitters_username",
                    "supporter_meeting_user_ids": "supporters_username",
                    "tag_ids": "tags",
                }.items()
                if entry[v]
            },
            **{
                k: self._get_field_id(entry, v)
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
            entry = self._add_error_to_entry(entry, err)
            messages.append(err["message"])

        return {"state": self.row_state, "messages": messages, "data": entry}

    def setup_lookups(self, data: List[Dict[str, Any]]) -> None:
        self.number_lookup = Lookup(
            self.datastore,
            "motion",
            [(number, entry) for entry in data if (number := entry.get("number"))],
            field="number",
            mapped_fields=[],
        )
        self.block_lookup = Lookup(
            self.datastore,
            "motion_block",
            [(title, entry) for entry in data if (title := entry.get("block"))],
            field="title",
            mapped_fields=[],
        )
        self.category_lookup = Lookup(
            self.datastore,
            "motion_category",
            [(name, entry) for entry in data if (name := entry.get("category_name"))],
            field="name",
            mapped_fields=["prefix"],
        )
        self.username_lookup = Lookup(
            self.datastore,
            "user",
            [
                (username, entry)
                for entry in data
                for username in set(
                    [
                        *self._get_field_array(entry, "submitters_username"),
                        *self._get_field_array(entry, "supporters_username"),
                    ]
                )
            ],
            field="username",
            mapped_fields=[],
        )
        self.tags_lookup = Lookup(
            self.datastore,
            "tag",
            [
                (name, entry)
                for entry in data
                for name in self._get_field_array(entry, "tags")
            ],
            field="name",
            mapped_fields=[],
        )

    def _get_field_array(self, entry: Dict[str, Any], fieldname: str) -> List[str]:
        date = entry.get(fieldname)
        if isinstance(date, list):
            return date
        elif date:
            return [date]
        return []

    def _get_field_ids(self, entry: Dict[str, Any], fieldname: str) -> List[int]:
        value = entry[fieldname]
        if not isinstance(value, list):
            value = [entry[fieldname]]
        return [val["id"] for val in value if val.get("id")]

    def _get_field_id(self, entry: Dict[str, Any], fieldname: str) -> int:
        return entry[fieldname].get("id")

    def _add_error_to_entry(
        self, entry: Dict[str, Any], err: MotionActionErrorData
    ) -> Dict[str, Any]:
        fieldname = ""
        match err["type"]:
            case MotionErrorType.UNIQUE_NUMBER:
                fieldname = "number"
            case MotionErrorType.TEXT:
                fieldname = "text"
            case MotionErrorType.REASON:
                fieldname = "reason"
            case _:
                raise ActionException(err["message"])
        if not (entry.get(fieldname) and isinstance(entry[fieldname], dict)):
            entry[fieldname] = {
                "value": entry.get(fieldname, ""),
                "info": ImportState.ERROR,
            }
        else:
            entry[fieldname]["info"] = ImportState.ERROR
        return entry
