from typing import List, Set, Union

from ...services.datastore.interface import DatastoreService
from ...shared.exceptions import ActionException
from ...shared.patterns import KEYSEPARATOR, FullQualifiedId, fqid_collection, fqid_id


def assert_belongs_to_meeting(
    datastore: DatastoreService,
    fqids: Union[FullQualifiedId, List[FullQualifiedId]],
    meeting_id: int,
) -> None:
    if not isinstance(fqids, list):
        fqids = [fqids]

    errors: Set[str] = set()
    for fqid in fqids:
        if fqid_collection(fqid) == "meeting":
            if fqid_id(fqid) != meeting_id:
                errors.add(str(fqid))
        elif fqid_collection(fqid) == "user":
            instance = datastore.get(
                fqid,
                ["meeting_ids"],
                lock_result=False,
                raise_exception=False,
            )
            if meeting_id not in instance.get("meeting_ids", []):
                errors.add(str(fqid))
        elif fqid_collection(fqid) == "mediafile":
            mediafile = datastore.get(fqid, ["owner_id"], lock_result=False)
            collection, id_ = mediafile["owner_id"].split(KEYSEPARATOR)
            if collection == "meeting":
                if int(id_) != meeting_id:
                    errors.add(str(fqid))
            else:
                errors.add(str(fqid))
        else:
            instance = datastore.get(
                fqid,
                ["meeting_id"],
                lock_result=False,
                raise_exception=False,
            )
            if instance.get("meeting_id") != meeting_id:
                errors.add(str(fqid))

    if errors:
        raise ActionException(
            f"The following models do not belong to meeting {meeting_id}: {list(errors)}"
        )
