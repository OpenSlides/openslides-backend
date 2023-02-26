from typing import List, Set, Union

from ...services.datastore.interface import DatastoreService
from ...shared.exceptions import ActionException
from ...shared.filters import And, FilterOperator
from ...shared.patterns import (
    KEYSEPARATOR,
    FullQualifiedId,
    collection_from_fqid,
    id_from_fqid,
)


def assert_belongs_to_meeting(
    datastore: DatastoreService,
    fqids: Union[FullQualifiedId, List[FullQualifiedId]],
    meeting_id: int,
) -> None:
    if not isinstance(fqids, list):
        fqids = [fqids]

    errors: Set[str] = set()
    for fqid in fqids:
        if collection_from_fqid(fqid) == "meeting":
            if id_from_fqid(fqid) != meeting_id:
                errors.add(str(fqid))
        elif collection_from_fqid(fqid) == "user":
            instance = datastore.get(
                fqid,
                ["meeting_ids"],
                lock_result=False,
                raise_exception=False,
            )
            if meeting_id in instance.get("meeting_ids", []):
                continue
            # try on datastore whether minimum 1 group-relation exist in meeting_user
            filter_ = And(
                FilterOperator("meeting_id", "=", meeting_id),
                FilterOperator("user_id", "=", id_from_fqid(fqid)),
            )
            result = datastore.filter("meeting_user", filter_, ["group_ids"])
            if len(result) == 1 and list(result.values())[0].get("group_ids"):
                continue
            errors.add(str(fqid))
        elif collection_from_fqid(fqid) == "mediafile":
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
