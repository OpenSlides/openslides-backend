import time
from typing import Any, Dict, Iterable, Optional, Tuple

from ....models.base import model_registry
from ....models.fields import (
    BaseTemplateField,
    GenericRelationField,
    GenericRelationListField,
    RelationField,
    RelationListField,
)
from ....models.models import Committee
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
from ...util.typing import ActionData, ActionResults


@register_action("committee.import_meeting")
class CommitteeImportMeeting(SingularActionMixin, Action):
    """
    Action to import a meeting.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_update_schema(
        additional_required_fields={"meeting_json": {"type": "object"}}
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
        return (final_write_request, None)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_json = instance["meeting_json"]

        # checks if the meeting_json is correct
        if not len(meeting_json.get("meeting", [])) == 1:
            raise ActionException("Need exact one meeting in meeting collection.")
        allowed_collections = (
            "user",
            "meeting",
            "group",
            "personal_note",
            "tag",
            "agenda_item",
            "list_of_speakers",
            "speaker",
            "topic",
            "motion",
            "motion_submitter",
            "motion_comment",
            "motion_comment_section",
            "motion_category",
            "motion_block",
            "motion_change_recommendation",
            "motion_state",
            "motion_workflow",
            "motion_statute_paragraph",
            "poll",
            "option",
            "vote",
            "assignment",
            "assignment_candidate",
            "mediafile",
            "projector",
            "projection",
            "projector_message",
            "projector_countdown",
            "chat_group",
        )

        for collection in meeting_json:
            if meeting_json.get(collection) and collection not in allowed_collections:
                raise ActionException(f"{collection} must be empty.")

        self.check_usernames_and_generate_new_ones(meeting_json)
        self.update_meeting_and_generate_passwords(instance)

        # replace ids in the meeting_json
        self.create_replace_map(meeting_json)
        self.replace_fields(instance)
        return instance

    def check_usernames_and_generate_new_ones(self, json_data: Dict[str, Any]) -> None:
        used_usernames = set()
        for entry in json_data["user"]:
            is_username_unique = False
            template_username = entry["username"].rstrip(" 0123456789")
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

    def update_meeting_and_generate_passwords(self, instance: Dict[str, Any]) -> None:
        # update committee_id
        json_data = instance["meeting_json"]
        json_data["meeting"][0]["committee_id"] = instance["id"]

        # generate passwords
        for entry in json_data["user"]:
            entry["password"] = self.auth.hash(get_random_string(10))

        # set enable_anonymous
        json_data["meeting"][0]["enable_anonymous"] = False

        # set imported_at
        json_data["meeting"][0]["imported_at"] = round(time.time())

    def create_replace_map(self, json_data: Dict[str, Any]) -> None:
        replace_map: Dict[str, Dict[int, int]] = {}
        for collection in json_data:
            replace_map[collection] = {}
            new_ids = self.datastore.reserve_ids(
                Collection(collection), len(json_data[collection])
            )
            for entry, new_id in zip(json_data[collection], new_ids):
                replace_map[collection][entry["id"]] = new_id
        self.replace_map = replace_map

    def replace_fields(self, instance: Dict[str, Any]) -> None:
        json_data = instance["meeting_json"]
        for collection in json_data:
            for entry in json_data[collection]:
                for field in list(entry.keys()):
                    self.replace_field_ids(collection, entry, field)

    def replace_field_ids(
        self,
        collection: str,
        entry: Dict[str, Any],
        field: str,
    ) -> None:
        if field == "id":
            entry["id"] = self.replace_map[collection][entry["id"]]
        elif collection == "meeting" and field == "committee_id":
            pass
        else:
            model_field = model_registry[Collection(collection)]().try_get_field(field)
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
            elif isinstance(model_field, RelationField):
                target_collection = model_field.get_target_collection().collection
                if entry[field]:
                    entry[field] = self.replace_map[target_collection][entry[field]]
            elif isinstance(model_field, RelationListField):
                target_collection = model_field.get_target_collection().collection
                entry[field] = [
                    self.replace_map[target_collection][id_] for id_ in entry[field]
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

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        json_data = instance["meeting_json"]
        write_requests = []
        for collection in json_data:
            for entry in json_data[collection]:
                fqid = FullQualifiedId(Collection(collection), entry["id"])
                write_requests.append(
                    self.build_write_request(
                        EventType.Create,
                        fqid,
                        f"import meeting {json_data['meeting'][0]['id']}",
                        entry,
                    )
                )
        # add meeting to committee/meeting_ids
        write_requests.append(
            self.build_write_request(
                EventType.Update,
                FullQualifiedId(Collection("committee"), instance["id"]),
                f"import meeting {json_data['meeting'][0]['id']}",
                None,
                {"add": {"meeting_ids": [json_data["meeting"][0]["id"]]}, "remove": {}},
            )
        )
        return write_requests

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if not has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            instance["id"],
        ):
            raise MissingPermission(CommitteeManagementLevel.CAN_MANAGE)
