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
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.filters import FilterOperator
from ....shared.interfaces.event import EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...action import Action
from ...util.crypto import get_random_string
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResults


@register_action("committee.import_meeting")
class CommitteeImportMeeting(Action):
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
        for instance in action_data:
            self.validate_instance(instance)
            try:
                self.check_permissions(instance)
            except MissingPermission as e:
                msg = f"You are not allowed to perform action {self.name}."
                e.message = msg + " " + e.message
                raise e
            self.index += 1
        self.index = -1

        instances = self.get_updated_instances(action_data)
        for instance in instances:
            instance = self.base_update_instance(instance)
            write_request = self.create_write_requests(instance)
            self.write_requests.extend(write_request)

        final_write_request = self.process_write_requests()
        return (final_write_request, None)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_json = instance["meeting_json"]

        # checks if the meeting_json is correct
        if not len(meeting_json.get("meeting", [])) == 1:
            raise ActionException("Need exact one meeting in meeting collection.")
        shall_be_empty = ("organization", "organization_tag", "committee", "resource")

        for collection in shall_be_empty:
            if meeting_json.get(collection):
                raise ActionException(f"{collection} must be empty.")

        for user in meeting_json.get("user", []):
            if not user["password"] == "":
                raise ActionException("User password must be an empty string.")

        self.check_usernames_and_generate_new_ones(meeting_json)
        self.update_meeting_and_generate_passwords(instance)

        # replace ids in the meeting_json
        replace_map = self.create_replace_map(meeting_json)
        self.replace_fields(instance, replace_map)
        return instance

    def check_usernames_and_generate_new_ones(self, json_data: Dict[str, Any]) -> None:
        used_usernames = set()
        for entry in json_data["user"]:
            username_unique = False
            template_username = entry["username"].rstrip("0123456789")
            count = 1
            while not username_unique:
                if entry["username"] in used_usernames:
                    entry["username"] = template_username + str(count)
                    count += 1
                    continue
                result = self.datastore.filter(
                    Collection("user"),
                    FilterOperator("username", "=", entry["username"]),
                    ["id"],
                )
                if result:
                    entry["username"] = template_username + str(count)
                    count += 1
                    continue
                username_unique = True
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

    def create_replace_map(
        self, json_data: Dict[str, Any]
    ) -> Dict[str, Dict[int, int]]:
        replace_map: Dict[str, Dict[int, int]] = {}
        for collection in json_data:
            replace_map[collection] = {}
            new_ids = self.datastore.reserve_ids(
                Collection(collection), len(json_data[collection])
            )
            for entry, new_id in zip(json_data[collection], new_ids):
                replace_map[collection][entry["id"]] = new_id
        return replace_map

    def replace_fields(
        self, instance: Dict[str, Any], replace_map: Dict[str, Dict[int, int]]
    ) -> None:
        json_data = instance["meeting_json"]
        for collection in json_data:
            for entry in json_data[collection]:
                for field in list(entry.keys()):
                    self.replace_field_ids(collection, entry, field, replace_map)

    def replace_field_ids(
        self,
        collection: str,
        entry: Dict[str, Any],
        field: str,
        replace_map: Dict[str, Dict[int, int]],
    ) -> None:
        if field == "id":
            entry["id"] = replace_map[collection][entry["id"]]
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
                        replace_map[model_field.replacement_collection.collection][
                            int(id_)
                        ]
                    )
                    for id_ in entry[field]
                ]
            elif isinstance(model_field, RelationField):
                target_collection = model_field.get_target_collection().collection
                if entry[field]:
                    entry[field] = replace_map[target_collection][entry[field]]
            elif isinstance(model_field, RelationListField):
                target_collection = model_field.get_target_collection().collection
                entry[field] = [
                    replace_map[target_collection][id_] for id_ in entry[field]
                ]
            elif isinstance(model_field, GenericRelationField):
                if entry[field]:
                    name, id_ = entry[field].split(KEYSEPARATOR)
                    entry[field] = (
                        name + KEYSEPARATOR + str(replace_map[name][int(id_)])
                    )
            elif isinstance(model_field, GenericRelationListField):
                new_fqid_list = []
                for fqid in entry[field]:
                    name, id_ = fqid.split(KEYSEPARATOR)
                    new_fqid_list.append(
                        name + KEYSEPARATOR + str(replace_map[name][int(id_)])
                    )
                entry[field] = new_fqid_list
            if (
                isinstance(model_field, BaseTemplateField)
                and model_field.replacement_collection
                and not model_field.is_template_field(field)
            ):
                replacement = model_field.get_replacement(field)
                id_ = int(replacement)
                new_id_ = replace_map[model_field.replacement_collection.collection][
                    id_
                ]
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
        return
