import re
from collections import defaultdict
from collections.abc import Generator, Iterable
from typing import Any, cast

import fastjsonschema

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator, Or
from ....shared.interfaces.event import Event
from ....shared.schema import schema_version
from ....shared.typing import Schema
from ...mixins.meeting_user_helper import get_meeting_user
from ...mixins.send_email_mixin import EmailCheckMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.action_type import ActionType
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement
from ..gender.create import GenderCreate
from ..structure_level.create import StructureLevelCreateAction
from .create import UserCreate
from .update import UserUpdate
from .user_mixins import UsernameMixin

allowed_user_fields = [
    "saml_id",
    "title",
    "first_name",
    "last_name",
    "email",
    "gender",
    "pronoun",
    "is_active",
    "is_physical_person",
    "member_number",
]

allowed_meeting_user_fields = [
    "groups",
    "structure_levels",
    "number",
    "comment",
    "vote_weight",
    "present",
]


@register_action("user.save_saml_account", action_type=ActionType.STACK_INTERNAL)
class UserSaveSamlAccount(
    EmailCheckMixin,
    UsernameMixin,
    SingularActionMixin,
):
    """
    Internal action to save (create or update) a saml account.
    It should be called from the auth service.
    """

    user: dict[str, Any] = {}
    saml_attr_mapping: dict[str, str]
    check_email_field = "email"
    model = User()
    schema: Schema = {}
    skip_archived_meeting_check = True

    def validate_instance(self, instance: dict[str, Any]) -> None:
        organization = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["saml_enabled", "saml_attr_mapping"],
            lock_result=False,
        )
        if not organization.get("saml_enabled"):
            raise ActionException(
                "SingleSignOn is not enabled in OpenSlides configuration"
            )
        self.saml_attr_mapping: dict[str, Any] = organization.get(
            "saml_attr_mapping", dict()
        )
        if not self.saml_attr_mapping or not isinstance(self.saml_attr_mapping, dict):
            raise ActionException(
                "SingleSignOn field attributes are not configured in OpenSlides"
            )
        self.schema = {
            "$schema": schema_version,
            "title": "create saml account schema",
            "type": "object",
            "properties": {
                payload_field: {
                    "oneOf": [
                        (type_def := self.model.get_field(model_field).get_schema()),
                        {
                            "type": "array",
                            "items": type_def,
                            "minItems": 1 if model_field == "saml_id" else 0,
                        },
                    ]
                }
                for model_field, payload_field in self.saml_attr_mapping.items()
                # handle only allowed fields. handle gender separately since it needs conversion to id
                if model_field in allowed_user_fields and model_field != "gender"
            },
            "required": [self.saml_attr_mapping["saml_id"]],
            "additionalProperties": True,
        }
        self.schema["properties"].update(
            {
                "gender": {
                    "oneOf": [
                        {"type": ["string", "null"], "maxLength": 256},
                        {
                            "type": "array",
                            "items": {"type": ["string", "null"], "maxLength": 256},
                            "minItems": 0,
                        },
                    ]
                },
            }
        )
        try:
            fastjsonschema.validate(self.schema, instance)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)

    def validate_fields(self, instance_old: dict[str, Any]) -> dict[str, Any]:
        """
        Transforms the payload fields into model fields, removes the possible array-wrapped format.
        Mapper data is comprised on a per meeting basis. On conflicts the last statement is used.
        Groups and structure levels are combined, however.
        Meeting related data will be transformed via the idp attributes to the actual model data.
        """
        instance: dict[str, Any] = dict()
        for model_field, payload_field in self.saml_attr_mapping.items():
            if (
                isinstance(payload_field, str)
                and payload_field in instance_old
                and model_field in allowed_user_fields
            ):
                idp_attribute = (
                    tx[0]
                    if isinstance((tx := instance_old[payload_field]), list) and len(tx)
                    else tx
                )
                if idp_attribute not in (None, []):
                    instance[model_field] = idp_attribute
        self.apply_meeting_mapping(instance, instance_old)
        return super().validate_fields(instance)

    def prepare_action_data(self, action_data: ActionData) -> ActionData:
        """Necessary to prevent id reservation in CreateAction's prepare_action_data"""
        return action_data

    def check_permissions(self, instance: dict[str, Any]) -> None:
        pass

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        users = self.datastore.filter(
            "user",
            FilterOperator("saml_id", "=", instance["saml_id"]),
            [
                "id",
                "meeting_user_ids",
                "is_present_in_meeting_ids",
                "gender_id",
                *allowed_user_fields,
            ],
        )
        if gender := instance.pop("gender", None):
            gender_dict = self.datastore.filter(
                "gender",
                FilterOperator("name", "=", gender),
                ["id"],
            )
            gender_id = None
            if gender_dict:
                gender_id = next(iter(gender_dict.keys()))
            else:
                action_result = self.execute_other_action(
                    GenderCreate, [{"name": gender}]
                )
                if action_result and action_result[0]:
                    gender_id = action_result[0].get("id", 0)
            if gender_id:
                instance["gender_id"] = gender_id
            else:
                self.logger.warning(
                    f"save_saml_account could neither find nor create {gender}. Not handling gender."
                )
        # Empty string: remove gender_id
        elif gender == "":
            instance["gender_id"] = None
        meeting_users: dict[int, dict[str, Any]] | None = dict()
        user_id = None
        if len(users) == 1:
            self.user = next(iter(users.values()))
            instance["id"] = (user_id := cast(int, self.user["id"]))
            meeting_users = self.apply_meeting_user_data(instance, user_id, True)
            if meeting_users:
                self.update_meeting_users_from_db(meeting_users, user_id)
            instance = {
                k: v for k, v in instance.items() if k == "id" or v != self.user.get(k)
            }
            if len(instance) > 1:
                self.execute_other_action(UserUpdate, [instance])
        elif len(users) == 0:
            instance = self.set_defaults(instance)
            meeting_users = instance.pop("meeting_user_data", None)
            response = self.execute_other_action(UserCreate, [instance])
            if response and response[0]:
                user_id = response[0].get("id")
            instance["meeting_user_data"] = meeting_users
            if user_id:
                meeting_users = self.apply_meeting_user_data(instance, user_id, False)
        else:
            ActionException(
                f"More than one existing user found in database with saml_id {instance['saml_id']}"
            )
        if meeting_users:
            self.execute_other_action(UserUpdate, [mu for mu in meeting_users.values()])
        return instance

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        """
        delegated to execute_other_action
        """
        return []

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        return {"user_id": instance["id"]}

    def set_defaults(self, instance: dict[str, Any]) -> dict[str, Any]:
        if "is_active" not in instance:
            instance["is_active"] = True
        if "is_physical_person" not in instance:
            instance["is_physical_person"] = True
        instance["can_change_own_password"] = False
        instance["username"] = self.generate_usernames([instance.get("saml_id", "")])[0]
        return instance

    def validate_meeting_mapper(
        self, instance: dict[str, Any], meeting_mapper: dict[str, Any]
    ) -> bool:
        """
        Validates the meeting mapper to be complete. Returns False if not.
        Returns True if the mapper matches its criteria on instances values or no conditions were given.
        Instances values can not be None or empty string.
        """
        if not meeting_mapper.get("external_id"):
            return False
        if not (mapper_conditions := meeting_mapper.get("conditions")):
            return True
        return all(
            (
                (instance_value := instance.get(mapper_condition.get("attribute")))
                and regex_condition.search(instance_value)
            )
            for mapper_condition in mapper_conditions
            if (regex_condition := re.compile(mapper_condition.get("condition")))
        )

    def apply_meeting_mapping(
        self, instance: dict[str, Any], instance_old: dict[str, Any]
    ) -> None:
        if meeting_mappers := cast(
            list[dict[str, Any]],
            self.saml_attr_mapping.get("meeting_mappers", []),
        ):
            meeting_user_data: dict[str, Any] = defaultdict(dict)
            for meeting_mapper in meeting_mappers:
                if self.validate_meeting_mapper(instance_old, meeting_mapper):
                    meeting_external_id = cast(str, meeting_mapper["external_id"])
                    mapping_results = meeting_user_data[meeting_external_id]
                    allow_update: str | bool
                    if isinstance(
                        allow_update := cast(
                            str, meeting_mapper.get("allow_update", "True")
                        ),
                        str,
                    ):
                        allow_update = allow_update.casefold() != "False".casefold()
                    result = {
                        **{
                            key: value
                            for key, value in self.get_field_data(
                                instance_old,
                                mapping_results.get("for_create", dict()),
                                meeting_mapper,
                            )
                        },
                    }
                    if allow_update:
                        mapping_results["for_create"] = result
                        mapping_results["for_update"] = {
                            **{
                                key: value
                                for key, value in self.get_field_data(
                                    instance_old,
                                    mapping_results.get("for_update", dict()),
                                    meeting_mapper,
                                )
                            },
                        }
                    else:
                        mapping_results["for_create"] = result
            if meeting_user_data:
                instance["meeting_user_data"] = meeting_user_data
            else:
                self.logger.warning(
                    f"save_saml_account found no matching meeting mappers."
                )

    def apply_meeting_user_data(
        self, instance: dict[str, Any], user_id: int, is_update: bool
    ) -> dict[int, dict[str, Any]] | None:
        if not (meeting_user_data := instance.pop("meeting_user_data", None)) or not (
            external_meeting_ids := sorted(
                [ext_id for ext_id in meeting_user_data.keys()]
            )
        ):
            return None
        meetings = {
            meeting_id: meeting
            for meeting_id, meeting in sorted(
                self.datastore.filter(
                    "meeting",
                    Or(
                        FilterOperator("external_id", "=", external_meeting_id)
                        for external_meeting_id in external_meeting_ids
                    ),
                    ["id", "default_group_id", "external_id"],
                ).items()
            )
        }
        missing_meetings = [
            external_meeting_id
            for external_meeting_id in external_meeting_ids
            if external_meeting_id
            not in {meeting.get("external_id") for meeting in meetings.values()}
        ]
        if missing_meetings:
            self.logger.warning(
                f"save_saml_account found no meetings for {len(missing_meetings)} meetings with external_ids {missing_meetings}"
            )
        # declare and half way through initialize mu data
        result: dict[int, dict[str, Any]] = dict()
        for (
            meeting_id,
            meeting,
        ) in meetings.items():
            if not (
                instance_meeting_user_data := meeting_user_data.get(
                    meeting["external_id"]
                )
            ):
                continue
            if is_update:
                instance_meeting_user = instance_meeting_user_data.get("for_update")
            else:
                instance_meeting_user = instance_meeting_user_data.get("for_create")
            if instance_meeting_user is not None:
                instance_meeting_user["id"] = user_id
                instance_meeting_user["meeting_id"] = meeting_id
                for saml_meeting_user_field in ["groups", "structure_levels"]:
                    names = sorted(
                        instance_meeting_user.pop(saml_meeting_user_field, [])
                    )
                    if saml_meeting_user_field == "groups":
                        ids = self.get_group_ids(names, meeting)
                    elif saml_meeting_user_field == "structure_levels":
                        ids = self.get_structure_level_ids(names, meeting)
                    if ids:
                        instance_meeting_user[
                            f"{saml_meeting_user_field.rstrip('s')}_ids"
                        ] = ids
                if instance_meeting_user.pop("present", ""):
                    present_in_meeting_ids = instance.get(
                        "is_present_in_meeting_ids", []
                    )
                    if meeting_id not in present_in_meeting_ids:
                        present_in_meeting_ids.append(meeting_id)
                    instance["is_present_in_meeting_ids"] = present_in_meeting_ids
                result[meeting_id] = instance_meeting_user
        return result

    def update_meeting_users_from_db(
        self, meeting_users: dict[int, dict[str, Any]], user_id: int
    ) -> None:
        """updates meeting users with groups and structure level relations from database"""
        for meeting_id, meeting_user in meeting_users.items():
            if meeting_user_db := get_meeting_user(
                self.datastore,
                meeting_id,
                user_id,
                ["id", "group_ids", "structure_level_ids"],
            ):
                for field_name in ["group_ids", "structure_level_ids"]:
                    if old_ids := meeting_user_db.get(field_name):
                        ids = meeting_user.get(field_name, [])
                        for _id in ids:
                            if _id not in old_ids:
                                meeting_user[field_name] = old_ids + [_id]

    def get_field_data(
        self,
        instance: dict[str, Any],
        meeting_user: dict[str, Any],
        meeting_mapper: dict[str, dict[str, Any]],
    ) -> Generator[tuple[str, Any]]:
        """
        returns the field data for the given idp mapping field. Groups the groups and structure levels for each meeting.
        Uses mappers for generating default values.
        """
        missing_attributes = []
        for saml_meeting_user_field in allowed_meeting_user_fields:
            result: set[str] | str | bool = ""
            meeting_mapping = meeting_mapper.get("mappings", dict())
            result = meeting_user.get(saml_meeting_user_field, "")
            if saml_meeting_user_field in ["groups", "structure_levels"]:
                attr_default_list = meeting_mapping.get(saml_meeting_user_field, [])
            else:
                attr_default_list = [
                    meeting_mapping.get(saml_meeting_user_field, dict())
                ]
            for attr_default in attr_default_list:
                idp_attribute = attr_default.get("attribute", "")
                if saml_meeting_user_field == "number":
                    # Number cannot have a default.
                    if value := instance.get(idp_attribute):
                        result = cast(str, value)
                    else:
                        missing_attributes.append(idp_attribute)
                elif not (value := instance.get(idp_attribute)):
                    missing_attributes.append(idp_attribute)
                    value = attr_default.get("default")
                if value:
                    if saml_meeting_user_field in ["groups", "structure_levels"]:
                        # Need to append to group and structure_level for same meeting.
                        if not result:
                            result = set()
                        cast(set, result).update(value.split(", "))
                    elif saml_meeting_user_field == "comment":
                        # Want comments from all matching mappers.
                        if result:
                            result = cast(str, result) + " " + value
                        else:
                            result = value
                    elif saml_meeting_user_field == "present":
                        # Result is int or bool. int will later be interpreted as bool.
                        result = (
                            value
                            if not isinstance(value, str)
                            else (
                                False
                                if value.casefold() == "false".casefold()
                                else True
                            )
                        )
                    else:
                        result = value
            if result:
                yield saml_meeting_user_field, result
        if fields := ",".join(missing_attributes):
            mapper_name = meeting_mapper.get("name", "unnamed")
            self.logger.debug(
                f"Meeting mapper: {mapper_name} could not find value in idp data for fields: {fields}. Using default if available."
            )

    def get_group_ids(self, group_names: list[str], meeting: dict) -> list[int]:
        """
        Gets the group ids from given group names in that meeting.
        If none of the groups exists in the meeting, the meetings default group is returned.
        """
        if group_names:
            groups = self.datastore.filter(
                "group",
                And(
                    FilterOperator("meeting_id", "=", meeting["id"]),
                    Or(
                        FilterOperator("external_id", "=", group_name)
                        for group_name in group_names
                    ),
                ),
                ["meeting_user_ids"],
            )
            if len(groups) > 0:
                return sorted(groups)
        if default_group_id := meeting["default_group_id"]:
            external_meeting_id = meeting["external_id"]
            self.logger.warning(
                f"save_saml_account found no group in meeting '{external_meeting_id}' for {group_names}, but used default_group of meeting"
            )
            return [default_group_id]
        else:
            assert False

    def get_structure_level_ids(
        self, structure_level_names: list[str], meeting: dict[str, Any]
    ) -> list[int]:
        """
        Gets the structure level ids from given structure level names in that meeting.
        For this also creates new structure levels not already existing in the meeting.
        """
        if structure_level_names:
            meeting_id = meeting["id"]
            found_structure_levels = self.datastore.filter(
                "structure_level",
                And(
                    FilterOperator("meeting_id", "=", meeting_id),
                    Or(
                        FilterOperator("name", "=", structure_level_name)
                        for structure_level_name in structure_level_names
                        if structure_level_name
                    ),
                ),
                ["meeting_user_ids"],
            )
            found_structure_level_ids = list(found_structure_levels.keys())
            if len(found_structure_levels) == len(structure_level_names):
                return found_structure_level_ids
            else:
                found_structure_level_names = [
                    structure_level.get("name")
                    for structure_level in found_structure_levels.values()
                ]
                to_be_created_structure_levels = [
                    sl_name
                    for sl_name in structure_level_names
                    if sl_name and sl_name not in found_structure_level_names
                ]
                # meeting_user_ids are only known during UserUpdate. Hence we cannot do batch create for all meeting users
                if structure_levels_result := (
                    self.execute_other_action(
                        StructureLevelCreateAction,
                        [
                            {"name": structure_level_name, "meeting_id": meeting_id}
                            for structure_level_name in to_be_created_structure_levels
                        ],
                    )
                ):
                    return sorted(
                        [
                            structure_level["id"]
                            for structure_level in structure_levels_result
                            if structure_level
                        ]
                        + found_structure_level_ids
                    )
        return []
