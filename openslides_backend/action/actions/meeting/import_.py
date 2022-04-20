import time
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from datastore.migrations import BaseEvent, CreateEvent
from datastore.shared.util import collection_and_id_from_fqid

from migrations import get_backend_migration_index
from migrations.migrate import MigrationWrapper

from ....models.base import model_registry
from ....models.checker import Checker, CheckException
from ....models.fields import (
    BaseGenericRelationField,
    BaseRelationField,
    BaseTemplateField,
    GenericRelationField,
    GenericRelationListField,
    RelationField,
    RelationListField,
)
from ....models.models import Meeting
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import has_committee_management_level
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.filters import FilterOperator
from ....shared.interfaces.event import EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...action import Action, RelationUpdates
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.crypto import get_random_string
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement, ActionResults
from ..motion.update import RECOMMENDATION_EXTENSION_REFERENCE_IDS_PATTERN
from ..user.user_mixin import LimitOfUserMixin

ONE_ORGANIZATION = 1


@register_action("meeting.import")
class MeetingImport(SingularActionMixin, LimitOfUserMixin, Action):
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
        action_data = self.get_updated_instances(action_data)
        instance = next(iter(action_data))

        if self.name == "meeting.import":
            self.check_one_meeting(instance)
            self.check_not_allowed_fields(instance)
            self.set_committee_and_orga_relation(instance)
            instance = self.migrate_data(instance)
            self.unset_committee_and_orga_relation(instance)
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

    def check_one_meeting(self, instance: Dict[str, Any]) -> None:
        meeting_json = instance.get("meeting", {})
        if not len(meeting_json.get("meeting", {}).values()) == 1:
            raise ActionException("Need exact one meeting in meeting collection.")

    def check_not_allowed_fields(self, instance: Dict[str, Any]) -> None:
        json_data = instance["meeting"]
        for user in json_data.get("user", {}).values():
            if (
                OrganizationManagementLevel(
                    user.get("organization_management_level", "no_right")
                )
                > OrganizationManagementLevel.NO_RIGHT
            ):
                raise ActionException(
                    "Imported user may not have OrganizationManagementLevel rights!"
                )
            if user.get("committee_$_management_level"):
                raise ActionException(
                    "Imported user may not have CommitteeManagementLevel rights!"
                )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_json = instance["meeting"]
        self.check_usernames_and_generate_new_ones(meeting_json)
        active_user_in_json = len(
            [
                key
                for key in meeting_json.get("user", [])
                if meeting_json["user"][key].get("is_active")
            ]
        )
        self.check_limit_of_user(active_user_in_json)

        # save blobs from mediafiles
        self.mediadata = []
        for entry in meeting_json.get("mediafile", {}).values():
            # mediafiles have "blob": None
            if blob := entry.pop("blob", None):
                self.mediadata.append((blob, entry["id"], entry["mimetype"]))

        for entry in meeting_json.get("motion", {}).values():
            to_remove = set()
            for paragraph in entry.get("amendment_paragraph_$", []):
                if (entry.get(fname := "amendment_paragraph_$" + paragraph)) is None:
                    to_remove.add(paragraph)
                    entry.pop(fname, None)
            if to_remove:
                entry["amendment_paragraph_$"] = list(
                    set(entry["amendment_paragraph_$"]) - to_remove
                )

        # check datavalidation
        checker = Checker(data=meeting_json, mode="external")
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

    def check_usernames_and_generate_new_ones(self, json_data: Dict[str, Any]) -> None:
        used_usernames = set()
        for entry in json_data.get("user", {}).values():
            is_username_unique = False
            template_username = entry["username"].replace(" ", "")
            count = 1
            while not is_username_unique:
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
                is_username_unique = True
            used_usernames.add(entry["username"])

    def check_limit_of_meetings(
        self, text: str = "import", text2: str = "active "
    ) -> None:
        organization = self.datastore.get(
            FullQualifiedId(Collection("organization"), ONE_ORGANIZATION),
            ["active_meeting_ids", "limit_of_meetings"],
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
        meeting["is_active_in_organization_id"] = ONE_ORGANIZATION

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
        meeting["is_active_in_organization_id"] = ONE_ORGANIZATION

        # generate passwords
        for entry in json_data["user"].values():
            entry["password"] = self.auth.hash(get_random_string(10))

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
            if not json_data[collection]:
                continue
            new_ids = self.datastore.reserve_ids(
                Collection(collection), len(json_data[collection])
            )
            for entry, new_id in zip(json_data[collection].values(), new_ids):
                replace_map[collection][entry["id"]] = new_id
        self.replace_map = replace_map

    def replace_fields(self, instance: Dict[str, Any]) -> None:
        json_data = instance["meeting"]
        new_json_data = {}
        for collection in json_data:
            new_collection = {}
            coll_class = Collection(collection)
            for entry in json_data[collection].values():
                for field in list(entry.keys()):
                    self.replace_field_ids(collection, entry, field)
                new_collection[str(entry["id"])] = entry
                entry["meta_new"] = True
                self.datastore.apply_changed_model(
                    FullQualifiedId(coll_class, entry["id"]), entry
                )
            new_json_data[collection] = new_collection
        instance["meeting"] = new_json_data

    def replace_field_ids(
        self,
        collection: str,
        entry: Dict[str, Any],
        field: str,
    ) -> None:

        model_field = model_registry[Collection(collection)]().try_get_field(field)
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
                target_collections = [k.collection for k in model_field.to.keys()]
            if all(c not in self.allowed_collections for c in target_collections):
                return
        if field == "id":
            entry["id"] = self.replace_map[collection][entry["id"]]
        elif (
            collection == "meeting"
            and field == "user_ids"
            and "user" in self.allowed_collections
        ):
            entry[field] = [
                self.replace_map["user"][id_] for id_ in entry.get(field) or []
            ]
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
                new_id_ = self.replace_map[
                    model_field.replacement_collection.collection
                ][id_]
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
            group["user_ids"].insert(0, self.user_id)
        else:
            group["user_ids"] = [self.user_id]
        self.new_group_for_request_user = admin_group_id

    def upload_mediadata(self) -> None:
        for blob, id_, mimetype in self.mediadata:
            replaced_id = self.replace_map["mediafile"][id_]
            self.media.upload_mediafile(blob, replaced_id, mimetype)

    def create_write_requests(
        self, instance: Dict[str, Any], pure_create_requests: bool = False
    ) -> Iterable[WriteRequest]:
        """be carefull, this method is also used by meeting.clone action"""
        json_data = instance["meeting"]
        meeting = self.get_meeting_from_json(json_data)
        meeting_id = meeting["id"]
        write_requests = []
        for collection in json_data:
            for entry in json_data[collection].values():
                entry.pop("meta_new", None)
                fqid = FullQualifiedId(Collection(collection), entry["id"])
                write_requests.append(
                    self.build_write_request(
                        EventType.Create,
                        fqid,
                        f"import meeting {meeting_id}",
                        entry,
                    )
                )
        if pure_create_requests:
            return write_requests

        # add meeting to committee/meeting_ids
        write_requests.append(
            self.build_write_request(
                EventType.Update,
                FullQualifiedId(Collection("committee"), meeting["committee_id"]),
                f"import meeting {meeting_id}",
                None,
                {"add": {"meeting_ids": [meeting_id]}, "remove": {}},
            )
        )

        # add meeting to organization/active_meeting_ids if not archived
        if meeting.get("is_active_in_organization_id"):
            write_requests.append(
                self.build_write_request(
                    EventType.Update,
                    FullQualifiedId(Collection("organization"), 1),
                    f"import meeting {meeting_id}",
                    None,
                    {"add": {"active_meeting_ids": [meeting_id]}, "remove": {}},
                )
            )

        self.append_extra_write_requests(write_requests, instance["meeting"])

        # handle the calc fields.
        write_requests.extend(list(self.handle_calculated_fields(instance)))
        return write_requests

    def append_extra_write_requests(
        self, write_requests: List[WriteRequest], json_data: Dict[str, Any]
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
            write_requests.append(
                self.build_write_request(
                    EventType.Update,
                    FullQualifiedId(Collection("user"), self.user_id),
                    f"import meeting {meeting_id}",
                    None,
                    {
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

    def handle_calculated_fields(
        self, instance: Dict[str, Any]
    ) -> Iterable[WriteRequest]:
        json_data = instance["meeting"]
        relations: RelationUpdates = {}
        for collection in json_data:
            for entry in json_data[collection].values():
                model = model_registry[Collection(collection)]()
                relations.update(
                    self.relation_manager.get_relation_updates(
                        model,
                        entry,
                        "meeting.import",
                        process_calculated_fields_only=True,
                    )
                )
        return self.handle_relation_updates_helper(relations)

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        """Returns the newly created id."""
        return {"id": self.get_meeting_from_json(instance["meeting"])["id"]}

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
                fqid = FullQualifiedId(Collection(collection), entry["id"])
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
                FullQualifiedId(Collection("organization"), ONE_ORGANIZATION),
                [
                    "committee_ids",
                    "active_meeting_ids",
                    "archived_meeting_ids",
                    "template_meeting_ids",
                    "resource_ids",
                    "organization_tag_ids",
                ],
            )
            committee = self.datastore.get(
                FullQualifiedId(Collection("committee"), instance["committee_id"]),
                ["meeting_ids"],
            )
            models = {
                f"organization/{ONE_ORGANIZATION}": organization,
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
        return instance

    def create_instance_from_migrated_events(
        self, instance: Dict[str, Any], migrated_events: List[BaseEvent]
    ) -> Dict[str, Any]:
        data: Dict[str, Dict] = defaultdict(dict)
        for event in migrated_events:
            collection, id_ = collection_and_id_from_fqid(event.fqid)
            if event.type == CreateEvent.type:
                data[collection].update({str(id_): event.data})
            elif event.fqid.split("/")[0] in ("organization", "committee", "user"):
                continue
            else:
                raise ActionException(
                    f"ActionType {event.type} for {event.fqid} not implemented!"
                )
        instance["meeting"] = data
        return instance
