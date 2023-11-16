from re import search, sub
from typing import Any, Dict, Iterable, List, Optional, Set, cast

from openslides_backend.shared.filters import And, FilterOperator, Or

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
                            "motion_amendment": {"type": "boolean"},
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
    submitter_lookup: Lookup
    supporter_lookup: Lookup
    category_lookup: Lookup
    tags_lookup: Lookup
    block_lookup: Lookup
    _first_state_id: Optional[int] = None
    _operator_username: Optional[str] = None

    _last_motion_mock_id: Optional[int] = None
    _user_ids_to_meeting_user: Dict[int, Any]

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # transform instance into a correct create/update payload
        # try to find a pre-existing motion with the same number
        # if there is one, validate for a motion.create, otherwise for a motion.update
        # using get_create_payload_integrity_error_message and get_update_payload_integrity_error_message

        data = instance.pop("data")
        data = self.add_payload_index_to_action_data(data)
        self.setup_lookups(data, instance["meeting_id"])

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
        set_entry_id = False

        if (is_amendment := entry.get("motion_amendment")) and isinstance(
            is_amendment, bool
        ):
            entry["motion_amendment"] = {
                "value": is_amendment,
                "info": ImportState.WARNING,
            }
            messages.append("Amendments cannot be correctly imported")

        if (category_name := entry.get("category_name")) and isinstance(
            category_name, str
        ):
            category_prefix = entry.get("category_prefix")
            categories = self.category_lookup.get_matching_data_by_name(category_name)
            categories = [
                category
                for category in categories
                if category.get("prefix") == category_prefix
            ]
            if len(categories) == 1 and categories[0].get("id") != 0:
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
        elif (category_prefix := entry.get("category_prefix")) and isinstance(
            category_prefix, str
        ):
            entry["category_name"] = {"value": "", "info": ImportState.WARNING}
            messages.append("Category could not be found")

        if (number := entry.get("number")) and isinstance(number, str):
            check_result = self.number_lookup.check_duplicate(number)
            id_ = cast(int, self.number_lookup.get_field_by_name(number, "id"))
            if check_result == ResultType.FOUND_ID and id_ != 0:
                self.row_state = ImportState.DONE
                set_entry_id = True
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

        has_submitter_error: bool = False
        for fieldname in ["submitter", "supporter"]:
            if users := entry.get(f"{fieldname}s_username"):
                if not isinstance(users, list):
                    users = [users]
                verbose = entry.get(f"{fieldname}s_verbose", [])
                if not isinstance(verbose, list):
                    verbose = [verbose]
                verbose_user_mismatch = len(verbose) > len(users)
                username_set: Set[str] = set([])
                entry_list: list[Dict[str, Any]] = []
                message_set = set()
                lookup = (
                    self.submitter_lookup
                    if fieldname == "submitter"
                    else self.supporter_lookup
                )
                for user in users:
                    if isinstance(user, str):
                        if verbose_user_mismatch:
                            entry_list.append(
                                {"value": user, "info": ImportState.ERROR}
                            )
                        elif user in username_set:
                            entry_list.append(
                                {"value": user, "info": ImportState.WARNING}
                            )
                            message_set.add(
                                f"At least one {fieldname} has been referenced multiple times"
                            )
                        else:
                            username_set.add(user)
                            found_users = lookup.get_matching_data_by_name(user)
                            if len(found_users) == 1 and found_users[0].get("id") != 0:
                                user_id = cast(int, found_users[0].get("id"))
                                if len(
                                    self._user_ids_to_meeting_user.get(user_id, {}).get(
                                        "group_ids", []
                                    )
                                ):
                                    entry_list.append(
                                        {
                                            "value": user,
                                            "info": ImportState.DONE,
                                            "id": user_id,
                                        }
                                    )
                                else:
                                    entry_list.append(
                                        {"value": user, "info": ImportState.WARNING}
                                    )
                                    message_set.add(
                                        f"At least one {fieldname} is not part of this meeting"
                                    )
                            elif len(found_users) <= 1:
                                entry_list.append(
                                    {
                                        "value": user,
                                        "info": ImportState.WARNING,
                                    }
                                )
                                message_set.add(
                                    f"Could not find at least one {fieldname}"
                                )
                            else:
                                entry_list.append(
                                    {
                                        "value": user,
                                        "info": ImportState.WARNING,
                                    }
                                )
                                message_set.add(
                                    f"Found multiple users for at least one {fieldname}"
                                )
                entry[f"{fieldname}s_username"] = entry_list
                if verbose_user_mismatch:
                    self.row_state = ImportState.ERROR
                    message_set.add(
                        f"Error: Verbose field is set and has more entries than the username field for {fieldname}s"
                    )
                    if fieldname == "submitter":
                        has_submitter_error = True
                messages.extend([message for message in message_set])

        if not has_submitter_error:
            if (
                len((cast(List[dict[str, Any]], entry.get("submitters_username", []))))
                == 0
            ):
                entry["submitters_username"] = [self._get_self_username_object()]
            elif (
                len(
                    [
                        entry
                        for entry in (
                            cast(
                                List[dict[str, Any]],
                                entry.get("submitters_username", []),
                            )
                        )
                        if entry.get("info") and (entry["info"] != ImportState.WARNING)
                    ]
                )
                == 0
            ):
                entry["submitters_username"].append(self._get_self_username_object())

        if tags := entry.get("tags"):
            if not isinstance(tags, list):
                tags = [tags]
            entry_list = []
            message_set = set()
            tags_set: Set[str] = set()
            for tag in tags:
                if isinstance(tag, str):
                    if tag in tags_set:
                        entry_list.append({"value": tag, "info": ImportState.WARNING})
                        message_set.add(
                            "At least one tag has been referenced multiple times"
                        )
                    else:
                        tags_set.add(tag)
                        found_tags = self.tags_lookup.get_matching_data_by_name(tag)
                        if len(found_tags) == 1 and found_tags[0].get("id") != 0:
                            tag_id = cast(int, found_tags[0].get("id"))
                            entry_list.append(
                                {
                                    "value": tag,
                                    "info": ImportState.DONE,
                                    "id": tag_id,
                                }
                            )
                        elif len(found_tags) <= 1:
                            entry_list.append(
                                {
                                    "value": tag,
                                    "info": ImportState.WARNING,
                                }
                            )
                            message_set.add("Could not find at least one tag")
                        else:
                            entry_list.append(
                                {
                                    "value": tag,
                                    "info": ImportState.WARNING,
                                }
                            )
                            message_set.add("Found multiple tags with the same name")
            entry["tags"] = entry_list
            messages.extend([message for message in message_set])

        if (block := entry.get("block")) and isinstance(block, str):
            found_blocks = self.block_lookup.get_matching_data_by_name(block)
            if len(found_blocks) == 1 and found_blocks[0].get("id") != 0:
                block_id = cast(int, found_blocks[0].get("id"))
                entry["block"] = {
                    "value": block,
                    "info": ImportState.DONE,
                    "id": block_id,
                }
            elif len(found_blocks) <= 1:
                entry["block"] = {
                    "value": block,
                    "info": ImportState.WARNING,
                }
                messages.append("Could not find motion block")
            else:
                entry["block"] = {
                    "value": block,
                    "info": ImportState.WARNING,
                }
                messages.append("Found multiple motion blocks with the same name")

        if id_ and set_entry_id:
            entry["id"] = id_

        # TODO: Currently doesn't recognize pre-existing tags
        if (
            (text := entry.get("text"))
            and isinstance(text, str)
            and not search(r"^<\w+[^>]*>[\w\W]*?<\/\w>$", text)
        ):
            entry["text"] = (
                "<p>"
                + sub(r"\n", "<br />", sub(r"\n([ \t]*\n)+", "</p><p>", text))
                + "</p>"
            )

        for field in ["title", "text", "reason"]:
            if (date := entry.get(field)) and isinstance(date, str):
                entry[field] = {"value": date, "info": ImportState.DONE}

        for field in [
            "title",
            "text",
            "number",
            "reason",
            "category_name",
            "block",
        ]:
            if not entry.get(field):
                entry[field] = {"value": "", "info": ImportState.DONE}
        for field in ["submitters_username", "supporters_username", "tags"]:
            if not entry.get(field):
                entry[field] = []

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
            for field in [MotionErrorType.TITLE, MotionErrorType.TEXT]:
                if not payload.get(field):
                    errors.append(
                        {
                            "type": field,
                            "message": f"{field[0].capitalize() + field[1:]} is required",
                        }
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
                motion_id = self._get_motion_mock_id()
                self.apply_instance(payload, "motion/" + str(motion_id))

        for err in errors:
            entry = self._add_error_to_entry(entry, err)
            messages.append("Error: " + err["message"])

        return {"state": self.row_state, "messages": messages, "data": entry}

    def setup_lookups(self, data: Iterable[Dict[str, Any]], meeting_id: int) -> None:
        self.number_lookup = Lookup(
            self.datastore,
            "motion",
            [(number, entry) for entry in data if (number := entry.get("number"))],
            field="number",
            mapped_fields=[],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
        self.block_lookup = Lookup(
            self.datastore,
            "motion_block",
            [(title, entry) for entry in data if (title := entry.get("block"))],
            collection_field="title",
            field="block",
            mapped_fields=[],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
        self.category_lookup = Lookup(
            self.datastore,
            "motion_category",
            [(name, entry) for entry in data if (name := entry.get("category_name"))],
            field="category_name",
            collection_field="name",
            mapped_fields=["prefix"],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
        self.submitter_lookup = Lookup(
            self.datastore,
            "user",
            [
                (username, entry)
                for entry in data
                for username in self._get_field_array(entry, "submitters_username")
            ],
            field="submitters_username",
            collection_field="username",
            mapped_fields=["meeting_user_ids"],
        )
        self.supporter_lookup = Lookup(
            self.datastore,
            "user",
            [
                (username, entry)
                for entry in data
                for username in self._get_field_array(entry, "supporters_username")
            ],
            field="supporters_username",
            collection_field="username",
            mapped_fields=["meeting_user_ids"],
        )
        all_user_ids = set(
            list(self.submitter_lookup.id_to_name.keys())
            + list(self.supporter_lookup.id_to_name.keys())
        )
        all_meeting_users: Dict[int, Dict[str, Any]] = {}
        if len(all_user_ids):
            all_meeting_users = self.datastore.filter(
                "meeting_user",
                And(
                    FilterOperator("meeting_id", "=", meeting_id),
                    FilterOperator("group_ids", "!=", []),
                    FilterOperator("group_ids", "!=", None),
                    Or(
                        *[
                            FilterOperator("user_id", "=", user_id)
                            for user_id in all_user_ids
                        ]
                    ),
                ),
                [
                    "user_id",
                    "motion_submitter_ids",
                    "supported_motion_ids",
                    "group_ids",
                ],
                lock_result=False,
            )
        self._user_ids_to_meeting_user = {
            all_meeting_users[meeting_user_id]["user_id"]: all_meeting_users[
                meeting_user_id
            ]
            for meeting_user_id in all_meeting_users
            if all_meeting_users[meeting_user_id].get("user_id")
        }
        self.tags_lookup = Lookup(
            self.datastore,
            "tag",
            [
                (name, entry)
                for entry in data
                for name in self._get_field_array(entry, "tags")
            ],
            field="tags",
            collection_field="name",
            mapped_fields=[],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
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
        value = entry.get(fieldname, [])
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

    def _get_motion_mock_id(self) -> int:
        if self._last_motion_mock_id is None:
            self._last_motion_mock_id = (
                self.datastore.max("motion", FilterOperator("id", "!=", 0), field="id")
                or 0
            )
        self._last_motion_mock_id += 1
        return self._last_motion_mock_id
