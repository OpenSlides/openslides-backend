from typing import Any, cast

from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator, Or
from ...mixins.import_mixins import ImportRow, ImportState
from ...util.register import register_action
from ...util.typing import ActionData
from ..group.create import GroupCreate
from ..structure_level.create import StructureLevelCreateAction
from .base_import import BaseUserImport
from .participant_common import ParticipantCommon
from .set_present import UserSetPresentAction


@register_action("participant.import")
class ParticipantImport(BaseUserImport, ParticipantCommon):
    import_name = "participant"
    lookups: dict[str, dict[int, str]] = {}
    models_to_create: dict[str, list[str]] = {}
    newly_found_models: dict[str, dict[int, dict[str, Any]]] = {}

    def prefetch(self, action_data: ActionData) -> None:
        super().prefetch(action_data)
        self.meeting_id = cast(int, self.result["meeting_id"])

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.update_models_to_create("group", "groups")
        self.update_models_to_create("structure_level", "structure_level")
        instance = super().update_instance(instance)
        return instance

    def check_all_rows(self) -> None:
        if (
            not self.check_meeting_admin_integrity(self.meeting_id, self.rows)
        ) and self.import_state == ImportState.DONE:
            self.import_state = ImportState.ERROR

    def update_models_to_create(self, model_name: str, field_name: str) -> None:
        self.models_to_create[field_name] = []
        to_create: set[str] = {
            entry["value"]
            for row in self.rows
            for entry in row["data"].get(field_name, [])
            if entry.get("info") == ImportState.NEW
        }
        if len(to_create):
            self.newly_found_models[field_name] = self.datastore.filter(
                model_name,
                And(
                    FilterOperator("meeting_id", "=", self.meeting_id),
                    *(
                        [FilterOperator("anonymous_group_for_meeting_id", "=", None)]
                        if model_name == "group"
                        else []
                    ),
                    Or([FilterOperator("name", "=", name) for name in to_create]),
                ),
                ["name", "id"],
            )
            for model in self.newly_found_models[field_name].values():
                to_create.discard(model["name"])
            self.models_to_create[field_name] = list(to_create)

    def handle_create_relations(self, instance: dict[str, Any]) -> None:
        if self.import_state != ImportState.ERROR:
            for field in ["structure_level", "groups"]:
                singular_field = field.rstrip("s")
                if len(self.models_to_create.get(field, [])) or len(
                    self.newly_found_models.get(field, {})
                ):
                    newly_found_models_dict: dict[str, int] = {
                        model["name"]: id_
                        for id_, model in self.newly_found_models[field].items()
                    }
                    created_models = (
                        self.execute_other_action(
                            (
                                StructureLevelCreateAction
                                if field == "structure_level"
                                else GroupCreate
                            ),
                            [
                                {"name": name, "meeting_id": self.meeting_id}
                                for name in self.models_to_create[field]
                            ],
                        )
                        if len(self.models_to_create.get(field, []))
                        else None
                    )
                    if created_models or not len(self.models_to_create.get(field, [])):
                        models_dict = dict(
                            zip(
                                self.models_to_create.get(field, []),
                                created_models or [],
                            )
                        )
                        for row in self.rows:
                            for model in row["data"].get(field, []):
                                if model.get("info") == ImportState.NEW:
                                    if created_model := models_dict.get(model["value"]):
                                        model["id"] = created_model["id"]
                                    elif model_id := newly_found_models_dict.get(
                                        model["value"]
                                    ):
                                        model["id"] = model_id
                                        model["info"] = ImportState.DONE
                                    else:
                                        raise ActionException(
                                            f"Couldn't correctly create new {singular_field}s"
                                        )
                    else:
                        raise ActionException(
                            f"Couldn't correctly create new {singular_field}s"
                        )

    def validate_entry(self, row: ImportRow) -> None:
        super().validate_entry(row)
        entry = row["data"]
        entry["meeting_id"] = self.meeting_id
        if "groups" not in entry:
            raise ActionException(
                f"There is no group in the data of user '{self.get_value_from_union_str_object(entry.get('username'))}'. Is there a default group for the meeting?"
            )
        groups = entry.pop("groups", None)
        structure_levels = entry.pop("structure_level", None)
        entry["group_ids"] = [
            group_id for group in groups if (group_id := group.get("id"))
        ]
        if structure_levels:
            entry["structure_level_ids"] = [
                structure_level_id
                for structure_level in structure_levels
                if (structure_level_id := structure_level.get("id"))
            ]

        failing_fields = self.permission_check.get_failing_fields(entry)
        failing_fields_jsonupload = {
            field
            for field in entry
            if isinstance(entry[field], dict)
            and entry[field]["info"] == ImportState.REMOVE
        }
        if less_ff := list(failing_fields_jsonupload - set(failing_fields)):
            less_ff.sort()
            row["messages"].append(
                f"In contrast to preview you may import field(s) '{', '.join(less_ff)}'"
            )
            for field in less_ff:
                entry[field]["info"] = ImportState.DONE
        if more_ff := list(set(failing_fields) - failing_fields_jsonupload):
            more_ff.sort()
            row["messages"].append(
                f"Error: In contrast to preview you may not import field(s) '{', '.join(more_ff)}'"
            )
            row["state"] = ImportState.ERROR
            for field in more_ff:
                entry[field]["info"] = ImportState.ERROR
        entry.pop("group_ids")
        entry.pop("structure_level_ids", None)
        entry["groups"] = groups
        if structure_levels:
            entry["structure_level"] = structure_levels

        for field in ("groups", "structure_level"):
            valid = False
            if field in entry:
                singular_field = field.rstrip("s")
                for instance in (instances := entry[field]):
                    if (instance_id := instance.get("id")) in self.lookups[field]:
                        if self.lookups[field][instance_id] == instance["value"]:
                            valid = True
                        else:
                            instance["info"] = ImportState.WARNING
                            row["messages"].append(
                                f"The {singular_field} '{instance_id} {instance['value']}' changed its name to '{self.lookups[field][instance_id]}'."
                            )
                    elif instance["info"] == ImportState.NEW:
                        valid = True
                    else:
                        instance["info"] = ImportState.WARNING
                        row["messages"].append(
                            f"The {singular_field} '{instance_id} {instance['value']}' doesn't exist anymore."
                        )
            if field == "groups" and not valid:
                row["messages"].append(
                    "Error in groups: No valid group found inside the pre-checked groups from import, see warnings."
                )
                row["state"] = ImportState.ERROR
                instances[0]["info"] = ImportState.ERROR

        self.validate_locked_out_status(
            entry, row["messages"], entry.get("groups", []), row
        )

        entry.pop("meeting_id")
        if row["state"] == ImportState.ERROR and self.import_state == ImportState.DONE:
            self.import_state = ImportState.ERROR

    def create_other_actions(self, rows: list[ImportRow]) -> list[int | None]:
        set_present_payload: list[dict[str, Any]] = []
        indices_to_set_presence_and_id: list[tuple[bool, int | None] | None] = []
        for row in rows:
            if (present := row["data"].get("is_present")) is not None:
                indices_to_set_presence_and_id.append((present, row["data"].get("id")))
                row["data"].pop("is_present")
            else:
                indices_to_set_presence_and_id.append(None)
            row["data"]["meeting_id"] = self.meeting_id

        ids = super().create_other_actions(rows)
        for i in range(len(indices_to_set_presence_and_id)):
            if (tup := indices_to_set_presence_and_id[i]) is not None:
                present, id_ = tup
                set_present_payload.append(
                    {
                        "id": id_ or ids[i],
                        "meeting_id": self.meeting_id,
                        "present": present,
                    }
                )
        if set_present_payload:
            self.execute_other_action(UserSetPresentAction, set_present_payload)
        return ids

    def setup_lookups(self) -> None:
        super().setup_lookups()
        for field in ("groups", "structure_level"):
            singular_field = field.rstrip("s")
            result = self.datastore.get_many(
                [
                    GetManyRequest(
                        singular_field,
                        list(
                            {
                                id
                                for row in self.rows
                                for instance in row["data"].get(field, [])
                                if (id := instance.get("id"))
                            }
                        ),
                        ["name"],
                    )
                ],
                lock_result=False,
                use_changed_models=False,
            )
            self.lookups[field] = {
                k: v["name"] for k, v in result.get(singular_field, {}).items()
            }
