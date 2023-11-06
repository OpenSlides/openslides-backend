from re import search, sub
from typing import Any, Dict, Iterable, List, Optional, cast

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
                    "required": [],
                    "additionalProperties": False,
                },
                "minItems": 1,
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
        {
            "property": "submitters_verbose",
            "type": "string",
            "is_list": True,
            "is_hidden": True,
        },
        {
            "property": "submitters_username",
            "type": "string",
            "is_object": True,
            "is_list": True,
        },
        {
            "property": "supporters_verbose",
            "type": "string",
            "is_list": True,
            "is_hidden": True,
        },
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
        {
            "property": "motion_amendment",
            "type": "boolean",
            "is_object": True,
            "is_hidden": True,
        },
    ]
    permission = Permissions.Motion.CAN_MANAGE
    row_state: ImportState
    number_lookup: Lookup
    username_lookup: Lookup
    category_lookup: Lookup
    tags_lookup: Lookup
    block_lookup: Lookup
    _first_state_id: Optional[int] = None
    _operator_username: Optional[str] = None

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # transform instance into a correct create/update payload
        # try to find a pre-existing motion with the same number
        # if there is one, validate for a motion.create, otherwise for a motion.update
        # using get_create_payload_integrity_error_message and get_update_payload_integrity_error_message

        data = instance.pop("data")
        data = self.add_payload_index_to_action_data(data)
        self.setup_lookups(data)

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

        if (is_amendment := entry.get("motion_amendment")) and type(
            is_amendment
        ) == bool:
            entry["motion_amendment"] = {
                "value": is_amendment,
                "info": ImportState.WARNING,
            }
            messages.append("Amendments cannot be correctly imported")

        if (category_name := entry.get("category_name")) and type(category_name) == str:
            category_prefix = entry.get("category_prefix")
            categories = self.category_lookup.name_to_ids[category_name]
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
                messages.append("Error: Found multiple motions with the same number")
        else:
            category_id: Optional[int] = None
            if entry.get("category_name"):
                category_id = entry["category_name"].get("id")
            self.row_state = ImportState.NEW
            value: Dict[str, Any] = {}
            self.set_number(
                value,
                meeting_id,
                self._get_first_workflow_state_id(meeting_id),
                None,
                category_id,
            )
            if number := value.get("number"):
                entry["number"] = {"value": number, "info": ImportState.GENERATED}

        for field in ["submitters", "supporters"]:
            if users := entry.get(field + "_username"):
                if not isinstance(users, list):
                    users = [users]
                verbose = entry.get(field + "_verbose", [])
                if not isinstance(verbose, list):
                    verbose = [verbose]
                verbose_user_mismatch = len(verbose) > len(users)
                entry_list: list[Dict[str, Any]] = []
                message_set = set()
                for user in users:
                    if isinstance(user, str):
                        if verbose_user_mismatch:
                            entry_list.append(
                                {"value": user, "info": ImportState.ERROR}
                            )
                        check_result = self.username_lookup.check_duplicate(user)
                        user_id = cast(
                            int, self.username_lookup.get_field_by_name(user, "id")
                        )
                        if check_result == ResultType.FOUND_ID and user_id != 0:
                            entry_list.append(
                                {
                                    "value": user,
                                    "info": ImportState.DONE,
                                    "id": user_id,
                                }
                            )
                        elif check_result == ResultType.NOT_FOUND or user_id == 0:
                            entry_list.append(
                                {
                                    "value": user,
                                    "info": ImportState.WARNING,
                                }
                            )
                            message_set.add(
                                "Could not find the user for at least one username"
                            )
                        elif check_result == ResultType.FOUND_MORE_IDS:
                            entry_list.append(
                                {
                                    "value": user,
                                    "info": ImportState.WARNING,
                                }
                            )
                            message_set.add(
                                "Found multiple users for at least one username"
                            )
                entry[field + "_username"] = entry_list
                if verbose_user_mismatch:
                    self.row_state = ImportState.ERROR
                    message_set.add(
                        "Error: Verbose field is set and has more entries than the username field"
                    )
                messages.extend(
                    [
                        field[0].upper() + field[1:] + ": " + message
                        for message in message_set
                    ]
                )

        if len((cast(List[dict[str, Any]], entry.get("submitters_username", [])))) == 0:
            entry["submitter_usernames"] = [self._get_self_username_object()]

        if tags := entry.get("tags"):
            if not isinstance(tags, list):
                tags = [tags]
            entry_list = []
            message_set = set()
            for tag in tags:
                if isinstance(tag, str):
                    check_result = self.tags_lookup.check_duplicate(tag)
                    tag_id = cast(int, self.tags_lookup.get_field_by_name(tag, "id"))
                    if check_result == ResultType.FOUND_ID and tag_id != 0:
                        entry_list.append(
                            {
                                "value": tag,
                                "info": ImportState.DONE,
                                "id": tag_id,
                            }
                        )
                    elif check_result == ResultType.NOT_FOUND or tag_id == 0:
                        entry_list.append(
                            {
                                "value": tag,
                                "info": ImportState.WARNING,
                            }
                        )
                        message_set.add("Could not find at least one tag")
                    elif check_result == ResultType.FOUND_MORE_IDS:
                        entry_list.append(
                            {
                                "value": tag,
                                "info": ImportState.WARNING,
                            }
                        )
                        message_set.add("Found multiple tags with the same name")
                entry["tags"] = entry_list
                messages.extend([message for message in message_set])

        if (block := entry.get("block")) and type(block) == str:
            check_result = self.block_lookup.check_duplicate(block)
            block_id = cast(int, self.block_lookup.get_field_by_name(block, "id"))
            if check_result == ResultType.FOUND_ID and block_id != 0:
                entry["block"] = {
                    "value": block,
                    "info": ImportState.DONE,
                    "id": block_id,
                }
            elif check_result == ResultType.NOT_FOUND or block_id == 0:
                entry["block"] = {
                    "value": block,
                    "info": ImportState.WARNING,
                }
                messages.append("Couldn't find motion block")
            elif check_result == ResultType.FOUND_MORE_IDS:
                entry["block"] = {
                    "value": block,
                    "info": ImportState.WARNING,
                }
                messages.append("Found multiple motion blocks with the same name")

        # TODO: Currently doesn't recognize pre-existing tags
        if (
            (text := entry.get("text"))
            and type(text) == str
            and not search(r"^<\w+[^>]*>[\w\W]*?<\/\w>$", text)
        ):
            entry["text"] = (
                "<p>"
                + sub(r"\n", "<br />", sub(r"\n([ \t]*\n)+", "</p><p>", text))
                + "</p>"
            )

        for field in ["title", "text", "reason"]:
            if (date := entry.get(field)) and type(date) == str:
                entry[field] = {"value": date, "info": ImportState.DONE}

        # check via mixin
        payload = {
            **{
                k: v.get("value")
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
                if entry.get(v)
            },
            **{
                k: self._get_field_id(entry, v)
                for k, v in {
                    "category_id": "category_name",
                    "block_id": "block",
                }.items()
                if entry.get(v)
            },
        }
        errors: List[MotionActionErrorData] = []
        if id_:
            payload = {"id": id_, **payload}
            errors = self.get_update_payload_integrity_error_message(
                payload, meeting_id
            )
        else:
            payload = {"meeting_id": meeting_id, **payload}
            errors = self.get_create_payload_integrity_error_message(
                payload, meeting_id
            )
            if not (
                self.row_state == ImportState.WARNING
                or self.row_state == ImportState.ERROR
            ):
                # Important for motion number generation
                # TODO: Replace reserve_id with something that doesn't indefinately close up that id
                motion_id = self.datastore.reserve_id("motion")
                self.apply_instance(payload, "motion/" + str(motion_id))

        for err in errors:
            entry = self._add_error_to_entry(entry, err)
            messages.append("Error: " + err["message"])

        return {"state": self.row_state, "messages": messages, "data": entry}

    def setup_lookups(self, data: Iterable[Dict[str, Any]]) -> None:
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
            field="category_name",
            collection_field="name",
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

    def _get_self_username_object(self) -> Dict[str, Any]:
        if not self._operator_username:
            user = self.datastore.get("user/" + str(self.user_id), ["username"])
            if not (user and user.get("username")):
                raise ActionException("Couldn't find operator's username")
            self._operator_username = cast(str, user["username"])
        return {
            "value": self._operator_username,
            "info": ImportState.GENERATED,
            "id": self.user_id,
        }

    def _get_first_workflow_state_id(self, meeting_id: int) -> int:
        if not self._first_state_id:
            default_workflows = self.datastore.filter(
                "motion_workflow",
                FilterOperator("default_workflow_meeting_id", "=", meeting_id),
                mapped_fields=["first_state_id"],
            ).values()
            if len(default_workflows) != 1:
                raise ActionException("Couldn't determine default workflow")
            self._first_state_id = cast(
                int, list(default_workflows)[0].get("first_state_id")
            )
        return self._first_state_id

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
            case MotionErrorType.TITLE:
                fieldname = "title"
            case _:
                raise ActionException("Error: " + err["message"])
        if not (entry.get(fieldname) and isinstance(entry[fieldname], dict)):
            entry[fieldname] = {
                "value": entry.get(fieldname, ""),
                "info": ImportState.ERROR,
            }
        else:
            entry[fieldname]["info"] = ImportState.ERROR
        self.row_state = ImportState.ERROR
        return entry
