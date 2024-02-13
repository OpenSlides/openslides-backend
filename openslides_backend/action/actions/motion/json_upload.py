from collections import defaultdict
from collections.abc import Iterable
from re import search, sub
from typing import Any, cast

from openslides_backend.shared.filters import And, Filter, FilterOperator, Or

from ....models.models import Motion
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import (
    BaseJsonUploadAction,
    ImportState,
    Lookup,
    ResultType,
)
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
    BaseJsonUploadAction,
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
        {"property": "title", "type": "string", "is_object": True},
        {"property": "text", "type": "string", "is_object": True},
        {"property": "number", "type": "string", "is_object": True},
        {"property": "reason", "type": "string", "is_object": True},
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
    username_lookup: dict[str, list[dict[str, Any]]] = {}
    category_lookup: dict[str, list[dict[str, Any]]] = {}
    tags_lookup: dict[str, list[dict[str, Any]]] = {}
    block_lookup: dict[str, list[dict[str, Any]]] = {}
    _first_state_id: int | None = None
    _operator_username: str | None = None
    _previous_numbers: list[str]
    import_name = "motion"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        # transform instance into a correct create/update payload
        # try to find a pre-existing motion with the same number
        # if there is one, validate for a motion.update, otherwise for a motion.create
        # using get_update_payload_integrity_error_message and get_create_payload_integrity_error_message

        data = instance.pop("data")
        data = self.add_payload_index_to_action_data(data)
        self.setup_lookups(data, instance["meeting_id"])

        # enrich data with meeting_id
        for entry in data:
            entry["meeting_id"] = instance["meeting_id"]

        self._previous_numbers = []
        self.rows = [self.validate_entry(entry) for entry in data]

        # generate statistics
        self.generate_statistics()
        return {}

    def validate_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        messages: list[str] = []
        id_: int | None = None
        meeting_id: int = entry["meeting_id"]
        set_entry_id = False

        if (is_amendment := entry.get("motion_amendment")) is not None:
            entry["motion_amendment"] = {
                "value": is_amendment,
                "info": ImportState.DONE,
            }
            if is_amendment:
                entry["motion_amendment"]["info"] = ImportState.WARNING
                messages.append("Amendments cannot be correctly imported")

        if category_name := entry.get("category_name"):
            category_prefix = entry.get("category_prefix")
            categories = self.category_lookup.get(category_name, [])
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
        elif category_prefix := entry.get("category_prefix"):
            entry["category_name"] = {"value": "", "info": ImportState.WARNING}
            messages.append("Category could not be found")

        if number := entry.get("number"):
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
            category_id: int | None = None
            if entry.get("category_name"):
                category_id = entry["category_name"].get("id")
            self.row_state = ImportState.NEW
            value: dict[str, Any] = {}
            self.set_number(
                value,
                meeting_id,
                self._get_first_workflow_state_id(meeting_id),
                None,
                category_id,
                other_forbidden_numbers=self._previous_numbers,
            )
            if number := value.get("number"):
                entry["number"] = {"value": number, "info": ImportState.GENERATED}
                self._previous_numbers.append(number)

        has_submitter_error: bool = False
        for fieldname in ["submitter", "supporter"]:
            if users := entry.get(f"{fieldname}s_username"):
                verbose = entry.get(f"{fieldname}s_verbose", [])
                verbose_user_mismatch = len(verbose) > len(users)
                username_set: set[str] = set()
                entry_list: list[dict[str, Any]] = []
                duplicates: set[str] = set()
                not_found: set[str] = set()
                for user in users:
                    if verbose_user_mismatch:
                        entry_list.append({"value": user, "info": ImportState.ERROR})
                    elif user in username_set:
                        entry_list.append({"value": user, "info": ImportState.WARNING})
                        duplicates.add(user)
                    else:
                        username_set.add(user)
                        found_users = self.username_lookup.get(user, [])
                        if len(found_users) == 1 and found_users[0].get("id") != 0:
                            user_id = cast(int, found_users[0].get("id"))
                            entry_list.append(
                                {
                                    "value": user,
                                    "info": ImportState.DONE,
                                    "id": user_id,
                                }
                            )
                        elif len(found_users) <= 1:
                            entry_list.append(
                                {
                                    "value": user,
                                    "info": ImportState.WARNING,
                                }
                            )
                            not_found.add(user)
                        else:
                            raise ActionException(
                                f"Database corrupt: Found multiple users with the username {user}"
                            )
                entry[f"{fieldname}s_username"] = entry_list
                if verbose_user_mismatch:
                    self.row_state = ImportState.ERROR
                    messages.append(
                        f"Error: Verbose field is set and has more entries than the username field for {fieldname}s"
                    )
                    if fieldname == "submitter":
                        has_submitter_error = True
                if len(duplicates):
                    messages.append(
                        f"At least one {fieldname} has been referenced multiple times: "
                        + ", ".join(duplicates)
                    )
                if len(not_found):
                    messages.append(
                        f"Could not find at least one {fieldname}: "
                        + ", ".join(not_found)
                    )

        if not has_submitter_error:
            if (
                len(cast(list[dict[str, Any]], entry.get("submitters_username", [])))
                == 0
            ):
                entry["submitters_username"] = [self._get_self_username_object()]
            elif (
                len(
                    [
                        entry
                        for entry in (
                            cast(
                                list[dict[str, Any]],
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
            entry_list = []
            duplicates = set()
            not_found = set()
            multiple: set[str] = set()
            tags_set: set[str] = set()
            for tag in tags:
                if tag in tags_set:
                    entry_list.append({"value": tag, "info": ImportState.WARNING})
                    duplicates.add(tag)
                else:
                    tags_set.add(tag)
                    found_tags = self.tags_lookup.get(tag, [])
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
                        not_found.add(tag)
                    else:
                        entry_list.append(
                            {
                                "value": tag,
                                "info": ImportState.WARNING,
                            }
                        )
                        multiple.add(tag)
            entry["tags"] = entry_list
            if len(duplicates):
                messages.append(
                    "At least one tag has been referenced multiple times: "
                    + ", ".join(duplicates)
                )
            if len(not_found):
                messages.append(
                    "Could not find at least one tag: " + ", ".join(not_found)
                )
            if len(multiple):
                messages.append(
                    "Found multiple tags with the same name: " + ", ".join(multiple)
                )

        if (block := entry.get("block")) and isinstance(block, str):
            found_blocks = self.block_lookup.get(block, [])
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

        if (text := entry.get("text")) and not search(
            r"^<\w+[^>]*>[\w\W]*?<\/\w>$", text
        ):
            entry["text"] = (
                "<p>"
                + sub(r"\n", "<br />", sub(r"\n([ \t]*\n)+", "</p><p>", text))
                + "</p>"
            )

        for field in ["title", "text", "reason"]:
            if (date := entry.get(field)) and isinstance(date, str):
                if date == "":
                    del entry[field]
                else:
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

        errors: list[MotionActionErrorData] = []
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

        for err in errors:
            entry = self._add_error_to_entry(entry, err)
            messages.append("Error: " + err["message"])

        return {"state": self.row_state, "messages": messages, "data": entry}

    def setup_lookups(self, data: Iterable[dict[str, Any]], meeting_id: int) -> None:
        self.number_lookup = Lookup(
            self.datastore,
            "motion",
            [(number, entry) for entry in data if (number := entry.get("number"))],
            field="number",
            mapped_fields=[],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
        self.block_lookup = self.get_lookup_dict(
            "motion_block",
            [title for entry in data if (title := entry.get("block"))],
            "title",
            and_filters=[FilterOperator("meeting_id", "=", meeting_id)],
        )
        self.category_lookup = self.get_lookup_dict(
            "motion_category",
            [name for entry in data if (name := entry.get("category_name"))],
            "name",
            ["prefix"],
            and_filters=[FilterOperator("meeting_id", "=", meeting_id)],
        )
        self.username_lookup = self.get_lookup_dict(
            "user",
            list(
                {
                    username
                    for entry in data
                    if (
                        usernames := [
                            *entry.get("submitters_username", []),
                            *entry.get("supporters_username", []),
                        ]
                    )
                    for username in usernames
                    if username
                }
            ),
            "username",
            ["meeting_ids"],
        )
        self.username_lookup = {
            username: [
                date
                for date in self.username_lookup[username]
                if date.get("meeting_ids") and (meeting_id in date["meeting_ids"])
            ]
            for username in self.username_lookup
        }
        self.tags_lookup = self.get_lookup_dict(
            "tag",
            [
                name
                for entry in data
                if (names := entry.get("tags"))
                for name in names
                if name
            ],
            "name",
            and_filters=[FilterOperator("meeting_id", "=", meeting_id)],
        )

    def get_lookup_dict(
        self,
        collection: str,
        entries: list[str],
        fieldname: str = "name",
        mapped_fields: list[str] = [],
        and_filters: list[Filter] = [],
    ) -> dict[str, list[dict[str, Any]]]:
        lookup: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if len(entries):
            data = self.datastore.filter(
                collection,
                And(
                    *and_filters,
                    Or([FilterOperator(fieldname, "=", name) for name in set(entries)]),
                ),
                [*mapped_fields, "id", fieldname],
                lock_result=False,
            )
            for date in data.values():
                lookup[date[fieldname]].append(date)
        return lookup

    def _get_self_username_object(self) -> dict[str, Any]:
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

    def _get_field_array(self, entry: dict[str, Any], fieldname: str) -> list[str]:
        date = entry.get(fieldname)
        if isinstance(date, list):
            return date
        elif date:
            return [date]
        return []

    def _get_field_ids(self, entry: dict[str, Any], fieldname: str) -> list[int]:
        value = entry.get(fieldname, [])
        if not isinstance(value, list):
            value = [entry[fieldname]]
        return [val["id"] for val in value if val.get("id")]

    def _get_field_id(self, entry: dict[str, Any], fieldname: str) -> int:
        return entry[fieldname].get("id")

    def _add_error_to_entry(
        self, entry: dict[str, Any], err: MotionActionErrorData
    ) -> dict[str, Any]:
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
