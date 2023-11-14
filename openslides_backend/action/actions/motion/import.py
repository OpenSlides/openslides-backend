from typing import Any, Dict, List, cast

from openslides_backend.action.mixins.import_mixins import (
    ImportMixin,
    ImportRow,
    ImportState,
    Lookup,
    ResultType,
)
from openslides_backend.action.util.register import register_action
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.filters import And, FilterOperator, Or

from ....models.models import ImportPreview
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...util.default_schema import DefaultSchema
from .create import MotionCreate
from .update import MotionUpdate


@register_action("motion.import")
class AccountImport(ImportMixin):
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
    submitter_lookup: Lookup
    supporter_lookup: Lookup
    category_lookup: Lookup
    tags_lookup: Lookup
    block_lookup: Lookup

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if not instance["import"]:
            return {}

        instance = super().update_instance(instance)
        meeting_id = self.get_meeting_id(instance)
        self.setup_lookups(meeting_id)

        self.rows = [self.validate_entry(row) for row in self.result["rows"]]

        # TODO also with motion_submitter.create and -delete
        if self.import_state != ImportState.ERROR:
            create_action_payload: List[Dict[str, Any]] = []
            update_action_payload: List[Dict[str, Any]] = []
            self.flatten_object_fields(["text", "reason", "title", "number"])
            for row in self.rows:
                if row["state"] == ImportState.NEW:
                    create_action_payload.append(row["data"])
                else:
                    # TODO: Split off submitter and handle it separately
                    update_action_payload.append(row["data"])
            if create_action_payload:
                self.execute_other_action(MotionCreate, create_action_payload)
            if update_action_payload:
                self.execute_other_action(MotionUpdate, update_action_payload)

        return {}

    def validate_entry(self, row: ImportRow) -> ImportRow:
        entry = row["data"]

        number = self.get_value_from_union_str_object(entry.get("number"))
        if number:
            check_result = self.number_lookup.check_duplicate(number)
            id_ = cast(int, self.number_lookup.get_field_by_name(number, "id"))

            if check_result == ResultType.FOUND_ID and id_ != 0:
                if row["state"] != ImportState.DONE:
                    row["messages"].append(
                        f"Error: row state expected to be '{ImportState.DONE}', but it is '{row['state']}'."
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
                        f"Error: number '{number}' found in different id ({id_} instead of {entry['id']})"
                    )
            elif check_result == ResultType.FOUND_MORE_IDS:
                row["state"] = ImportState.ERROR
                entry["number"]["info"] = ImportState.ERROR
                row["messages"].append(
                    f"Error: number '{number}' is duplicated in import."
                )
            elif check_result == ResultType.NOT_FOUND_ANYMORE:
                row["messages"].append(
                    f"Error: motion {entry['number']['id']} not found anymore for updating motion '{number}'."
                )
                row["state"] = ImportState.ERROR

        category_name = self.get_value_from_union_str_object(entry.get("category_name"))
        if category_name and entry["category_name"].get("info") == ImportState.DONE:
            categories = self.category_lookup.name_to_ids[category_name]
            if category_prefix := self.get_value_from_union_str_object(
                entry.get("category_name")
            ):
                categories = [
                    category
                    for category in categories
                    if category.get("prefix") == category_prefix and category.get("id")
                ]
            if len(categories) == 1:
                category = categories[0]
                if category.get("id") != entry["category_name"].get("id"):
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
            check_result = self.block_lookup.check_duplicate(block)
            # TODO
            block_id = cast(int, self.block_lookup.get_field_by_name(block, "id"))
            if check_result == ResultType.FOUND_ID and block_id != 0:
                if block_id != entry["block"]["id"]:
                    entry["block"] = {"value": block, "info": ImportState.ERROR}
                    row["messages"].append(
                        "Error: Motion block search didn't deliver the same result as in the preview"
                    )
            elif (
                check_result == ResultType.NOT_FOUND
                or check_result == ResultType.NOT_FOUND_ANYMORE
                or block_id == 0
            ):
                entry["block"] = {
                    "value": block,
                    "info": ImportState.ERROR,
                }
                row["messages"].append("Error: Couldn't find motion block anymore")
            elif check_result == ResultType.FOUND_MORE_IDS:
                entry["block"] = {
                    "value": block,
                    "info": ImportState.ERROR,
                }
                row["messages"].append(
                    "Error: Found multiple motion blocks with the same name"
                )

        # TODO tags and usernames validation

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
            mapped_fields=["submitter_ids"],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
        self.block_lookup = Lookup(
            self.datastore,
            "motion_block",
            [
                (entry["block"]["value"], entry)
                for row in rows
                if "block" in (entry := row["data"])
                and entry["block"].get("info") != ImportState.WARNING
            ],
            collection_field="title",
            field="block",
            mapped_fields=[],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )
        self.category_lookup = Lookup(
            self.datastore,
            "motion_category",
            [
                (entry["category_name"]["value"], entry)
                for row in rows
                if "category_name" in (entry := row["data"])
                and entry["category_name"].get("info") != ImportState.WARNING
            ],
            field="category_name",
            collection_field="name",
            mapped_fields=["prefix"],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )

        self.submitter_lookup = Lookup(
            self.datastore,
            "user",
            [
                (user["value"], entry)
                for row in rows
                if "submitters_username" in (entry := row["data"])
                for user in entry["submitters_username"]
                if user.get("info") != ImportState.WARNING
            ],
            field="submitters_username",
            collection_field="username",
            mapped_fields=["meeting_user_ids"],
        )
        self.supporter_lookup = Lookup(
            self.datastore,
            "user",
            [
                (user["value"], entry)
                for row in rows
                if "supporters_username" in (entry := row["data"])
                for user in entry["supporters_username"]
                if user.get("info") != ImportState.WARNING
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
        self._supporter_ids_to_user_id = {
            supporter_id: all_meeting_users[meeting_user_id]["user_id"]
            for meeting_user_id in all_meeting_users
            for supporter_id in all_meeting_users[meeting_user_id].get(
                "motion_supporter_ids", []
            )
            if all_meeting_users[meeting_user_id].get("user_id")
        }
        self.tags_lookup = Lookup(
            self.datastore,
            "tag",
            [
                (tag["value"], entry)
                for row in rows
                if "tags" in (entry := row["data"])
                for tag in entry["tags"]
                if tag.get("info") != ImportState.WARNING
            ],
            field="tags",
            collection_field="name",
            mapped_fields=[],
            global_and_filter=FilterOperator("meeting_id", "=", meeting_id),
        )

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        store_id = instance["id"]
        worker = self.datastore.get(
            fqid_from_collection_and_id("import_preview", store_id),
            ["name", "result"],
            lock_result=False,
        )
        if worker.get("name") == self.import_name:
            return next(iter(worker.get("result", {})["rows"]))["data"]["meeting_id"]
        raise ActionException("Import data cannot be found.")
