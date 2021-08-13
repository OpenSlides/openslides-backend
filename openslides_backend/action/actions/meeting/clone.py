import time
from collections import defaultdict
from typing import Any, Dict

from ....models.checker import Checker, CheckException
from ....models.models import Meeting
from ....presenter.export_meeting import export_meeting
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
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
        checker = Checker(data=meeting_json, is_import=True)
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
            if not json_data[collection]:
                continue
            if collection == "user":
                for user_id in json_data["meeting"]["user_ids"]:
                    replace_map["user"][user_id] = user_id
            else:
                new_ids = self.datastore.reserve_ids(
                    Collection(collection), len(json_data[collection])
                )
                for entry, new_id in zip(json_data[collection], new_ids):
                    replace_map[collection][entry["id"]] = new_id
        self.replace_map = replace_map

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
