import re
import time
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union, cast

from datastore.migrations import BaseEvent, CreateEvent, ListUpdateEvent, UpdateEvent

from openslides_backend.migrations import get_backend_migration_index
from openslides_backend.migrations.migrate import MigrationWrapper
from openslides_backend.models.base import model_registry
from openslides_backend.models.checker import Checker, CheckException
from openslides_backend.models.fields import (
    BaseGenericRelationField,
    BaseRelationField,
    BaseTemplateField,
    GenericRelationField,
    GenericRelationListField,
    RelationField,
    RelationListField,
    TemplateCharField,
    TemplateDecimalField,
    TemplateHTMLStrictField,
    TemplateRelationField,
)
from openslides_backend.models.models import Meeting, User
from openslides_backend.permissions.management_levels import CommitteeManagementLevel
from openslides_backend.permissions.permission_helper import (
    has_committee_management_level,
)
from openslides_backend.services.datastore.interface import GetManyRequest
from openslides_backend.shared.exceptions import ActionException, MissingPermission
from openslides_backend.shared.filters import FilterOperator, Or
from openslides_backend.shared.interfaces.event import EventType
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.shared.patterns import (
    KEYSEPARATOR,
    collection_and_id_from_fqid,
    collection_from_fqid,
    fqid_from_collection_and_id,
)
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....shared.interfaces.event import Event, ListFields
from ....shared.util import ONE_ORGANIZATION_ID
from ...action import RelationUpdates
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.crypto import get_random_string
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement, ActionResults
from ..motion.update import EXTENSION_REFERENCE_IDS_PATTERN
from ..user.user_mixin import LimitOfUserMixin, UsernameMixin


@register_action("meeting.import")
class MeetingImport(SingularActionMixin, LimitOfUserMixin, UsernameMixin):
    """
    Action to import a meeting.
    """

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_default_schema(
        required_properties=["committee_id"],
        additional_required_fields={
            "meeting": {"type": "object"},
        },
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

        # prefetch as much data as possible
        self.prefetch(action_data)

        action_data = self.get_updated_instances(action_data)
        instance = next(iter(action_data))
        instance = self.preprocess_data(instance)
        self.validate_instance(instance)
        try:
            self.check_permissions(instance)
        except MissingPermission as e:
            msg = f"You are not allowed to perform action {self.name}."
            e.message = msg + " " + e.message
            raise e
        instance = self.base_update_instance(instance)
        self.events.extend(self.create_events(instance))
        write_request = self.build_write_request()
        result = [self.create_action_result_element(instance)]
        return (write_request, result)

    def prefetch(self, action_data: ActionData) -> None:
        requests = [
            GetManyRequest(
                "organization",
                [ONE_ORGANIZATION_ID],
                [
                    "active_meeting_ids",
                    "archived_meeting_ids",
                ],
            ),
            GetManyRequest(
                "committee",
                list({instance["committee_id"] for instance in action_data}),
                [
                    "meeting_ids",
                ],
            ),
        ]
        if self.user_id:
            cml_fields = [
                f"committee_${management_level}_management_level"
                for management_level in cast(
                    List[str], User.committee__management_level.replacement_enum
                )
            ]
            requests.append(
                GetManyRequest(
                    "user",
                    [self.user_id],
                    ["group_$_ids", "committee_ids", *cml_fields],
                ),
            )
        self.datastore.get_many(requests, use_changed_models=False)

    def preprocess_data(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        self.check_one_meeting(instance)
        self.remove_not_allowed_fields(instance)
        self.set_committee_and_orga_relation(instance)
        instance = self.migrate_data(instance)
        self.unset_committee_and_orga_relation(instance)
        return instance

    def check_one_meeting(self, instance: Dict[str, Any]) -> None:
        meeting_json = instance.get("meeting", {})
        if not len(meeting_json.get("meeting", {}).values()) == 1:
            raise ActionException("Need exactly one meeting in meeting collection.")

    def remove_not_allowed_fields(self, instance: Dict[str, Any]) -> None:
        json_data = instance["meeting"]
        regex_cml = re.compile(r"^committee_\$(\D)*_management_level$")

        def remove_from_collection(
            model: Dict[str, Any], regex: re.Pattern[str]
        ) -> None:
            keys: List[str] = []
            for key in model.keys():
                if regex.search(key):
                    keys.append(key)
            for key in keys:
                model.pop(key)

        for user in json_data.get("user", {}).values():
            user.pop("organization_management_level", None)
            user.pop("committee_ids", None)
            remove_from_collection(user, regex_cml)
        self.get_meeting_from_json(json_data).pop("organization_tag_ids", None)
        json_data.pop("action_worker", None)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_json = instance["meeting"]
        self.generate_merge_user_map(meeting_json)
        self.check_usernames_and_generate_new_ones(meeting_json)
        active_new_users_in_json = len(
            [
                key
                for key in meeting_json.get("user", [])
                if meeting_json["user"][key].get("is_active")
                and int(key) not in self.merge_user_map
            ]
        )
        self.check_limit_of_user(active_new_users_in_json)

        # save blobs from mediafiles
        self.mediadata = []
        for entry in meeting_json.get("mediafile", {}).values():
            # mediafiles have "blob": None
            if blob := entry.pop("blob", None):
                self.mediadata.append((blob, entry["id"], entry["mimetype"]))

        for entry in meeting_json.get("motion", {}).values():
            to_remove = set()
            for paragraph in entry.get("amendment_paragraph_$") or []:
                if (entry.get(fname := "amendment_paragraph_$" + paragraph)) is None:
                    to_remove.add(paragraph)
                    entry.pop(fname, None)
            if to_remove:
                entry["amendment_paragraph_$"] = list(
                    set(entry["amendment_paragraph_$"]) - to_remove
                )

        # check datavalidation
        checker = Checker(
            data=meeting_json,
            mode="external",
            repair=True,
            fields_to_remove={
                "motion": [
                    "origin_id",
                    "derived_motion_ids",
                    "all_origin_id",
                    "all_derived_motion_ids",
                ],
                "user": [
                    "password",
                    "default_password",
                    "last_email_sent",
                    "last_login",
                ],
            },
        )
        try:
            checker.run_check()
        except CheckException as ce:
            raise ActionException(str(ce))
        self.allowed_collections = checker.allowed_collections

        for entry in meeting_json.get("motion", {}).values():
            if entry.get("all_origin_ids") or entry.get("all_derived_motion_ids"):
                raise ActionException(
                    "Motion all_origin_ids and all_derived_motion_ids should be empty."
                )

        self.check_limit_of_meetings()
        self.update_meeting_and_users(instance)

        # replace ids in the meeting_json
        self.create_replace_map(meeting_json)
        self.replace_fields(instance)
        meeting_json = instance["meeting"]
        self.update_admin_group(meeting_json)
        self.upload_mediadata()
        return instance

    def empty_if_none(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        return value

    def get_user_key(self, user_values: Dict[str, Any]) -> Tuple[str, str, str, str]:
        return (
            self.empty_if_none(user_values.get("username")),
            self.empty_if_none(user_values.get("first_name")),
            self.empty_if_none(user_values.get("last_name")),
            self.empty_if_none(user_values.get("email")).lower(),
        )

    def generate_merge_user_map(self, json_data: Dict[str, Any]) -> None:
        for entry in json_data.get("user", {}).values():
            entry["username"] = entry["username"].strip()
        filter_ = Or(
            *[
                FilterOperator("username", "=", entry["username"])
                for entry in json_data.get("user", {}).values()
            ]
        )

        filtered_users = self.datastore.filter(
            "user",
            filter_,
            ["username", "first_name", "last_name", "email"],
            lock_result=False,
            use_changed_models=False,
        )
        filtered_users_dict = {
            self.get_user_key(values): key for key, values in filtered_users.items()
        }

        self.merge_user_map = {
            int(key): filtered_users_dict[self.get_user_key(values)]
            for key, values in json_data.get("user", {}).items()
            if filtered_users_dict.get(self.get_user_key(values)) is not None
        }
        self.number_of_imported_users = len(json_data.get("user", {}))
        self.number_of_merged_users = len(self.merge_user_map)

    def check_usernames_and_generate_new_ones(self, json_data: Dict[str, Any]) -> None:
        user_entries = [
            entry
            for entry in json_data.get("user", {}).values()
            if int(entry["id"]) not in self.merge_user_map
        ]
        usernames: List[str] = [entry["username"] for entry in user_entries]
        new_usernames = self.generate_usernames(usernames)

        for entry, username in zip(user_entries, new_usernames):
            entry["username"] = username

    def check_limit_of_meetings(
        self, text: str = "import", text2: str = "active "
    ) -> None:
        organization = self.datastore.get(
            fqid_from_collection_and_id("organization", ONE_ORGANIZATION_ID),
            ["active_meeting_ids", "limit_of_meetings"],
            lock_result=False,
            use_changed_models=False,
        )
        if (
            limit_of_meetings := organization.get("limit_of_meetings", 0)
        ) and limit_of_meetings == len(organization.get("active_meeting_ids", [])):
            raise ActionException(
                f"You cannot {text} an {text2}meeting, because you reached your limit of {limit_of_meetings} active meetings."
            )

    def set_committee_and_orga_relation(self, instance: Dict[str, Any]) -> None:
        json_data = instance["meeting"]
        meeting = self.get_meeting_from_json(json_data)
        meeting["committee_id"] = instance["committee_id"]
        meeting["is_active_in_organization_id"] = ONE_ORGANIZATION_ID

    def unset_committee_and_orga_relation(self, instance: Dict[str, Any]) -> None:
        json_data = instance["meeting"]
        meeting = self.get_meeting_from_json(json_data)
        meeting["committee_id"] = None
        meeting["is_active_in_organization_id"] = None

    def update_meeting_and_users(self, instance: Dict[str, Any]) -> None:
        # update committee_id and is_active_in_organization_id
        json_data = instance["meeting"]
        meeting = self.get_meeting_from_json(json_data)
        meeting["committee_id"] = instance["committee_id"]
        meeting["is_active_in_organization_id"] = ONE_ORGANIZATION_ID

        # generate passwords
        for entry in json_data["user"].values():
            if entry["id"] not in self.merge_user_map:
                entry["default_password"] = get_random_string(10)
                entry["password"] = self.auth.hash(entry["default_password"])

        # set enable_anonymous
        meeting["enable_anonymous"] = False

        # set imported_at
        meeting["imported_at"] = round(time.time())

    def get_meeting_from_json(self, json_data: Any) -> Any:
        """
        Small helper to retrieve the one and only meeting object from the import data.
        """
        key = next(iter(json_data["meeting"]))
        return json_data["meeting"][key]

    def create_replace_map(self, json_data: Dict[str, Any]) -> None:
        replace_map: Dict[str, Dict[int, int]] = defaultdict(dict)
        for collection in json_data:
            if collection.startswith("_") or not json_data[collection]:
                continue
            if collection != "user":
                new_ids = self.datastore.reserve_ids(
                    collection, len(json_data[collection])
                )
                for entry, new_id in zip(json_data[collection].values(), new_ids):
                    replace_map[collection][entry["id"]] = new_id
            else:
                if (
                    amount := self.number_of_imported_users
                    - self.number_of_merged_users
                ):
                    new_user_ids = iter(self.datastore.reserve_ids("user", amount))
                for entry in json_data[collection].values():
                    if (user_id := entry["id"]) in self.merge_user_map:
                        replace_map[collection][user_id] = self.merge_user_map[user_id]
                    else:
                        replace_map[collection][user_id] = next(new_user_ids)
        self.replace_map = replace_map

    def replace_fields(self, instance: Dict[str, Any]) -> None:
        json_data = instance["meeting"]
        new_json_data = {}
        for collection in json_data:
            if collection.startswith("_"):
                continue
            new_collection = {}
            for entry in json_data[collection].values():
                old_entry_id = entry["id"]
                for field in list(entry.keys()):
                    self.replace_field_ids(collection, entry, field)
                new_collection[str(entry["id"])] = entry
                if collection != "user" or old_entry_id not in self.merge_user_map:
                    entry["meta_new"] = True
                self.datastore.apply_changed_model(
                    fqid_from_collection_and_id(collection, entry["id"]), entry
                )
            new_json_data[collection] = new_collection
        instance["meeting"] = new_json_data

    def replace_field_ids(
        self,
        collection: str,
        entry: Dict[str, Any],
        field: str,
    ) -> None:
        model_field = model_registry[collection]().try_get_field(field)
        if model_field is None:
            raise ActionException(f"{collection}/{field} is not allowed.")
        if isinstance(model_field, BaseRelationField):
            if isinstance(model_field, BaseGenericRelationField):
                content_list = (
                    content
                    if isinstance(content := entry.get(field), list)
                    else [content]
                )
                target_collections = [
                    item.split(KEYSEPARATOR)[0] for item in content_list if item
                ]
            else:
                target_collections = list(model_field.to.keys())
            if all(c not in self.allowed_collections for c in target_collections):
                return
        if field == "id":
            entry["id"] = self.replace_map[collection][entry["id"]]
        elif collection == "meeting" and field == "user_ids":
            entry[field] = None
        elif collection == "user" and field == "meeting_ids":
            entry[field] = None
        elif collection == "motion" and field in (
            "recommendation_extension",
            "state_extension",
        ):
            if entry[field]:

                def replace_fn(match: re.Match[str]) -> str:
                    # replace the reference patterns in the extension fields with the new ids
                    collection, id = collection_and_id_from_fqid(match.group("fqid"))
                    new_id = self.replace_map[collection][id]
                    return f"[{fqid_from_collection_and_id(collection, new_id)}]"

                entry[field] = EXTENSION_REFERENCE_IDS_PATTERN.sub(
                    replace_fn, entry[field]
                )
        else:
            if (
                isinstance(model_field, BaseTemplateField)
                and model_field.is_template_field(field)
                and model_field.replacement_collection
            ):
                entry[field] = [
                    str(self.replace_map[model_field.replacement_collection][int(id_)])
                    for id_ in entry[field]
                ]
            elif (
                isinstance(model_field, BaseTemplateField)
                and model_field.is_template_field(field)
                and not model_field.replacement_collection
            ):
                pass
            elif isinstance(model_field, RelationField):
                target_collection = model_field.get_target_collection()
                if entry[field]:
                    entry[field] = self.replace_map[target_collection][entry[field]]
            elif isinstance(model_field, RelationListField):
                target_collection = model_field.get_target_collection()
                entry[field] = [
                    self.replace_map[target_collection][id_]
                    for id_ in entry.get(field) or []
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
                new_id_ = self.replace_map[model_field.replacement_collection][id_]
                new_field = model_field.get_structured_field_name(new_id_)
                tmp = entry[field]
                del entry[field]
                entry[new_field] = tmp

    def update_admin_group(self, data_json: Dict[str, Any]) -> None:
        meeting = self.get_meeting_from_json(data_json)
        admin_group_id = meeting.get("admin_group_id")
        group = data_json.get("group", {}).get(str(admin_group_id))
        if not group:
            raise ActionException(
                "Imported meeting has no AdminGroup to assign to request user"
            )
        if group.get("user_ids"):
            if self.user_id not in group["user_ids"]:
                group["user_ids"].insert(0, self.user_id)
        else:
            group["user_ids"] = [self.user_id]
        self.new_group_for_request_user = admin_group_id

    def upload_mediadata(self) -> None:
        for blob, id_, mimetype in self.mediadata:
            replaced_id = self.replace_map["mediafile"][id_]
            self.media.upload_mediafile(blob, replaced_id, mimetype)

    def create_events(
        self, instance: Dict[str, Any], pure_create_events: bool = False
    ) -> Iterable[Event]:
        """Be careful, this method is also used by meeting.clone!"""
        json_data = instance["meeting"]
        meeting = self.get_meeting_from_json(json_data)
        meeting_id = meeting["id"]
        events = []
        update_events = []
        for collection in json_data:
            for entry in json_data[collection].values():
                meta_new = entry.pop("meta_new", None)
                if meta_new:
                    fqid = fqid_from_collection_and_id(collection, entry["id"])
                    events.append(
                        self.build_event(
                            EventType.Create,
                            fqid,
                            entry,
                        )
                    )
                elif (
                    collection == "user" and entry["id"] in self.merge_user_map.values()
                ):
                    list_fields: ListFields = {"add": {}, "remove": {}}
                    fields: Dict[str, Any] = {}
                    for field, value in entry.items():
                        model_field = model_registry[collection]().try_get_field(field)
                        if (
                            isinstance(model_field, BaseTemplateField)
                            and model_field.replacement_collection
                            and isinstance(model_field, RelationListField)
                        ):
                            list_fields["add"][field] = value
                        elif isinstance(model_field, BaseTemplateField) and isinstance(
                            model_field,
                            (
                                TemplateHTMLStrictField,
                                TemplateCharField,
                                TemplateDecimalField,
                                TemplateRelationField,
                            ),
                        ):
                            if model_field.is_template_field(field):
                                list_fields["add"][field] = value
                            else:
                                fields[field] = value
                        elif isinstance(model_field, RelationListField):
                            list_fields["add"][field] = value
                        elif isinstance(model_field, RelationField):
                            fields[field] = value
                    fqid = fqid_from_collection_and_id(collection, entry["id"])
                    if fields or list_fields["add"]:
                        update_events.append(
                            self.build_event(
                                EventType.Update,
                                fqid,
                                fields=fields if fields else None,
                                list_fields=list_fields if list_fields["add"] else None,
                            )
                        )

        if pure_create_events:
            return events
        events.extend(update_events)

        # add meeting to committee/meeting_ids
        events.append(
            self.build_event(
                EventType.Update,
                fqid_from_collection_and_id("committee", meeting["committee_id"]),
                list_fields={"add": {"meeting_ids": [meeting_id]}, "remove": {}},
            )
        )

        # add meetings to organization if set in meeting
        adder: Dict[str, List[Union[int, str]]] = {}
        if meeting.get("is_active_in_organization_id"):
            adder["active_meeting_ids"] = [meeting_id]
        if meeting.get("template_for_organization_id"):
            adder["template_meeting_ids"] = [meeting_id]

        if adder:
            events.append(
                self.build_event(
                    EventType.Update,
                    ONE_ORGANIZATION_FQID,
                    list_fields={
                        "add": adder,
                        "remove": {},
                    },
                )
            )

        self.append_extra_events(events, instance["meeting"])

        # handle the calc fields.
        events.extend(self.handle_calculated_fields(instance))
        return events

    def append_extra_events(
        self, events: List[Event], json_data: Dict[str, Any]
    ) -> None:
        meeting = self.get_meeting_from_json(json_data)
        meeting_id = meeting["id"]

        # add request user to admin group of imported meeting.
        # Request user is added to group in meeting to organization/active_meeting_ids if not archived
        if (
            meeting.get("is_active_in_organization_id")
            and hasattr(self, "new_group_for_request_user")
            and self.new_group_for_request_user
        ):
            events.append(
                self.build_event(
                    EventType.Update,
                    fqid_from_collection_and_id("user", self.user_id),
                    list_fields={
                        "add": {
                            "group_$_ids": [str(meeting_id)],
                            f"group_${meeting_id}_ids": [
                                self.new_group_for_request_user
                            ],
                        },
                        "remove": {},
                    },
                )
            )

        # add new users to the organization.user_ids
        new_user_ids = []
        for user_entry in json_data.get("user", {}).values():
            if user_entry["id"] not in self.merge_user_map.values():
                new_user_ids.append(user_entry["id"])

        if new_user_ids:
            events.append(
                self.build_event(
                    EventType.Update,
                    ONE_ORGANIZATION_FQID,
                    list_fields={
                        "add": {
                            "user_ids": new_user_ids,
                        },
                        "remove": {},
                    },
                )
            )

    def handle_calculated_fields(self, instance: Dict[str, Any]) -> Iterable[Event]:
        regex = re.compile(
            r"^(user|committee)/(\d)*/(meeting_ids|committee_ids|user_ids)$"
        )
        json_data = instance["meeting"]
        relations: RelationUpdates = {}
        for collection in json_data:
            for entry in json_data[collection].values():
                model = model_registry[collection]()
                relations.update(
                    self.relation_manager.get_relation_updates(
                        model,
                        entry,
                        "meeting.import",
                        process_calculated_fields_only=True,
                    )
                )
        # Fix bug in calculated fields, see #1367
        entries_to_remove: List[str] = []
        for field, entry in relations.items():
            if regex.search(field):
                if entry["add"]:
                    entry["remove"] = []
                else:
                    entries_to_remove.append(field)
        for field in entries_to_remove:
            del relations[field]
        return self.handle_relation_updates_helper(relations)

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        """Returns the newly created id."""
        result = {"id": self.get_meeting_from_json(instance["meeting"])["id"]}
        if hasattr(self, "number_of_imported_users") and hasattr(
            self, "number_of_merged_users"
        ):
            result["number_of_imported_users"] = self.number_of_imported_users
            result["number_of_merged_users"] = self.number_of_merged_users
        return result

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if not has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            instance["committee_id"],
        ):
            raise MissingPermission(CommitteeManagementLevel.CAN_MANAGE)

    def create_import_create_events(
        self, instance: Dict[str, Any]
    ) -> List[CreateEvent]:
        json_data = instance["meeting"]
        import_create_events = []
        for collection in json_data:
            for entry in json_data[collection].values():
                # Necessary to remove None-values in event
                for k, v in list(entry.items()):
                    if v is None:
                        entry.pop(k)
                fqid = fqid_from_collection_and_id(collection, entry["id"])
                import_create_events.append(CreateEvent(str(fqid), entry))
        return import_create_events

    def migrate_data(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        1. Method checks instance for valid migration_index
        2. convert the instance json-data to datastore create events
        3. do the migrations
        4. get the migrated events from migration wrapper
        5. Convert only create events back to json-data
        """
        start_migration_index = instance.get("meeting", {}).pop(
            "_migration_index", None
        )
        if not start_migration_index or start_migration_index < 0:
            raise ActionException(
                f"The data must have a valid migration index, but '{start_migration_index}' is not valid!"
            )
        backend_migration_index = get_backend_migration_index()
        if backend_migration_index < start_migration_index:
            raise ActionException(
                f"Your data migration index '{start_migration_index}' is higher than the migration index of this backend '{backend_migration_index}'! Please, update your backend!"
            )
        if backend_migration_index > start_migration_index:
            migration_wrapper = MigrationWrapper(
                verbose=True,
                memory_only=True,
            )
            organization = self.datastore.get(
                ONE_ORGANIZATION_FQID,
                [
                    "committee_ids",
                    "active_meeting_ids",
                    "archived_meeting_ids",
                    "template_meeting_ids",
                    "resource_ids",
                    "organization_tag_ids",
                ],
                lock_result=False,
            )
            committee = self.datastore.get(
                fqid_from_collection_and_id("committee", instance["committee_id"]),
                ["meeting_ids"],
                lock_result=False,
            )
            models = {
                ONE_ORGANIZATION_FQID: organization,
                f"committee/{instance['committee_id']}": committee,
            }
            migration_wrapper.set_additional_data(
                self.create_import_create_events(instance),
                models,
                start_migration_index,
            )
            migration_wrapper.execute_command("finalize")
            migrated_events = migration_wrapper.get_migrated_events()
            instance = self.create_instance_from_migrated_events(
                instance, migrated_events
            )
        instance["meeting"]["_migration_index"] = backend_migration_index
        return instance

    def create_instance_from_migrated_events(
        self, instance: Dict[str, Any], migrated_events: List[BaseEvent]
    ) -> Dict[str, Any]:
        data: Dict[str, Dict] = defaultdict(dict)
        for event in migrated_events:
            collection, id_ = collection_and_id_from_fqid(event.fqid)
            str_id = str(id_)
            if event.type == CreateEvent.type:
                data[collection].update({str_id: event.data})
            elif event.type == UpdateEvent.type:
                data[collection][str_id].update(event.data)
            elif collection_from_fqid(event.fqid) in (
                "organization",
                "committee",
                "user",
            ):
                continue
            elif isinstance(event, ListUpdateEvent):
                if event.add:
                    for k, v in event.add.items():
                        data[collection][str_id][k] = list(
                            set(data[collection][str_id][k]).union(v)
                        )
                if event.remove:
                    for k, v in event.remove.items():
                        data[collection][str_id][k] = list(
                            set(data[collection][str_id][k]).difference(v)
                        )
            else:
                raise ActionException(
                    f"ActionType {event.type} for {event.fqid} not implemented!"
                )
        instance["meeting"] = data
        return instance
