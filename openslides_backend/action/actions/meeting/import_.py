import time
from collections import defaultdict
from typing import Any, Dict, Iterable, Optional, Tuple

from ....models.base import model_registry
from ....models.checker import Checker, CheckException
from ....models.fields import (
    BaseTemplateField,
    GenericRelationField,
    GenericRelationListField,
    RelationField,
    RelationListField,
)
from ....models.models import Meeting
from ....permissions.management_levels import CommitteeManagementLevel
from ....permissions.permission_helper import has_committee_management_level
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.filters import FilterOperator
from ....shared.interfaces.event import EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...action import Action
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.crypto import get_random_string
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement, ActionResults
from ..motion.update import RECOMMENDATION_EXTENSION_REFERENCE_IDS_PATTERN


@register_action("meeting.import")
class MeetingImport(SingularActionMixin, Action):
    """
    Action to import a meeting.
    """

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_default_schema(
        required_properties=["committee_id"],
        additional_required_fields={"meeting": {"type": "object"}},
        title="Import meeting",
        description="Import a meeting into the committee.",
    )

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> Tuple[Optional[WriteRequest], Optional[ActionResults]]:
        """
        Simplified entrypoint to perform the action.
        """
        self.user_id = user_id
        self.index = 0
        action_data = self.get_updated_instances(action_data)
        instance = next(iter(action_data))
        self.validate_instance(instance)
        try:
            self.check_permissions(instance)
        except MissingPermission as e:
            msg = f"You are not allowed to perform action {self.name}."
            e.message = msg + " " + e.message
            raise e
        instance = self.base_update_instance(instance)
        self.write_requests.extend(self.create_write_requests(instance))
        final_write_request = self.process_write_requests()
        result = [self.create_action_result_element(instance)]
        return (final_write_request, result)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_json = instance["meeting"]

        # checks if the meeting is correct
        if not len(meeting_json.get("meeting", [])) == 1:
            raise ActionException("Need exact one meeting in meeting collection.")

        self.check_usernames_and_generate_new_ones(meeting_json)

        # save blobs from mediafiles
        self.mediadata = []
        json_data = instance["meeting"]
        for entry in json_data.get("mediafile", []):
            if "blob" in entry:
                self.mediadata.append(
                    (entry.pop("blob"), entry["id"], entry["mimetype"])
                )

        # check datavalidation
        checker = Checker(data=json_data, is_import=True)
        try:
            checker.run_check()
        except CheckException as ce:
            raise ActionException(str(ce))

        for entry in json_data.get("motion", []):
            if entry.get("all_origin_ids") or entry.get("all_derived_motion_ids"):
                raise ActionException(
                    "Motion all_origin_ids and all_derived_motion_ids should be empty."
                )

        self.update_meeting_and_users(instance)

        # replace ids in the meeting_json
        self.create_replace_map(meeting_json)
        self.replace_fields(instance)
        self.update_admin_group(meeting_json)
        self.upload_mediadata()
        return instance

    def check_usernames_and_generate_new_ones(self, json_data: Dict[str, Any]) -> None:
        used_usernames = set()
        for entry in json_data.get("user", []):
            is_username_unique = False
            template_username = entry["username"]
            count = 1
            while not is_username_unique:
                if entry["username"] in used_usernames:
                    entry["username"] = template_username + " " + str(count)
                    count += 1
                    continue
                result = self.datastore.filter(
                    Collection("user"),
                    FilterOperator("username", "=", entry["username"]),
                    ["id"],
                )
                if result:
                    entry["username"] = template_username + " " + str(count)
                    count += 1
                    continue
                is_username_unique = True
            used_usernames.add(entry["username"])

    def update_meeting_and_users(self, instance: Dict[str, Any]) -> None:
        # update committee_id
        json_data = instance["meeting"]
        json_data["meeting"][0]["committee_id"] = instance["committee_id"]
        json_data["meeting"][0]["is_active_in_organization_id"] = 1

        # generate passwords
        for entry in json_data["user"]:
            entry["password"] = self.auth.hash(get_random_string(10))

        # set enable_anonymous
        json_data["meeting"][0]["enable_anonymous"] = False

        # set imported_at
        json_data["meeting"][0]["imported_at"] = round(time.time())

    def create_replace_map(self, json_data: Dict[str, Any]) -> None:
        replace_map: Dict[str, Dict[int, int]] = defaultdict(dict)
        for collection in json_data:
            if not json_data[collection]:
                continue
            new_ids = self.datastore.reserve_ids(
                Collection(collection), len(json_data[collection])
            )
            for entry, new_id in zip(json_data[collection], new_ids):
                replace_map[collection][entry["id"]] = new_id
        self.replace_map = replace_map

    def replace_fields(
        self, instance: Dict[str, Any], ignore_user: bool = False
    ) -> None:
        json_data = instance["meeting"]
        for collection in json_data:
            if ignore_user and collection == "user":
                continue
            for entry in json_data[collection]:
                for field in list(entry.keys()):
                    self.replace_field_ids(collection, entry, field)

    def replace_field_ids(
        self,
        collection: str,
        entry: Dict[str, Any],
        field: str,
    ) -> None:

        model_field = model_registry[Collection(collection)]().try_get_field(field)
        if model_field is None:
            raise ActionException(f"{collection}/{field} is not allowed.")
        elif field == "id":
            entry["id"] = self.replace_map[collection][entry["id"]]
        elif collection == "meeting" and field in (
            "committee_id",
            "is_active_in_organization_id",
        ):
            pass
        elif collection == "meeting" and field == "user_ids":
            entry[field] = [self.replace_map["user"][id_] for id_ in entry[field] or []]
        elif collection == "user" and field == "meeting_ids":
            entry[field] = list(self.replace_map["meeting"].values())
        elif collection == "motion" and field == "recommendation_extension":
            if entry[field]:
                fqids_str = RECOMMENDATION_EXTENSION_REFERENCE_IDS_PATTERN.findall(
                    entry[field]
                )
                entry_str = entry[field]
                entry_list = []
                for fqid in fqids_str:
                    search_str = "[" + fqid + "]"
                    idx = entry_str.find(search_str)
                    entry_list.append(entry_str[:idx])
                    col, id_ = fqid.split(KEYSEPARATOR)
                    replace_str = (
                        "["
                        + col
                        + KEYSEPARATOR
                        + str(self.replace_map[col][int(id_)])
                        + "]"
                    )
                    entry_list.append(replace_str)
                    entry_str = entry_str[idx + len(replace_str) :]
                entry_list.append(entry_str)
                entry[field] = "".join(entry_list)
        else:
            if (
                isinstance(model_field, BaseTemplateField)
                and model_field.is_template_field(field)
                and model_field.replacement_collection
            ):
                entry[field] = [
                    str(
                        self.replace_map[model_field.replacement_collection.collection][
                            int(id_)
                        ]
                    )
                    for id_ in entry[field]
                ]
            elif (
                isinstance(model_field, BaseTemplateField)
                and model_field.is_template_field(field)
                and not model_field.replacement_collection
            ):
                pass
            elif isinstance(model_field, RelationField):
                target_collection = model_field.get_target_collection().collection
                if entry[field]:
                    entry[field] = self.replace_map[target_collection][entry[field]]
            elif isinstance(model_field, RelationListField):
                target_collection = model_field.get_target_collection().collection
                entry[field] = [
                    self.replace_map[target_collection][id_]
                    for id_ in entry[field] or []
                ]
            elif isinstance(model_field, GenericRelationField):
                if entry[field]:
                    name, id_ = entry[field].split(KEYSEPARATOR)
                    entry[field] = (
                        name + KEYSEPARATOR + str(self.replace_map[name][int(id_)])
                    )
            elif isinstance(model_field, GenericRelationListField):
                new_fqid_list = []
                for fqid in entry[field]:
                    name, id_ = fqid.split(KEYSEPARATOR)
                    new_fqid_list.append(
                        name + KEYSEPARATOR + str(self.replace_map[name][int(id_)])
                    )
                entry[field] = new_fqid_list
            if (
                isinstance(model_field, BaseTemplateField)
                and model_field.replacement_collection
                and not model_field.is_template_field(field)
            ):
                replacement = model_field.get_replacement(field)
                id_ = int(replacement)
                new_id_ = self.replace_map[
                    model_field.replacement_collection.collection
                ][id_]
                new_field = model_field.get_structured_field_name(new_id_)
                tmp = entry[field]
                del entry[field]
                entry[new_field] = tmp

    def update_admin_group(self, data_json: Dict[str, Any]) -> None:
        admin_group_id = data_json["meeting"][0]["admin_group_id"]
        for entry in data_json["group"]:
            if entry["id"] == admin_group_id:
                if entry["user_ids"]:
                    entry["user_ids"].insert(0, self.user_id)
                else:
                    entry["user_ids"] = [self.user_id]

        data_json["meeting"][0]["user_ids"].insert(0, self.user_id)

    def upload_mediadata(self) -> None:
        for blob, id_, mimetype in self.mediadata:
            replaced_id = self.replace_map["mediafile"][id_]
            self.media.upload_mediafile(blob, replaced_id, mimetype)

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        json_data = instance["meeting"]
        meeting_id = json_data["meeting"][0]["id"]
        write_requests = []
        for collection in json_data:
            for entry in json_data[collection]:
                fqid = FullQualifiedId(Collection(collection), entry["id"])
                write_requests.append(
                    self.build_write_request(
                        EventType.Create,
                        fqid,
                        f"import meeting {meeting_id}",
                        entry,
                    )
                )
        # add meeting to committee/meeting_ids
        write_requests.append(
            self.build_write_request(
                EventType.Update,
                FullQualifiedId(
                    Collection("committee"), json_data["meeting"][0]["committee_id"]
                ),
                f"import meeting {meeting_id}",
                None,
                {"add": {"meeting_ids": [meeting_id]}, "remove": {}},
            )
        )
        # add meeting to organization/active_meeting_ids
        write_requests.append(
            self.build_write_request(
                EventType.Update,
                FullQualifiedId(Collection("organization"), 1),
                f"import meeting {meeting_id}",
                None,
                {"add": {"active_meeting_ids": [meeting_id]}, "remove": {}},
            )
        )
        return write_requests

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        """Returns the newly created id."""
        return {"id": instance["meeting"]["meeting"][0]["id"]}

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if not has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            instance["committee_id"],
        ):
            raise MissingPermission(CommitteeManagementLevel.CAN_MANAGE)
