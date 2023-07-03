import time
from typing import Any, Dict, List

from openslides_backend.models.checker import (
    Checker,
    CheckException,
    external_motion_fields,
)
from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import CommitteeManagementLevel
from openslides_backend.permissions.permission_helper import (
    has_committee_management_level,
)
from openslides_backend.services.datastore.interface import GetManyRequest
from openslides_backend.shared.exceptions import ActionException, PermissionDenied
from openslides_backend.shared.interfaces.event import Event, EventType
from openslides_backend.shared.patterns import (
    FullQualifiedId,
    fqid_from_collection_and_id,
)
from openslides_backend.shared.schema import id_list_schema, required_id_schema

from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .export_helper import export_meeting
from .import_ import ONE_ORGANIZATION_ID, MeetingImport

updatable_fields = [
    "committee_id",
    "welcome_title",
    "description",
    "start_time",
    "end_time",
    "location",
    "organization_tag_ids",
    "name",
]


@register_action("meeting.clone")
class MeetingClone(MeetingImport):
    """
    Action to clone a meeting.
    """

    schema = DefaultSchema(Meeting()).get_default_schema(
        optional_properties=updatable_fields,
        additional_required_fields={"meeting_id": required_id_schema},
        additional_optional_fields={
            "user_ids": id_list_schema,
            "admin_ids": id_list_schema,
            "set_as_template": {"type": "boolean"},
        },
    )

    def prefetch(self, action_data: ActionData) -> None:
        self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list({instance["meeting_id"] for instance in action_data}),
                    ["committee_id"],
                ),
                GetManyRequest(
                    "organization",
                    [ONE_ORGANIZATION_ID],
                    [
                        "active_meeting_ids",
                        "archived_meeting_ids",
                        "limit_of_meetings",
                    ],
                ),
            ],
            use_changed_models=False,
        )

    def preprocess_data(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # overwrite method from meeting.import
        return instance

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_json = export_meeting(self.datastore, instance["meeting_id"])
        instance["meeting"] = meeting_json
        self.additional_user_ids = instance.pop("user_ids", None) or []
        self.additional_admin_ids = instance.pop("admin_ids", None) or []
        set_as_template = instance.pop("set_as_template", False)

        # needs an empty map for superclass code
        self.merge_user_map = {
            int(id_): int(id_) for id_ in meeting_json.get("user", {})
        }
        self.number_of_imported_users = len(self.merge_user_map)
        self.number_of_merged_users = len(self.merge_user_map)

        # checks if the meeting is correct
        self.check_one_meeting(instance)
        meeting = self.get_meeting_from_json(meeting_json)

        if committee_id := instance.get("committee_id"):
            meeting["committee_id"] = committee_id

        # pre update the meeting
        if "name" not in instance:
            suffix = " - Copy"
            max_length = Meeting().name.constraints.get("maxLength")
            old_name = meeting["name"]
            if max_length and len(old_name) + len(suffix) > max_length:
                meeting["name"] = (
                    old_name[: max_length - len(suffix) - 3] + "..." + suffix
                )
            else:
                meeting["name"] = old_name + suffix

        for field in updatable_fields:
            if field in instance:
                meeting[field] = instance.pop(field)

        # check datavalidation
        checker = Checker(
            data=meeting_json,
            mode="internal",
            repair=True,
            fields_to_remove={
                "motion": external_motion_fields,
            },
        )
        try:
            checker.run_check()
        except CheckException as ce:
            raise ActionException(str(ce))
        self.allowed_collections = checker.allowed_collections

        # set active
        meeting["is_active_in_organization_id"] = ONE_ORGANIZATION_ID
        meeting["template_for_organization_id"] = (
            ONE_ORGANIZATION_ID if set_as_template else None
        )

        # check limit of meetings
        self.check_limit_of_meetings(
            text="clone",
            text2="",
        )
        # set imported_at
        meeting["imported_at"] = round(time.time())

        # replace ids in the meeting_json
        self.create_replace_map(meeting_json)
        self.duplicate_mediafiles(meeting_json)
        self.replace_fields(instance)

        if self.additional_user_ids:
            default_group_id = self.get_meeting_from_json(instance["meeting"]).get(
                "default_group_id"
            )
            self._update_default_and_admin_group(
                default_group_id, instance, self.additional_user_ids
            )

        if self.additional_admin_ids:
            admin_group_id = self.get_meeting_from_json(instance["meeting"]).get(
                "admin_group_id"
            )
            self._update_default_and_admin_group(
                admin_group_id, instance, self.additional_admin_ids
            )
        return instance

    @staticmethod
    def _update_default_and_admin_group(
        group_id: int, instance: Dict[str, Any], additional_user_ids: List[int]
    ) -> None:
        for entry in instance["meeting"].get("group", {}).values():
            if entry["id"] == group_id:
                user_ids = set(entry.get("user_ids", set()) or set())
                user_ids.update(additional_user_ids)
                entry["user_ids"] = list(user_ids)

    def duplicate_mediafiles(self, json_data: Dict[str, Any]) -> None:
        for mediafile_id in json_data["mediafile"]:
            mediafile = json_data["mediafile"][mediafile_id]
            if not mediafile.get("is_directory"):
                self.media.duplicate_mediafile(
                    mediafile["id"], self.replace_map["mediafile"][mediafile["id"]]
                )

    def append_extra_events(
        self, events: List[Event], json_data: Dict[str, Any]
    ) -> None:
        meeting_id = self.get_meeting_from_json(json_data)["id"]
        for model in json_data["group"].values():
            if model.get("user_ids"):
                for user_id in model.get("user_ids"):
                    if user_id in self.additional_user_ids or self.additional_admin_ids:
                        events.append(
                            self.build_event_helper(
                                fqid_from_collection_and_id("user", user_id),
                                meeting_id,
                                "group_$_ids",
                                model["id"],
                            )
                        )
        if organization_tag_ids := self.get_meeting_from_json(json_data).get(
            "organization_tag_ids"
        ):
            meeting_fqid = fqid_from_collection_and_id("meeting", meeting_id)
            for organization_tag_id in organization_tag_ids:
                events.append(
                    self.build_event(
                        EventType.Update,
                        fqid_from_collection_and_id(
                            "organization_tag", organization_tag_id
                        ),
                        list_fields={
                            "add": {
                                "tagged_ids": [meeting_fqid],
                            },
                            "remove": {},
                        },
                    ),
                )

    def field_with_meeting(self, field: str, meeting_id: int) -> str:
        front, back = field.split("$")
        return f"{front}${meeting_id}{back}"

    def build_event_helper(
        self,
        fqid: FullQualifiedId,
        meeting_id: int,
        field_template: str,
        model_id: int,
    ) -> Event:
        return self.build_event(
            EventType.Update,
            fqid,
            list_fields={
                "add": {
                    field_template: [str(meeting_id)],
                    self.field_with_meeting(field_template, meeting_id): [model_id],
                },
                "remove": {},
            },
        )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if instance.get("committee_id"):
            committee_id = instance["committee_id"]
        else:
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", instance["meeting_id"]),
                ["committee_id"],
                lock_result=False,
                use_changed_models=False,
            )
            committee_id = meeting["committee_id"]
        if not has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            committee_id,
        ):
            raise PermissionDenied(
                f"Missing {CommitteeManagementLevel.CAN_MANAGE.get_verbose_type()}: {CommitteeManagementLevel.CAN_MANAGE} for committee {committee_id}"
            )
