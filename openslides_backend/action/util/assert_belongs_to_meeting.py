from typing import List, Set, Union

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

    errors: Set[str] = set()
    for fqid in fqids:
        if fqid.collection.collection == "meeting":
            if fqid.id != meeting_id:
                errors.add(str(fqid))
        elif fqid.collection.collection == "user":
            instance = datastore.get(
                fqid,
                ["meeting_ids"],
                raise_exception=False,
            )
            if meeting_id not in instance.get("meeting_ids", []):
                errors.add(str(fqid))
        elif fqid.collection.collection == "mediafile":
            pass
        else:
            instance = datastore.get(
                fqid,
                ["meeting_id"],
                raise_exception=False,
            )
            if instance.get("meeting_id") != meeting_id:
                errors.add(str(fqid))

    if errors:
        raise ActionException(
            f"The following models do not belong to meeting {meeting_id}: {list(errors)}"
        )
