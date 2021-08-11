from typing import Any, Dict, List

import fastjsonschema

from ..models.base import model_registry
from ..shared.filters import FilterOperator
from ..shared.patterns import Collection
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

export_meeting_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "export_meeting",
        "description": "export the meeting with meeting_id",
        "properties": {
            "meeting_id": {"type": "integer"},
            "internal": {"type": "boolean"},
        },
        "required": ["meeting_id"],
        "additionalProperties": False,
    }
)


@register_presenter("export_meeting")
class ExportMeeting(BasePresenter):
    """
    Export a meeting
    """

    schema = export_meeting_schema

    def get_result(self) -> Any:
        self.check_permissions()
        export = {}
        meeting_collections = self.get_meeting_collections()
        for collection in meeting_collections:
            res = self.datastore.filter(
                Collection(collection),
                FilterOperator("meeting_id", "=", self.data["meeting_id"]),
            )
            res_list = self.remove_meta_fields(list(res.values()))
            export[collection] = res_list
        return {"export": export}

    def check_permissions(self) -> None:
        pass

    def get_meeting_collections(self) -> List[str]:
        not_meeting_collections = [
            "organization",
            "organization_tag",
            "meeting",
            "user",
            "resource",
            "committee",
        ]
        meeting_collections = [
            c.collection
            for c in model_registry
            if c.collection not in not_meeting_collections
        ]
        return meeting_collections

    def remove_meta_fields(self, res: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        list_without_meta_fields = []
        for entry in res:
            if "meta_position" in entry:
                del entry["meta_position"]
            if "meta_deleted" in entry:
                del entry["meta_deleted"]
            list_without_meta_fields.append(entry)
        return list_without_meta_fields
