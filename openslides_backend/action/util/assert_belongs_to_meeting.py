from typing import List, Union

from ...services.datastore.deleted_models_behaviour import InstanceAdditionalBehaviour
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

    errors: List[str] = []
    for fqid in fqids:
        if fqid.collection.collection == "meeting":
            if fqid.id != meeting_id:
                errors.append(str(fqid))
            continue
        mapped_fields = ["meeting_id"]
        if fqid.collection.collection == "user":
            mapped_fields += ["guest_meeting_ids", f"group_${meeting_id}_ids"]

        instance = datastore.fetch_model(
            fqid,
            mapped_fields,
            db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
            exception=False,
        )
        if instance.get("meeting_id") != meeting_id:
            if fqid.collection.collection == "user" and (
                meeting_id in instance.get("guest_meeting_ids", [])
                or instance.get(f"group_${meeting_id}_ids")
            ):
                continue
            errors.append(str(fqid))

    if errors:
        raise ActionException(
            f"The following models do not belong to meeting {meeting_id}: {errors}"
        )
