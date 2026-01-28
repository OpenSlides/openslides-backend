import re
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from openslides_backend.action.actions.meeting.mixins import MeetingPermissionMixin
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.models.base import model_registry
from openslides_backend.models.checker import Checker, CheckException
from openslides_backend.models.fields import (
    BaseGenericRelationField,
    BaseRelationField,
    GenericRelationField,
    GenericRelationListField,
    OnDelete,
    RelationField,
    RelationListField,
)
from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permission_helper import (
    has_organization_management_level,
)
from openslides_backend.services.database.interface import GetManyRequest
from openslides_backend.shared.exceptions import ActionException, MissingPermission
from openslides_backend.shared.filters import FilterOperator, Or
from openslides_backend.shared.interfaces.event import EventType
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.shared.patterns import (
    KEYSEPARATOR,
    collection_and_id_from_fqid,
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from openslides_backend.shared.schema import models_map_object

from ....shared.interfaces.event import Event, ListFields, ListFieldsDict
from ....shared.util import (
    ALLOWED_HTML_TAGS_STRICT,
    ONE_ORGANIZATION_FQID,
    ONE_ORGANIZATION_ID,
    validate_html,
)
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.crypto import get_random_password
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement, ActionResults
from ..meeting_user.helper_mixin import MeetingUserHelperMixin
from ..motion.update import EXTENSION_REFERENCE_IDS_PATTERN
from ..user.user_mixins import LimitOfUserMixin, UsernameMixin


@register_action("meeting.import")
class MeetingImport(
    SingularActionMixin,
    LimitOfUserMixin,
    UsernameMixin,
    MeetingUserHelperMixin,
    MeetingPermissionMixin,
):
    """
    Action to import a meeting.
    """

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_default_schema(
        required_properties=["committee_id"],
        additional_required_fields={
            "meeting": {
                **models_map_object,
                "required": ["_migration_index", "meeting"],
            },
        },
        title="Import meeting",
        description="Import a meeting into the committee.",
    )

    def perform(
        self,
        action_data: ActionData,
        user_id: int,
        internal: bool = False,
        is_sub_call: bool = False,
    ) -> tuple[WriteRequest | None, ActionResults | None]:
        """
        Simplified entrypoint to perform the action.
        """
        self.user_id = user_id
        self.index = 0
        self.is_sub_call = is_sub_call

        # prefetch as much data as possible
        self.prefetch(action_data)

        action_data = self.get_updated_instances(action_data)
        instance = next(iter(action_data))
        self.validate_instance(instance)
        instance = self.preprocess_data(instance)
        try:
            self.check_permissions(instance)
        except MissingPermission as e:
            msg = f"You are not allowed to perform action {self.name}."
            e.message = msg + " " + e.message
            raise e
        instance = self.base_update_instance(instance)
        self.check_unique(next(iter(instance["meeting"]["meeting"].values())))
        self.events.extend(self.create_events(instance))
        write_request = self.build_write_request()
        result = [self.create_action_result_element(instance)]
        return (write_request, result)

    def check_permissions(self, instance: dict[str, Any]) -> None:
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.SUPERADMIN
        ):
            raise MissingPermission(OrganizationManagementLevel.SUPERADMIN)

    def prefetch(self, action_data: ActionData) -> None:
        requests = [
            GetManyRequest(
                "organization",
                [ONE_ORGANIZATION_ID],
                [
                    "active_meeting_ids",
                    "archived_meeting_ids",
                    "committee_ids",
                    "active_meeting_ids",
                    "archived_meeting_ids",
                    "template_meeting_ids",
                    "organization_tag_ids",
                    "limit_of_users",
                    "limit_of_meetings",
                    "user_ids",
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
            requests.append(
                GetManyRequest(
                    "user",
                    [self.user_id],
                    ["committee_ids", "committee_management_ids", "home_committee_id"],
                ),
            )
        self.datastore.get_many(requests, use_changed_models=False)

    def preprocess_data(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.check_one_meeting(instance)
        self.check_locked(instance)
        self.stash_gender_relations(instance)
        self.remove_not_allowed_fields(instance)
        self.set_committee_and_orga_relation(instance)
        self.check_data_migration_index(instance)
        self.unset_committee_and_orga_relation(instance)
        return instance

    def check_one_meeting(self, instance: dict[str, Any]) -> None:
        if len(instance["meeting"]["meeting"]) != 1:
            raise ActionException("Need exactly one meeting in meeting collection.")

    def check_unique(self, instance: dict[str, Any]) -> None:
        if instance.get("external_id"):
            self.check_unique_in_context(
                "external_id",
                instance["external_id"],
                "The external id of the meeting is not unique in the organization scope. Send a differing external id with this request.",
                instance["id"],
            )

    def check_locked(self, instance: dict[str, Any]) -> None:
        if list(instance["meeting"]["meeting"].values())[0].get("locked_from_inside"):
            raise ActionException("Cannot import a locked meeting.")

    def stash_gender_relations(self, instance: dict[str, Any]) -> None:
        # The Checker will not allow the gender to have or not to have an orga relation. So we need to circumvent it.
        self.user_id_to_gender = {}
        users = instance["meeting"].get("user", {})
        for user in users.values():
            if gender := user.pop("gender", None):
                self.user_id_to_gender[user["id"]] = gender

    def remove_not_allowed_fields(self, instance: dict[str, Any]) -> None:
        json_data = instance["meeting"]

        for user in json_data.get("user", {}).values():
            user.pop("organization_management_level", None)
            user.pop("committee_ids", None)
            user.pop("committee_management_ids", None)
            user.pop("home_committee_id", None)
        self.get_meeting_from_json(json_data).pop("organization_tag_ids", None)
        json_data.pop("action_worker", None)
        json_data.pop("import_preview", None)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        meeting_json = instance["meeting"]
        self.generate_merge_user_map(meeting_json)
        self.check_usernames_and_generate_new_ones(meeting_json)
        active_new_users_in_json = sum(
            bool(meeting_json["user"][key].get("is_active"))
            and int(key) not in self.merge_user_map
            for key in meeting_json.get("user", [])
        )
        self.check_limit_of_user(active_new_users_in_json)

        # save blobs from mediafiles
        self.mediadata = []
        for entry in meeting_json.get("mediafile", {}).values():
            # mediafiles have "blob": None
            if blob := entry.pop("blob", None):
                self.mediadata.append((blob, entry["id"], entry["mimetype"]))

        # remove None values from amendment paragraph, os3 exports have those.
        # and validate the html.
        for entry in meeting_json.get("motion", {}).values():
            if "amendment_paragraphs" in entry and isinstance(
                entry["amendment_paragraphs"], dict
            ):
                res = {}
                for key, html in entry["amendment_paragraphs"].items():
                    if html is None:
                        continue
                    res[key] = validate_html(html, ALLOWED_HTML_TAGS_STRICT)
                entry["amendment_paragraphs"] = res

        models_to_remove: set[tuple[str, int]] = set()
        for mm_id, mmediafile in meeting_json.get("meeting_mediafile", {}).items():
            if str(mmediafile["mediafile_id"]) not in meeting_json.get("mediafile", {}):
                self.prepare_model_removal(
                    "meeting_mediafile",
                    mm_id,
                    mmediafile,
                    meeting_json,
                    models_to_remove,
                )
        for collection, id_ in models_to_remove:
            del meeting_json[collection][str(id_)]

        # check datavalidation
        checker = Checker(
            data=meeting_json,
            mode="external",
            repair=True,
            fields_to_remove={
                "meeting": [
                    "forwarded_motion_ids",
                ],
                "motion": [
                    "origin_id",
                    "derived_motion_ids",
                    "all_origin_ids",
                    "all_derived_motion_ids",
                    "origin_meeting_id",
                ],
                "user": [
                    "password",
                    "default_password",
                    "last_email_sent",
                    "last_login",
                    "committee_ids",
                ],
            },
        )
        try:
            checker.run_check()
        except CheckException as ce:
            raise ActionException(str(ce))
        self.allowed_collections = checker.allowed_collections

        self.check_limit_of_meetings()
        self.update_meeting_and_users(instance)

        # replace ids in the meeting_json
        self.create_replace_map(meeting_json)
        self.replace_fields(instance)
        meeting_json = instance["meeting"]
        self.update_admin_group(meeting_json)
        self.upload_mediadata()
        self.handle_gender_string(instance)
        return instance

    def empty_if_none(self, value: str | None) -> str:
        if value is None:
            return ""
        return value

    def get_user_key(self, user_values: dict[str, Any]) -> tuple[str, str, str, str]:
        return (
            self.empty_if_none(user_values.get("username")),
            self.empty_if_none(user_values.get("first_name")),
            self.empty_if_none(user_values.get("last_name")),
            self.empty_if_none(user_values.get("email")).lower(),
        )

    def generate_merge_user_map(self, json_data: dict[str, Any]) -> None:
        if len(users := json_data.get("user", {})):
            for entry in users.values():
                entry["username"] = entry["username"].strip()
            filter_ = Or(
                *[
                    FilterOperator("username", "=", entry["username"])
                    for entry in users.values()
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
                for key, values in users.items()
                if filtered_users_dict.get(self.get_user_key(values)) is not None
            }
        else:
            self.merge_user_map = {}
        self.number_of_imported_users = len(users)
        self.number_of_merged_users = len(self.merge_user_map)

    def check_usernames_and_generate_new_ones(self, json_data: dict[str, Any]) -> None:
        user_entries = [
            entry
            for entry in json_data.get("user", {}).values()
            if int(entry["id"]) not in self.merge_user_map
        ]
        usernames: list[str] = [entry["username"] for entry in user_entries]
        new_usernames = self.generate_usernames(usernames)

        for entry, username in zip(user_entries, new_usernames):
            entry["username"] = username

    def handle_gender_string(self, instance: dict[str, Any]) -> None:
        for user_id in list(self.user_id_to_gender.keys()):
            if user_id in self.merge_user_map:
                del self.user_id_to_gender[user_id]
        genders = self.datastore.get_all("gender", ["id", "name"], lock_result=True)
        gender_dict = {gender.get("name", ""): gender for gender in genders.values()}
        new_genders = list(
            {value for value in self.user_id_to_gender.values()}.difference(gender_dict)
        )
        if new_genders:
            new_genders.sort()  # fix order for tests
            new_gender_ids = self.datastore.reserve_ids("gender", len(new_genders))
            new_gender_dict = {
                new_gender: {
                    "id": new_gender_id,
                    "name": new_gender,
                    "meta_new": True,
                    "organization_id": ONE_ORGANIZATION_ID,
                }
                for new_gender, new_gender_id in zip(new_genders, new_gender_ids)
            }
            gender_dict.update(new_gender_dict)
        instance["meeting"]["gender"] = {
            str(gender["id"]): gender for gender in gender_dict.values()
        }
        for user_id, gender in self.user_id_to_gender.items():
            gender_id = gender_dict[gender]["id"]
            replace_user_id = self.replace_map["user"][user_id]
            instance["meeting"]["user"][str(replace_user_id)]["gender_id"] = gender_id
            try:
                instance["meeting"]["gender"][str(gender_id)]["user_ids"].append(
                    replace_user_id
                )
            except KeyError:
                instance["meeting"]["gender"][str(gender_id)]["user_ids"] = [
                    replace_user_id
                ]

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

    def set_committee_and_orga_relation(self, instance: dict[str, Any]) -> None:
        json_data = instance["meeting"]
        meeting = self.get_meeting_from_json(json_data)
        meeting["committee_id"] = instance["committee_id"]
        meeting["is_active_in_organization_id"] = ONE_ORGANIZATION_ID

    def unset_committee_and_orga_relation(self, instance: dict[str, Any]) -> None:
        json_data = instance["meeting"]
        meeting = self.get_meeting_from_json(json_data)
        meeting["committee_id"] = None
        meeting["is_active_in_organization_id"] = None

    def update_meeting_and_users(self, instance: dict[str, Any]) -> None:
        # update committee_id and is_active_in_organization_id
        json_data = instance["meeting"]
        meeting = self.get_meeting_from_json(json_data)
        meeting["committee_id"] = instance["committee_id"]
        meeting["is_active_in_organization_id"] = ONE_ORGANIZATION_ID

        # generate passwords
        for entry in json_data.get("user", {}).values():
            if entry["id"] not in self.merge_user_map:
                entry["default_password"] = get_random_password()
                entry["password"] = self.auth.hash(entry["default_password"])

        # set enable_anonymous
        meeting["enable_anonymous"] = False

        # set imported_at
        meeting["imported_at"] = datetime.now()

    def get_meeting_from_json(self, json_data: Any) -> Any:
        """
        Small helper to retrieve the one and only meeting object from the import data.
        """
        key = next(iter(json_data["meeting"]))
        return json_data["meeting"][key]

    def create_replace_map(self, json_data: dict[str, Any]) -> None:
        replace_map: dict[str, dict[int, int]] = defaultdict(dict)
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

    def replace_fields(self, instance: dict[str, Any]) -> None:
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
        entry: dict[str, Any],
        field: str,
    ) -> None:
        model_field = model_registry[collection].try_get_field(field)
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
            if isinstance(model_field, RelationField):
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

    def update_admin_group(self, data_json: dict[str, Any]) -> None:
        """adds the request user to the admin group of the imported meeting"""
        meeting = self.get_meeting_from_json(data_json)
        admin_group_id = meeting.get("admin_group_id")
        group = data_json.get("group", {}).get(str(admin_group_id))
        if not group:
            raise ActionException(
                "Imported meeting has no AdminGroup to assign to request user"
            )
        new_meeting_user_id: int | None = None
        for meeting_user_id, meeting_user in data_json.get("meeting_user", {}).items():
            if meeting_user.get("user_id") == self.user_id:
                new_meeting_user_id = int(meeting_user_id)
                if new_meeting_user_id not in (group.get("meeting_user_ids", {}) or {}):
                    data_json["meeting_user"][meeting_user_id]["group_ids"] = (
                        data_json["meeting_user"][meeting_user_id].get("group_ids")
                        or []
                    ) + [admin_group_id]
                break
        if not new_meeting_user_id:
            new_meeting_user_id = self.datastore.reserve_id("meeting_user")
            data_json["meeting_user"] = data_json.get("meeting_user", {})
            data_json["meeting_user"][str(new_meeting_user_id)] = {
                "id": new_meeting_user_id,
                "meeting_id": meeting["id"],
                "user_id": self.user_id,
                "group_ids": [admin_group_id],
                "meta_new": True,
            }
            if not meeting.get("meeting_user_ids"):
                meeting["meeting_user_ids"] = list()
            meeting["meeting_user_ids"].append(new_meeting_user_id)
            request_user = self.datastore.get(
                fqid_user := fqid_from_collection_and_id("user", self.user_id),
                [
                    "id",
                    "meeting_user_ids",
                    "committee_management_ids",
                    "committee_ids",
                    "home_committee_id",
                ],
            )
            request_user.pop("meta_position", None)
            request_user["meeting_user_ids"] = (
                request_user.get("meeting_user_ids") or []
            ) + [new_meeting_user_id]
            data_json["user"] = data_json.get("user", {})
            data_json["user"][str(self.user_id)] = request_user
            self.replace_map["user"].update(
                {0: self.user_id}
            )  # create a user.update event
            self.replace_map["meeting_user"].update(
                {0: new_meeting_user_id}
            )  # create a meeting_user.update event
            self.datastore.apply_changed_model(fqid_user, request_user)
            self.datastore.apply_changed_model(
                fqid_from_collection_and_id("meeting_user", new_meeting_user_id),
                data_json["meeting_user"][str(new_meeting_user_id)],
            )
        if new_meeting_user_id not in (
            meeting_user_ids := data_json["group"][str(admin_group_id)].get(
                "meeting_user_ids", []
            )
        ):
            meeting_user_ids.append(new_meeting_user_id)
            data_json["group"][str(admin_group_id)][
                "meeting_user_ids"
            ] = meeting_user_ids

    def upload_mediadata(self) -> None:
        for blob, id_, mimetype in self.mediadata:
            replaced_id = self.replace_map["mediafile"][id_]
            self.media.upload_mediafile(blob, replaced_id, mimetype)

    def create_events(
        self, instance: dict[str, Any], pure_create_events: bool = False
    ) -> Iterable[Event]:
        """Be careful, this method is also used by meeting.clone!"""
        json_data = instance["meeting"]
        meeting = self.get_meeting_from_json(json_data)
        meeting_id = meeting["id"]
        events = []
        update_events = []
        add_genders_to_organisation = []
        for collection in json_data:
            for entry in json_data[collection].values():
                fqid = fqid_from_collection_and_id(collection, entry["id"])
                meta_new = entry.pop("meta_new", None)
                if meta_new:
                    if collection == "gender":
                        add_genders_to_organisation.append(entry["id"])
                    events.append(
                        self.build_event(
                            EventType.Create,
                            fqid,
                            entry,
                        )
                    )
                elif collection in ["user", "gender"] or (
                    collection == "mediafile"
                    and getattr(self, "action_name", None) == "clone"
                ):
                    list_fields: ListFields = {"add": {}, "remove": {}}
                    for field, value in entry.items():
                        model_field = model_registry[collection]().try_get_field(field)
                        if isinstance(model_field, RelationListField):
                            list_fields["add"][field] = value
                    if list_fields["add"]:
                        update_events.append(
                            self.build_event(
                                EventType.Update,
                                fqid,
                                fields=None,
                                list_fields=list_fields,
                            )
                        )
                elif collection == "meeting_user":
                    update_events.append(
                        self.build_event(
                            EventType.Update,
                            fqid,
                            fields=entry,
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

        # add meetings to organization if set in meeting, also genders if new created
        adder: ListFieldsDict = {}
        if meeting.get("is_active_in_organization_id"):
            adder["active_meeting_ids"] = [meeting_id]
        if meeting.get("template_for_organization_id"):
            adder["template_meeting_ids"] = [meeting_id]
        if add_genders_to_organisation:
            adder["gender_ids"] = add_genders_to_organisation

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
        return events

    def append_extra_events(
        self, events: list[Event], json_data: dict[str, Any]
    ) -> None:
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

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        """Returns the newly created id."""
        result = {"id": self.get_meeting_from_json(instance["meeting"])["id"]}
        if hasattr(self, "number_of_imported_users") and hasattr(
            self, "number_of_merged_users"
        ):
            result["number_of_imported_users"] = self.number_of_imported_users
            result["number_of_merged_users"] = self.number_of_merged_users
        return result

    def check_data_migration_index(self, instance: dict[str, Any]) -> None:
        """
        Check for valid migration index.
        """
        start_migration_index = instance["meeting"].pop("_migration_index")
        backend_migration_index = MigrationHelper.get_backend_migration_index()
        if backend_migration_index < start_migration_index:
            raise ActionException(
                f"Your data migration index '{start_migration_index}' is higher than the migration index of this backend '{backend_migration_index}'! Please, update your backend!"
            )
        if backend_migration_index > start_migration_index:
            raise ActionException(
                f"Your data migration index '{start_migration_index}' is lower than the migration index of this backend '{backend_migration_index}'! Please, use a more recent file!"
            )

    def prepare_model_removal(
        self,
        collection: str,
        model_id: int,
        content: dict[str, Any],
        meeting_json: Any,
        models_to_remove: set[tuple[str, int]] = set(),
    ) -> None:
        models_to_remove.add((collection, model_id))
        for field_name in content:
            if isinstance(
                (relation_field := model_registry[collection]().get_field(field_name)),
                BaseRelationField,
            ) and (to_remove := content.get(field_name)):
                if isinstance(to_remove, list):
                    for target in to_remove:
                        self.remove_back_relation(
                            int(model_id),
                            collection,
                            relation_field,
                            target,
                            meeting_json,
                            models_to_remove,
                        )
                else:
                    self.remove_back_relation(
                        int(model_id),
                        collection,
                        relation_field,
                        to_remove,
                        meeting_json,
                        models_to_remove,
                    )

    def remove_back_relation(
        self,
        model_id: int,
        model_collection: str,
        relation_field: BaseRelationField,
        to_remove: str | int,
        meeting_json: Any,
        models_to_remove: set[tuple[str, int]],
    ) -> None:
        if isinstance(relation_field, BaseGenericRelationField):
            assert isinstance(to_remove, str)
            coll = collection_from_fqid(to_remove)
            id_ = str(id_from_fqid(to_remove))
        else:
            assert isinstance(to_remove, int)
            coll = list(relation_field.to.keys())[0]
            id_ = str(to_remove)
        if (coll, id_) not in models_to_remove and id_ in meeting_json.get(coll, {}):
            if relation_field.on_delete == OnDelete.CASCADE:
                self.prepare_model_removal(
                    coll,
                    int(id_),
                    meeting_json[coll][id_],
                    meeting_json,
                    models_to_remove,
                )
            elif meeting_json[coll][id_].get(relation_field.to[coll]):
                if isinstance(meeting_json[coll][id_][relation_field.to[coll]], list):
                    meeting_json[coll][id_][relation_field.to[coll]] = [
                        other_mm_id
                        for other_mm_id in meeting_json[coll][id_][
                            relation_field.to[coll]
                        ]
                        if other_mm_id != model_id
                        and other_mm_id
                        != fqid_from_collection_and_id(model_collection, model_id)
                    ]
                else:
                    assert meeting_json[coll][id_][
                        relation_field.to[coll]
                    ] == model_id or meeting_json[coll][id_][
                        relation_field.to[coll]
                    ] == fqid_from_collection_and_id(
                        model_collection, model_id
                    )
                    del meeting_json[coll][id_][relation_field.to[coll]]
