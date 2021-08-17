import time
from collections import defaultdict
from typing import Any, Dict, Iterable, List

from ....models.checker import Checker, CheckException
from ....models.models import Meeting
from ....shared.exceptions import ActionException
from ....shared.interfaces.event import EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .export_helper import export_meeting
from .import_ import MeetingImport


@register_action("meeting.clone")
class MeetingClone(MeetingImport):
    """
    Action to clone a meeting.
    """

    schema = DefaultSchema(Meeting()).get_default_schema(
        additional_required_fields={"meeting_id": {"type": "integer"}}
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_json = export_meeting(self.datastore, instance["meeting_id"])
        instance["meeting"] = meeting_json
        meeting_json["user"] = []
        committee_id = meeting_json["meeting"][0]["committee_id"]
        meeting_json["meeting"][0]["committee_id"] = None

        # checks if the meeting is correct
        if not len(meeting_json.get("meeting", [])) == 1:
            raise ActionException("Need exact one meeting in meeting collection.")

        # save blobs from mediafiles
        self.mediadata = []
        for entry in meeting_json.get("mediafile", []):
            if "blob" in entry:
                self.mediadata.append(
                    (entry.pop("blob"), entry["id"], entry["mimetype"])
                )

        # check datavalidation
        checker = Checker(data=meeting_json, is_import=True, is_clone=True)
        try:
            checker.run_check()
        except CheckException as ce:
            raise ActionException(str(ce))

        for entry in meeting_json.get("motion", []):
            if entry.get("all_origin_ids") or entry.get("all_derived_motion_ids"):
                raise ActionException(
                    "Motion all_origin_ids and all_derived_motion_ids should be empty."
                )

        # set imported_at
        meeting_json["meeting"][0]["imported_at"] = round(time.time())

        # update committee_id
        meeting_json["meeting"][0]["committee_id"] = committee_id

        # replace ids in the meeting_json
        self.create_replace_map(meeting_json)
        self.replace_fields(instance, ignore_user=True)
        self.upload_mediadata()
        return instance

    def create_replace_map(self, json_data: Dict[str, Any]) -> None:
        replace_map: Dict[str, Dict[int, int]] = defaultdict(dict)
        for collection in json_data:
            if collection == "user":
                for user_id in json_data["meeting"][0]["user_ids"] or []:
                    replace_map["user"][user_id] = user_id
            elif not json_data[collection]:
                continue
            else:
                new_ids = self.datastore.reserve_ids(
                    Collection(collection), len(json_data[collection])
                )
                for entry, new_id in zip(json_data[collection], new_ids):
                    replace_map[collection][entry["id"]] = new_id
        self.replace_map = replace_map

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        write_requests = list(super().create_write_requests(instance))
        self.append_extra_write_requests(write_requests, instance["meeting"])
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

        for user_id in json_data["meeting"][0]["user_ids"]:
            write_requests.append(
                self.build_write_request(
                    EventType.Update,
                    FullQualifiedId(Collection("user"), user_id),
                    f"clone meeting {json_data['meeting'][0]['id']}",
                    list_fields={
                        "add": {
                            "meeting_ids": [json_data["meeting"][0]["id"]],
                        },
                        "remove": {},
                    },
                )
            )

    def field_with_meeting(self, field: str, json_data: Dict[str, Any]) -> str:
        front, back = field.split("$")
        return f"{front}${json_data['meeting'][0]['id']}{back}"

    def append_helper_list_int(
        self,
        write_requests: List[WriteRequest],
        json_data: Dict[str, Any],
        collection: str,
        field: str,
        field_template: str,
    ) -> None:
        for model in json_data[collection]:
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
        for model in json_data[collection]:
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
        for model in json_data[collection]:
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
            f"clone meeting {json_data['meeting'][0]['id']}",
            list_fields={
                "add": {
                    field_template: [str(json_data["meeting"][0]["id"])],
                    self.field_with_meeting(field_template, json_data): [model_id],
                },
                "remove": {},
            },
        )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
