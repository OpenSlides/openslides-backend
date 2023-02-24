import time
from typing import Any, Dict, List

from openslides_backend.models.checker import Checker, CheckException
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
from openslides_backend.shared.schema import id_list_schema

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
        additional_required_fields={"meeting_id": {"type": "integer"}},
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
        """
        Temporarely, because meeting.clone has _model and _collection attributes
        """
        underscore_keys = tuple(key for key in instance.keys() if key[0] == "_")
        [instance.pop(key) for key in underscore_keys]
        return instance

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_json = export_meeting(self.datastore, instance["meeting_id"])
        instance["meeting"] = meeting_json
        additional_user_ids = instance.pop("user_ids", None) or []
        additional_admin_ids = instance.pop("admin_ids", None) or []
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

        if (committee_id := instance.get("committee_id")) and committee_id != meeting[
            "committee_id"
        ]:
            meeting["committee_id"] = committee_id

        # pre update the meeting
        name_set = False
        for field in updatable_fields:
            if field in instance:
                if field == "name":
                    name_set = True
                value = instance.pop(field)
                meeting[field] = value
        if not name_set:
            meeting["name"] = meeting.get("name", "") + " - Copy"

        # reset mediafile/attachment_ids to [] if None.
        for mediafile_id in instance["meeting"].get("mediafile", []):
            if (
                instance["meeting"]["mediafile"][mediafile_id].get("attachment_ids")
                is None
            ):
                instance["meeting"]["mediafile"][mediafile_id]["attachment_ids"] = []

        # check datavalidation
        checker = Checker(
            data=meeting_json,
            mode="internal",
            repair=True,
            fields_to_remove={
                "motion": [
                    "origin_id",
                    "derived_motion_ids",
                    "all_origin_id",
                    "all_derived_motion_ids",
                ]
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

        meeting = self.get_meeting_from_json(meeting_json)
        meeting_id = meeting["id"]
        meeting_users_in_instance = instance["meeting"]["meeting_user"]
        if additional_user_ids:
            default_group_id = meeting.get("default_group_id")
            group_in_instance = instance["meeting"]["group"][str(default_group_id)]
            self._update_default_and_admin_group(
                group_in_instance,
                meeting_users_in_instance,
                additional_user_ids,
                meeting_id,
            )

        if additional_admin_ids:
            admin_group_id = meeting.get("admin_group_id")
            group_in_instance = instance["meeting"]["group"][str(admin_group_id)]
            self._update_default_and_admin_group(
                group_in_instance,
                meeting_users_in_instance,
                additional_admin_ids,
                meeting_id,
            )
        return instance

    def _update_default_and_admin_group(
        self,
        group_in_instance: Dict[str, Any],
        meeting_users_in_instance: Dict[str, Any],
        additional_user_ids: List[int],
        meeting_id: int,
    ) -> None:
        additional_meeting_user_ids = [
            self.create_or_get_meeting_user(meeting_id, user_id)
            for user_id in additional_user_ids
        ]
        meeting_user_ids = set(
            group_in_instance.get("meeting_user_ids", set()) or set()
        )
        meeting_user_ids.update(additional_meeting_user_ids)
        group_id = group_in_instance["id"]
        for meeting_user_id in additional_meeting_user_ids:
            fqid_meeting_user = fqid_from_collection_and_id(
                "meeting_user", meeting_user_id
            )
            group_ids = self.datastore.changed_models.get(fqid_meeting_user).get(
                "group_ids", []
            )
            if group_id not in group_ids:
                group_ids.append(group_id)
                self.datastore.changed_models.get(fqid_meeting_user)[
                    "group_ids"
                ] = group_ids
            meeting_users_in_instance[
                str(meeting_user_id)
            ] = self.datastore.changed_models.get(fqid_meeting_user)
        group_in_instance["meeting_user_ids"] = list(meeting_user_ids)

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
