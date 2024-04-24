from typing import Any

import fastjsonschema

from ..shared.patterns import fqid_from_collection_and_id
from ..shared.schema import required_id_schema, schema_version
from .base import BasePresenter
from .presenter import register_presenter

get_forwarding_committees_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get_forwarding_committees",
        "description": "get forwarding committees",
        "properties": {
            "committee_id": required_id_schema,
        },
        "required": ["committee_id"],
    }
)


@register_presenter("get_forwarding_committees")
class GetForwardingCommittees(BasePresenter):
    """
    Get forwarded committees.
    """

    schema = get_forwarding_committees_schema

    def get_result(self) -> Any:
        committee = self.datastore.get(
            fqid_from_collection_and_id("committee", self.data["committee_id"]),
            ["receive_forwardings_from_committee_ids"],
        )

        if not committee.get("receive_forwardings_from_committee_ids"):
            return []

        result = []
        for committee_id in committee["receive_forwardings_from_committee_ids"]:
            committee_data = self.datastore.get(
                fqid_from_collection_and_id("committee", committee_id), ["name"]
            )
            if committee_data.get("name"):
                result.append(committee_data["name"])
        return result
