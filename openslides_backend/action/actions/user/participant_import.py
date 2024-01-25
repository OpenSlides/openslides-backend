from typing import Any, Dict, List, Optional, Set, Tuple, cast

from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator, Or
from ...mixins.import_mixins import ImportRow, ImportState
from ...util.register import register_action
from ...util.typing import ActionData
from ..structure_level.create import StructureLevelCreateAction
from .base_import import BaseUserImport
from .participant_common import ParticipantCommon
from .set_present import UserSetPresentAction


@register_action("participant.import")
class ParticipantImport(BaseUserImport, ParticipantCommon):
    import_name = "participant"
    lookups: Dict[str, Dict[int, str]] = {}
    structure_level_to_create_list: List[str] = []
    newly_found_structure_levels: Dict[int, Dict[str, Any]] = {}

    def prefetch(self, action_data: ActionData) -> None:
        super().prefetch(action_data)
        self.meeting_id = cast(int, self.result["meeting_id"])

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        structure_levels_to_create: Set[str] = set(
            [
                level["value"]
                for row in self.rows
                for level in row["data"].get("structure_level", [])
                if level.get("info") == ImportState.NEW
            ]
        )
        if len(structure_levels_to_create):
            self.newly_found_structure_levels = self.datastore.filter(
                "structure_level",
                Or(
                    [
                        FilterOperator("name", "=", level)
                        for level in structure_levels_to_create
                    ]
                ),
                ["name", "id"],
            )
            for level in self.newly_found_structure_levels.values():
                structure_levels_to_create.discard(level["name"])
            self.structure_level_to_create_list = list(structure_levels_to_create)
        instance = super().update_instance(instance)
        return instance

    def handle_create_relations(self, instance: Dict[str, Any]) -> None:
        if self.import_state != ImportState.ERROR and (
            len(self.structure_level_to_create_list)
            or len(self.newly_found_structure_levels)
        ):
            newly_found_levels_dict: Dict[str, int] = {
                model["name"]: id_
                for id_, model in self.newly_found_structure_levels.items()
            }
            if (
                created_levels := (
                    self.execute_other_action(
                        StructureLevelCreateAction,
                        [
                            {"name": name, "meeting_id": self.meeting_id}
                            for name in self.structure_level_to_create_list
                        ],
                    )
                    if len(self.structure_level_to_create_list)
                    else []
                )
            ) is not None:
                levels_dict = (
                    dict(zip(self.structure_level_to_create_list, created_levels))
                    if len(created_levels)
                    else {}
                )
                for row in self.rows:
                    for level in row["data"].get("structure_level", []):
                        if level.get("info") == ImportState.NEW:
                            if structure_level := levels_dict.get(level["value"]):
                                level["id"] = structure_level["id"]
                            elif structure_level_id := newly_found_levels_dict.get(
                                level["value"]
                            ):
                                level["id"] = structure_level_id
                                level["info"] = ImportState.DONE
                            else:
                                raise ActionException(
                                    "Couldn't correctly create new structure_levels"
                                )
            else:
                raise ActionException("Couldn't correctly create new structure_levels")
        # elif len(self.newly_found_structure_levels):
        #     # levels_set = set(
        #     #     [model["name"] for model in self.newly_found_structure_levels.values()]
        #     # )
        #     for row in self.rows:
        #         error_levels: List[str] = []
        #         for level in row["data"].get("structure_level", []):
        #             if level.get("info") == ImportState.NEW:
        #                 if level["value"] in newly_found_levels_dict:
        #                     level["info"] = ImportState.ERROR
        #                     error_levels.append(level["value"])
        #                     row["state"] = ImportState.ERROR
        #                     self.import_state = ImportState.ERROR
        #         if len(error_levels):
        #             row["messages"].append(
        #                 f"Error: Failed to create the following structure levels as they were already created: {', '.join(error_levels)}"
        #             )

    def validate_entry(self, row: ImportRow) -> ImportRow:
        row = super().validate_entry(row)
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
                    if not (instance_id := instance.get("id")):
                        continue
                    if instance_id in self.lookups[field]:
                        if self.lookups[field][instance_id] == instance["value"]:
                            valid = True
                        else:
                            instance["info"] = ImportState.WARNING
                            row["messages"].append(
                                f"The {singular_field} '{instance_id} {instance['value']}' changed its name to '{self.lookups[field][instance_id]}'."
                            )
                    elif instance["info"] == ImportState.NEW and instance.get("id"):
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

        entry.pop("meeting_id")
        if row["state"] == ImportState.ERROR and self.import_state == ImportState.DONE:
            self.import_state = ImportState.ERROR
        return row

    def create_other_actions(self, rows: List[ImportRow]) -> List[Optional[int]]:
        set_present_payload: List[Dict[str, Any]] = []
        indices_to_set_presence_and_id: List[Optional[Tuple[bool, Optional[int]]]] = []
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
                            set(
                                id
                                for row in self.rows
                                for instance in row["data"].get(field, [])
                                if (id := instance.get("id"))
                            )
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
