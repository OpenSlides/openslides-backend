import time
from collections import defaultdict
from typing import Any, Dict, Iterable, List

from ....models.checker import Checker, CheckException
from ....models.models import Meeting
from ....permissions.management_levels import CommitteeManagementLevel
from ....permissions.permission_helper import has_committee_management_level
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.interfaces.event import EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .export_helper import export_meeting
from .import_ import MeetingImport

updatable_fields = [
    "committee_id",
    "welcome_title",
    "description",
    "start_time",
    "end_time",
    "location",
    "organization_tag_ids",
]


@register_action("meeting.clone")
class MeetingClone(MeetingImport):
    """
    Action to clone a meeting.
    """

    schema = DefaultSchema(Meeting()).get_default_schema(
        optional_properties=updatable_fields,
        additional_required_fields={"meeting_id": {"type": "integer"}},
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_json_old = export_meeting(
            self.datastore, self.media, instance["meeting_id"]
        )

        # Transform data format
        # TODO: Transform format earlier, e. g. in export_meeting function
        meeting_json: Dict[str, Any] = {}
        for collection, objs in meeting_json_old.items():
            meeting_json[collection] = {}
            for obj in objs:
                meeting_json[collection][str(obj["id"])] = obj

        instance["meeting"] = meeting_json

        # checks if the meeting is correct
        if not len(meeting_json.get("meeting", {}).keys()) == 1:
            raise ActionException("Need exact one meeting in meeting collection.")

        if (
            committee_id := instance.get("committee_id")
        ) and committee_id != self.get_meeting_from_json(meeting_json)["committee_id"]:
            self.get_meeting_from_json(meeting_json)["committee_id"] = committee_id

        # pre update the meeting
        for field in updatable_fields:
            if field in instance:
                value = instance.pop(field)
                self.get_meeting_from_json(meeting_json)[field] = value

        # reset mediafile/attachment_ids to [] if None.
        for mediafile_id in instance["meeting"].get("mediafile", []):
            if (
                instance["meeting"]["mediafile"][mediafile_id].get("attachment_ids")
                is None
            ):
                instance["meeting"]["mediafile"][mediafile_id]["attachment_ids"] = []

        # check datavalidation
        checker = Checker(data=meeting_json, mode="internal")
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

        # set active
        self.get_meeting_from_json(meeting_json)["is_active_in_organization_id"] = 1

        # check limit of meetings
        self.check_limit_of_meetings(
            self.get_meeting_from_json(meeting_json)["committee_id"],
            text="clone",
            text2="",
        )

        # set imported_at
        self.get_meeting_from_json(meeting_json)["imported_at"] = round(time.time())

        # replace ids in the meeting_json
        self.create_replace_map(meeting_json)
        self.duplicate_mediafiles(meeting_json)
        self.replace_fields(instance)

        self.add_meeting_title_suffix(instance)
        return instance

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

    def duplicate_mediafiles(self, json_data: Dict[str, Any]) -> None:
        for mediafile_id in json_data["mediafile"]:
            mediafile = json_data["mediafile"][mediafile_id]
            if not mediafile.get("is_directory"):
                self.media.duplicate_mediafile(
                    mediafile["id"], self.replace_map["mediafile"][mediafile["id"]]
                )

    def add_meeting_title_suffix(self, instance: Dict[str, Any]) -> None:
        meeting = self.get_meeting_from_json(instance["meeting"])
        meeting["name"] = meeting.get("name", "") + " - Copy"

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        write_requests = list(super().create_write_requests(instance))
        self.append_extra_write_requests(write_requests, instance["meeting"])
        write_requests.extend(list(self.handle_calculated_fields(instance)))
        return write_requests

    def append_extra_write_requests(
        self, write_requests: List[WriteRequest], json_data: Dict[str, Any]
    ) -> None:

        updated_field_n_n = (
            (
                "group",
                "user_ids",
                "group_$_ids",
            ),
            (
                "motion",
                "supporter_ids",
                "supported_motion_$_ids",
            ),
            (
                "poll",
                "voted_ids",
                "poll_voted_$_ids",
            ),
        )
        for tuple_ in updated_field_n_n:
            self.append_helper_list_list(write_requests, json_data, *tuple_)

        updated_field_n_1 = (
            (
                "speaker",
                "user_id",
                "speaker_$_ids",
            ),
            (
                "personal_note",
                "user_id",
                "personal_note_$_ids",
            ),
            (
                "motion_submitter",
                "user_id",
                "submitted_motion_$_ids",
            ),
            (
                "vote",
                "user_id",
                "vote_$_ids",
            ),
            (
                "vote",
                "delegated_user_id",
                "vote_delegated_vote_$_ids",
            ),
            (
                "assignment_candidate",
                "user_id",
                "assignment_candidate_$_ids",
            ),
        )
        for tuple_ in updated_field_n_1:
            self.append_helper_list_int(write_requests, json_data, *tuple_)

        updated_field_n_co = (
            (
                "option",
                "content_object_id",
                "option_$_ids",
            ),
            (
                "projection",
                "content_object_id",
                "projection_$_ids",
            ),
        )
        for tuple_ in updated_field_n_co:
            self.append_helper_list_cobj(write_requests, json_data, *tuple_)

    def field_with_meeting(self, field: str, json_data: Dict[str, Any]) -> str:
        front, back = field.split("$")
        return f"{front}${self.get_meeting_from_json(json_data)['id']}{back}"

    def append_helper_list_int(
        self,
        write_requests: List[WriteRequest],
        json_data: Dict[str, Any],
        collection: str,
        field: str,
        field_template: str,
    ) -> None:
        for model in json_data[collection].values():
            if model.get(field):
                write_requests.append(
                    self.build_write_request_helper(
                        model[field], json_data, field_template, model["id"]
                    )
                )

    def append_helper_list_list(
        self,
        write_requests: List[WriteRequest],
        json_data: Dict[str, Any],
        collection: str,
        field: str,
        field_template: str,
    ) -> None:
        for model in json_data[collection].values():
            if model.get(field):
                for user_id in model.get(field):
                    write_requests.append(
                        self.build_write_request_helper(
                            user_id, json_data, field_template, model["id"]
                        )
                    )

    def append_helper_list_cobj(
        self,
        write_requests: List[WriteRequest],
        json_data: Dict[str, Any],
        collection: str,
        field: str,
        field_template: str,
    ) -> None:
        for model in json_data[collection].values():
            if model.get(field):
                fqid = model[field]
                cobj_collection, cobj_id = fqid.split(KEYSEPARATOR)
                if cobj_collection == "user":
                    write_requests.append(
                        self.build_write_request_helper(
                            cobj_id, json_data, field_template, model["id"]
                        )
                    )

    def build_write_request_helper(
        self,
        user_id: int,
        json_data: Dict[str, Any],
        field_template: str,
        model_id: int,
    ) -> WriteRequest:
        return self.build_write_request(
            EventType.Update,
            FullQualifiedId(Collection("user"), user_id),
            f"clone meeting {self.get_meeting_from_json(json_data)['id']}",
            list_fields={
                "add": {
                    field_template: [str(self.get_meeting_from_json(json_data)["id"])],
                    self.field_with_meeting(field_template, json_data): [model_id],
                },
                "remove": {},
            },
        )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        meeting = self.datastore.fetch_model(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            ["committee_id"],
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
        if (
            payload_committee_id := instance.get("committee_id")
        ) and payload_committee_id != committee_id:
            if not has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                payload_committee_id,
            ):
                raise PermissionDenied(
                    f"Missing {CommitteeManagementLevel.CAN_MANAGE.get_verbose_type()}: {CommitteeManagementLevel.CAN_MANAGE} for committee {payload_committee_id}"
                )
