from typing import List, Union

from ...services.datastore.interface import DatastoreService
from ...shared.exceptions import ActionException
from ...shared.patterns import FullQualifiedId


def assert_belongs_to_meeting(
    datastore: DatastoreService,
    fqids: Union[FullQualifiedId, List[FullQualifiedId]],
    meeting_id: int,
) -> None:
    if not isinstance(fqids, list):
        fqids = [fqids]

    errors: List[FullQualifiedId] = []
    for fqid in fqids:
        if fqid.collection.collection == "meeting":
            if fqid.id == meeting_id:
                continue
            errors.append(fqid)
        mapped_fields = ["meeting_id"]
        if fqid.collection.collection == "user":
            mapped_fields += ["guest_meeting_ids", f"group_${meeting_id}_ids"]

        instance = datastore.fetch_model(
            fqid,
            mapped_fields,
        )
        if instance.get("meeting_id") != meeting_id:
            if fqid.collection.collection == "user" and (
                meeting_id in instance.get("guest_meeting_ids", [])
                or instance.get(f"group_${meeting_id}_ids")
            ):
                continue
            errors.append(fqid)

    if errors:
        raise ActionException(
            f"The following models do not belong to meeting {meeting_id}: {errors}"
        )
