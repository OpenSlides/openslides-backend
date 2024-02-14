from typing import Any, cast

from openslides_backend.action.mixins.import_mixins import (
    BaseImportAction,
    ImportRow,
    ImportState,
    Lookup,
    ResultType,
)
from openslides_backend.action.util.register import register_action
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.filters import And, Filter, FilterOperator, Or

from ....models.models import ImportPreview
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...util.default_schema import DefaultSchema
from ..meeting_user.create import MeetingUserCreate
from ..motion_submitter.create import MotionSubmitterCreateAction
from ..motion_submitter.delete import MotionSubmitterDeleteAction
from ..motion_submitter.sort import MotionSubmitterSort
from .create import MotionCreate
from .payload_validation_mixin import (
    MotionActionErrorData,
    MotionCreatePayloadValidationMixin,
    MotionErrorType,
    MotionUpdatePayloadValidationMixin,
)
from .update import MotionUpdate


@register_action("motion.import")
class MotionImport(
    BaseImportAction,
    MotionCreatePayloadValidationMixin,
    MotionUpdatePayloadValidationMixin,
):
    """
    Action to import a result from the import_preview.
    """

    model = ImportPreview()
    schema = DefaultSchema(ImportPreview()).get_default_schema(
        additional_required_fields={
            "id": required_id_schema,
            "import": {"type": "boolean"},
        }
    )
    permission = Permissions.Motion.CAN_MANAGE
    skip_archived_meeting_check = True
    import_name = "motion"
    number_lookup: Lookup
    username_lookup: dict[str, list[dict[str, Any]]]
    category_lookup: dict[str, list[dict[str, Any]]]
    tags_lookup: dict[str, list[dict[str, Any]]]
    block_lookup: dict[str, list[dict[str, Any]]]
    _user_ids_to_meeting_user: dict[int, Any]
    _submitter_ids_to_user_id: dict[int, int]

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if not instance["import"]:
            return {}

        instance = super().update_instance(instance)
        meeting_id = self.get_meeting_id(instance)
        self.setup_lookups(meeting_id)

        self.rows = [self.validate_entry(row) for row in self.result["rows"]]

        if self.import_state != ImportState.ERROR:
            create_action_payload: list[dict[str, Any]] = []
            update_action_payload: list[dict[str, Any]] = []
            submitter_create_action_payload: list[dict[str, Any]] = []
            submitter_delete_action_payload: list[dict[str, Any]] = []

            motion_to_submitter_user_ids: dict[int, list[int]] = {}
            old_submitters: dict[int, dict[int, int]] = (
                {}
            )  # {motion_id: {user_id:submitter_id}}
            for row in self.rows:
                payload: dict[str, Any] = row["data"].copy()
                used_list = ["text", "reason", "title", "number"]
                for field in used_list:
                    if field in payload:
                        if type(dvalue := payload[field]) is dict:
                            payload[field] = dvalue["value"]
                self.remove_fields_from_data(
                    payload,
                    ["submitters_verbose", "supporters_verbose", "motion_amendment"],
                )
                if (category := payload.pop("category_name", None)) and category[
                    "info"
                ] == ImportState.DONE:
                    payload["category_id"] = (
                        category["id"] if category.get("id") else None
                    )
                if (block := payload.pop("block", None)) and block[
                    "info"
                ] == ImportState.DONE:
                    payload["block_id"] = block["id"] if block.get("id") else None
                payload["tag_ids"] = self.get_ids_from_object_list(
                    payload.pop("tags", [])
                )
                meeting_users_to_create = [
                    {"user_id": submitter["id"], "meeting_id": meeting_id}
                    for submitter in payload["submitters_username"]
                    if submitter["info"] == ImportState.GENERATED
                    and submitter["id"] not in self._user_ids_to_meeting_user.keys()
                ]
                if len(meeting_users_to_create):
                    meeting_users = cast(
                        list[dict[str, int]],
                        self.execute_other_action(
                            MeetingUserCreate, meeting_users_to_create
                        ),
                    )
                    for i in range(len(meeting_users)):
                        self._user_ids_to_meeting_user[
                            meeting_users_to_create[i]["user_id"]
                        ] = meeting_users[i]
                submitters = self.get_ids_from_object_list(
                    payload.pop("submitters_username")
                )
                supporters = [
                    self._user_ids_to_meeting_user[supporter_id]["id"]
                    for supporter_id in self.get_ids_from_object_list(
                        payload.pop("supporters_username", [])
                    )
                ]
                payload["supporter_meeting_user_ids"] = supporters
                payload.pop("category_prefix", None)
                errors: list[MotionActionErrorData] = []
                if row["state"] == ImportState.NEW:
                    payload.update({"submitter_ids": submitters})
                    create_action_payload.append(payload)
                    errors = self.get_create_payload_integrity_error_message(
                        payload, meeting_id
                    )
                else:
                    id_ = payload["id"]
                    motion_to_submitter_user_ids[id_] = submitters
                    motion = {
                        k: v
                        for k, v in (
                            [
                                motion
                                for motion in self.number_lookup.name_to_ids.get(
                                    payload["number"], []
                                )
                                if motion.get("id")
                            ][0]
                        ).items()
                    }
                    for field in ["category_id", "block_id"]:
                        if payload.get(field) is None:
                            if not motion.get(field):
                                payload.pop(field, None)
                    if len(submitters):
                        motion_submitter_ids: list[int] = (
                            motion.get("submitter_ids", []) or []
                        )
                        matched_submitters = {
                            self._submitter_ids_to_user_id[submitter_id]: submitter_id
                            for submitter_id in motion_submitter_ids
                            if self._submitter_ids_to_user_id.get(submitter_id)
                            in submitters
                        }
                        submitter_create_action_payload.extend(
                            [
                                {
                                    "meeting_user_id": self._user_ids_to_meeting_user[
                                        user_id
                                    ]["id"],
                                    "motion_id": id_,
                                }
                                for user_id in submitters
                                if user_id not in matched_submitters.keys()
                            ]
                        )
                        submitter_delete_action_payload.extend(
                            [
                                {"id": submitter_id}
                                for submitter_id in motion_submitter_ids
                                if submitter_id not in matched_submitters.values()
                            ]
                        )
                        old_submitters[id_] = matched_submitters

                    payload.pop("meeting_id", None)
                    update_action_payload.append(payload)
                    errors = self.get_update_payload_integrity_error_message(
                        payload, meeting_id
                    )
                for err in errors:
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
                    if not (
                        row["data"].get(fieldname)
                        and isinstance(row["data"][fieldname], dict)
                    ):
                        row["data"][fieldname] = {
                            "value": row["data"].get(fieldname, ""),
                            "info": ImportState.ERROR,
                        }
                    else:
                        row["data"][fieldname]["info"] = ImportState.ERROR
                        row["data"][fieldname].pop("id", 0)
                    row["messages"].append("Error: " + err["message"])
                    row["state"] = ImportState.ERROR
                    self.import_state = ImportState.ERROR
            if self.import_state != ImportState.ERROR:
                created_submitters: list[dict[str, int]] = []
                if create_action_payload:
                    self.execute_other_action(MotionCreate, create_action_payload)
                if update_action_payload:
                    self.execute_other_action(MotionUpdate, update_action_payload)
                if len(submitter_create_action_payload):
                    created_submitters = cast(
                        list[dict[str, int]],
                        self.execute_other_action(
                            MotionSubmitterCreateAction, submitter_create_action_payload
                        ),
                    )
                if len(submitter_delete_action_payload):
                    self.execute_other_action(
                        MotionSubmitterDeleteAction, submitter_delete_action_payload
                    )
                new_submitters: dict[int, dict[int, int]] = (
                    {}
                )  # {motion_id: {meeting_user_id:submitter_id}}
                for i in range(len(created_submitters)):
                    motion_id = submitter_create_action_payload[i]["motion_id"]
                    new_submitters[motion_id] = {
                        **new_submitters.get(motion_id, {}),
                        submitter_create_action_payload[i][
                            "meeting_user_id"
                        ]: created_submitters[i]["id"],
                    }
                sort_payload: list[dict[str, Any]] = []
                for motion_id in motion_to_submitter_user_ids:
                    sorted_motion_submitter_ids: list[int] = []
                    for submitter_user_id in motion_to_submitter_user_ids[motion_id]:
                        meeting_user_id = cast(
                            int, self._user_ids_to_meeting_user[submitter_user_id]["id"]
                        )
                        if (
                            submitter_user_id
                            in old_submitters.get(motion_id, {}).keys()
                        ):
                            sorted_motion_submitter_ids.append(
                                old_submitters[motion_id][submitter_user_id]
                            )
                        elif (
                            meeting_user_id in new_submitters.get(motion_id, {}).keys()
                        ):
                            sorted_motion_submitter_ids.append(
                                new_submitters[motion_id][meeting_user_id]
                            )
                        else:
                            raise Exception(
                                f"Submitter sorting failed due to submitter for user/{submitter_user_id} not being found"
                            )
                    if len(sorted_motion_submitter_ids):
                        sort_payload.append(
                            {
                                "motion_id": motion_id,
                                "motion_submitter_ids": sorted_motion_submitter_ids,
                            }
                        )
                for payload in sort_payload:
                    self.execute_other_action(MotionSubmitterSort, [payload])

        return {}

    def get_ids_from_object_list(self, object_list: list[dict[str, Any]]) -> list[int]:
        return [
            obj["id"]
            for obj in object_list
            if obj.get("info") != ImportState.WARNING
            and obj.get("info") != ImportState.ERROR
        ]

    def remove_fields_from_data(
        self, data: dict[str, Any], fieldnames: list[str]
    ) -> None:
        for fieldname in fieldnames:
            data.pop(fieldname, None)

    def validate_entry(self, row: ImportRow) -> ImportRow:
        entry = row["data"]

        number = self.get_value_from_union_str_object(entry.get("number"))
        if number:
            check_result = self.number_lookup.check_duplicate(number)
            id_ = cast(int, self.number_lookup.get_field_by_name(number, "id"))

            if check_result == ResultType.FOUND_ID and id_ != 0:
                if row["state"] != ImportState.DONE:
                    row["messages"].append(
                        f"Error: Row state expected to be '{ImportState.DONE}', but it is '{row['state']}'."
                    )
                    row["state"] = ImportState.ERROR
                    entry["number"]["info"] = ImportState.ERROR
                elif "id" not in entry:
                    raise ActionException(
                        f"Invalid JsonUpload data: A data row with state '{ImportState.DONE}' must have an 'id'"
                    )
                elif entry["id"] != id_:
                    row["state"] = ImportState.ERROR
                    entry["number"]["info"] = ImportState.ERROR
                    row["messages"].append(
                        f"Error: Number '{number}' found in different id ({id_} instead of {entry['id']})"
                    )
            elif check_result == ResultType.FOUND_MORE_IDS:
                row["state"] = ImportState.ERROR
                entry["number"]["info"] = ImportState.ERROR
                row["messages"].append(
                    f"Error: Number '{number}' is duplicated in import."
                )
            elif check_result == ResultType.NOT_FOUND_ANYMORE:
                row["messages"].append(
                    f"Error: Motion {entry['number']['id']} not found anymore for updating motion '{number}'."
                )
                row["state"] = ImportState.ERROR

        category_name = self.get_value_from_union_str_object(entry.get("category_name"))
        if category_name and entry["category_name"].get("info") == ImportState.DONE:
            category_prefix = entry.get("category_prefix") or None
            if "id" not in entry["category_name"]:
                raise ActionException(
                    f"Invalid JsonUpload data: A category_name entry with state '{ImportState.DONE}' must have an 'id'"
                )
            categories = self.category_lookup.get(category_name, [])
            categories = [
                category
                for category in categories
                if category.get("prefix") == category_prefix
            ]
            if len(categories) > 0:
                if not any(
                    [
                        category.get("id") == entry["category_name"].get("id")
                        for category in categories
                    ]
                ):
                    row["messages"].append(
                        "Error: Category search didn't deliver the same result as in the preview"
                    )
                    entry["category_name"] = {
                        "value": category_name,
                        "info": ImportState.ERROR,
                    }
                    row["state"] = ImportState.ERROR
            else:
                entry["category_name"] = {
                    "value": category_name,
                    "info": ImportState.ERROR,
                }
                row["state"] = ImportState.ERROR
                row["messages"].append("Error: Category could not be found anymore")

        block = self.get_value_from_union_str_object(entry.get("block"))
        if block and entry["block"].get("info") == ImportState.DONE:
            if "id" not in entry["block"]:
                raise ActionException(
                    f"Invalid JsonUpload data: A block entry with state '{ImportState.DONE}' must have an 'id'"
                )
            found_blocks = self.block_lookup.get(block, [])
            if len(found_blocks) > 0:
                if not any(
                    [block.get("id") == entry["block"]["id"] for block in found_blocks]
                ):
                    entry["block"] = {"value": block, "info": ImportState.ERROR}
                    row["messages"].append(
                        "Error: Motion block search didn't deliver the same result as in the preview"
                    )
                    row["state"] = ImportState.ERROR
            else:
                entry["block"] = {
                    "value": block,
                    "info": ImportState.ERROR,
                }
                row["messages"].append("Error: Couldn't find motion block anymore")
                row["state"] = ImportState.ERROR

        if isinstance(entry.get("tags"), list):
            different: list[str] = []
            not_found: list[str] = []
            for tag_entry in entry.get("tags", []):
                tag = self.get_value_from_union_str_object(tag_entry)
                if tag and tag_entry.get("info") == ImportState.DONE:
                    if "id" not in tag_entry:
                        raise ActionException(
                            f"Invalid JsonUpload data: A tag entry with state '{ImportState.DONE}' must have an 'id'"
                        )
                    found_tags = self.tags_lookup.get(tag, [])
                    if len(found_tags) > 0:
                        if not any(
                            [tag.get("id") == tag_entry["id"] for tag in found_tags]
                        ):
                            tag_entry["info"] = ImportState.ERROR
                            tag_entry.pop("id")
                            different.append(tag)
                    else:
                        tag_entry["info"] = ImportState.ERROR
                        tag_entry.pop("id")
                        not_found.append(tag)
            if len(different):
                row["messages"].append(
                    "Error: Tag search didn't deliver the same result as in the preview: "
                    + ", ".join(different)
                )
                row["state"] = ImportState.ERROR
            if len(not_found):
                row["messages"].append(
                    "Error: Couldn't find tag anymore: " + ", ".join(not_found)
                )
                row["state"] = ImportState.ERROR

        for fieldname in ["submitter", "supporter"]:
            if isinstance(entry.get(f"{fieldname}s_username"), list):
                different = []
                not_found = []
                for user_entry in entry.get(f"{fieldname}s_username", []):
                    user = self.get_value_from_union_str_object(user_entry)
                    if user and (
                        user_entry.get("info") == ImportState.DONE
                        or user_entry.get("info") == ImportState.GENERATED
                    ):
                        if "id" not in user_entry:
                            raise ActionException(
                                f"Invalid JsonUpload data: A {fieldname} entry with state '{ImportState.DONE}' or '{ImportState.GENERATED}' must have an 'id'"
                            )
                        found_users = self.username_lookup.get(user, [])
                        if len(found_users) == 1:
                            if found_users[0].get("id") != user_entry["id"]:
                                user_entry["info"] = ImportState.ERROR
                                user_entry.pop("id")
                                different.append(user)
                        elif len(found_users) > 1:
                            raise ActionException(
                                f"Database corrupt: Found multiple users with the username {user}."
                            )
                        else:
                            user_entry["info"] = ImportState.ERROR
                            user_entry.pop("id")
                            not_found.append(user)
                if len(different):
                    row["messages"].append(
                        f"Error: {fieldname[0].capitalize() + fieldname[1:]} search didn't deliver the same result as in the preview: "
                        + ", ".join(different)
                    )
                    row["state"] = ImportState.ERROR
                if len(not_found):
                    row["messages"].append(
                        f"Error: Couldn't find {fieldname} anymore: "
                        + ", ".join(not_found)
                    )
                    row["state"] = ImportState.ERROR

        row["messages"] = list(set(row["messages"]))

        if row["state"] == ImportState.ERROR and self.import_state == ImportState.DONE:
            self.import_state = ImportState.ERROR
        return {
            "state": row["state"],
            "data": row["data"],
            "messages": row.get("messages", []),
        }

    def setup_lookups(self, meeting_id: int) -> None:
        rows = self.result["rows"]
        self.number_lookup = Lookup(
            self.datastore,
            "motion",
            [
                (entry["number"]["value"], entry)
                for row in rows
                if "number" in (entry := row["data"])
                and entry["number"].get("info") != ImportState.WARNING
            ],
            field="number",
            mapped_fields=["submitter_ids", "category_id", "block_id"],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
        self.block_lookup = self.get_lookup_dict(
            "motion_block",
            [
                entry["block"]["value"]
                for row in rows
                if "block" in (entry := row["data"])
                and entry["block"].get("info") != ImportState.WARNING
            ],
            "title",
            and_filters=[FilterOperator("meeting_id", "=", meeting_id)],
        )
        self.category_lookup = self.get_lookup_dict(
            "motion_category",
            [
                entry["category_name"]["value"]
                for row in rows
                if "category_name" in (entry := row["data"])
                and entry["category_name"].get("info") != ImportState.WARNING
            ],
            "name",
            ["prefix"],
            and_filters=[FilterOperator("meeting_id", "=", meeting_id)],
        )

        self.username_lookup = self.get_lookup_dict(
            "user",
            list(
                {
                    user["value"]
                    for row in rows
                    if (
                        users := [
                            *row["data"].get("submitters_username", []),
                            *row["data"].get("supporters_username", []),
                        ]
                    )
                    for user in users
                    if user and user.get("info") != ImportState.WARNING
                }
            ),
            "username",
            ["meeting_ids", "meeting_user_ids"],
        )
        self.username_lookup = {
            username: [
                date
                for date in self.username_lookup[username]
                if (
                    date.get("meeting_ids")
                    and (meeting_id in date["meeting_ids"])
                    or date.get("id") == self.user_id
                )
            ]
            for username in self.username_lookup
        }
        all_user_ids = list(
            [
                submitter["id"]
                for submitters in self.username_lookup.values()
                for submitter in submitters
            ]
        )
        all_meeting_users: dict[int, dict[str, Any]] = {}
        if len(all_user_ids):
            all_meeting_users = self.datastore.filter(
                "meeting_user",
                And(
                    FilterOperator("meeting_id", "=", meeting_id),
                    Or(
                        *[
                            FilterOperator("user_id", "=", user_id)
                            for user_id in all_user_ids
                        ]
                    ),
                ),
                [
                    "id",
                    "user_id",
                    "motion_submitter_ids",
                    "supported_motion_ids",
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
        self._submitter_ids_to_user_id = {
            submitter_id: all_meeting_users[meeting_user_id]["user_id"]
            for meeting_user_id in all_meeting_users
            for submitter_id in (
                all_meeting_users[meeting_user_id].get("motion_submitter_ids", []) or []
            )
            if all_meeting_users[meeting_user_id].get("user_id")
        }
        self.tags_lookup = self.get_lookup_dict(
            "tag",
            [
                tag["value"]
                for row in rows
                if "tags" in (entry := row["data"])
                for tag in entry["tags"]
                if tag.get("info") != ImportState.WARNING
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
        lookup: dict[str, list[dict[str, Any]]] = {}
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
            for date_id in data:
                date = data[date_id]
                lookup[date[fieldname]] = [
                    *lookup.get(date[fieldname], []),
                    date,
                ]
        return lookup

    def get_meeting_id(self, instance: dict[str, Any]) -> int:
        store_id = instance["id"]
        worker = self.datastore.get(
            fqid_from_collection_and_id("import_preview", store_id),
            ["name", "result"],
            lock_result=False,
        )
        if worker.get("name") == self.import_name:
            return next(iter(worker.get("result", {})["rows"]))["data"]["meeting_id"]
        raise ActionException("Import data cannot be found.")
